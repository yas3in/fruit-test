"""
Core bot actions and automation routines using fruitbot library.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional

import urllib3
try:
    from urllib3.contrib.socks import SOCKSProxyManager
except ImportError:
    SOCKSProxyManager = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import fruitbot
from fruitbot import Client
from fruitbot.exceptions import FruitCraftException, CaptchaRequired, AccountBlocked

logger = logging.getLogger("FruitBot")


def get_configured_client(
    restore_key: Optional[str] = None,
    proxy_url: Optional[str] = None,
    base_url: Optional[str] = None,
    no_proxy: bool = False,
    timeout: int = 15
) -> Client:
    """Initialize fruitbot.Client and configure proxy (port 10501) if enabled."""
    key = restore_key or os.getenv("FRUITCRAFT_RESTORE_KEY", "head9229burst65")
    b_url = base_url or os.getenv("FRUITCRAFT_BASE_URL", "http://iran.fruitcraft.ir")

    if no_proxy:
        p_url = None
    elif proxy_url is not None:
        p_url = proxy_url
    else:
        # Default to port 10501 proxy as requested by user
        env_proxy = os.getenv("FRUITCRAFT_PROXY") or os.getenv("PROXY_URL")
        p_url = env_proxy or f"http://127.0.0.1:{os.getenv('PROXY_PORT', '10501')}"

    print(f"🍉 Initializing FruitBot client...")
    print(f"   Base URL : {b_url}")
    if p_url:
        print(f"   Proxy    : {p_url} (Port 10501)")
    else:
        print("   Proxy    : Direct connection (No proxy)")

    bot = Client(
        session_name="fruit_session",
        restore_key=key,
        base_url=b_url,
        time_out=timeout
    )

    if p_url:
        try:
            network_instance = bot.sendRequest.__self__
            headers = network_instance.headers

            if p_url.startswith("socks5://") or p_url.startswith("socks5h://"):
                if SOCKSProxyManager is not None:
                    network_instance.http = SOCKSProxyManager(
                        p_url,
                        timeout=timeout,
                        headers=headers
                    )
                    print(f"   ✅ SOCKS5 proxy attached successfully.")
                else:
                    print("⚠️ PySocks not installed. Run: pip install PySocks")
            elif p_url.startswith("http://") or p_url.startswith("https://"):
                network_instance.http = urllib3.ProxyManager(
                    p_url,
                    timeout=timeout,
                    headers=headers
                )
                print(f"   ✅ HTTP proxy attached successfully.")
        except Exception as e:
            print(f"⚠️  Could not attach proxy manager: {e}")

    return bot


def parse_cards_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract card items from player data."""
    cards_raw = data.get("cards", [])
    if isinstance(cards_raw, dict):
        return list(cards_raw.values())
    elif isinstance(cards_raw, list):
        return cards_raw
    return []


def get_weakest_available_card(cards_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Finds the weakest and lowest-level card that is currently available.
    Rules:
    1. Select ONLY ONE card.
    2. Choose the weakest (lowest power/attack) and lowest level card.
    3. Verify that the card is available (not in cooldown and usable).
    """
    valid_cards = []
    for c in cards_list:
        if not isinstance(c, dict):
            continue
        cid = c.get("id", c.get("card_id"))
        if not cid:
            continue

        # Check availability
        in_cooldown = bool(c.get("in_cooldown", False))
        if in_cooldown:
            continue

        level = int(c.get("level", 1))
        power = int(c.get("power", c.get("attack", 0)))
        defense = int(c.get("defense", 0))

        valid_cards.append({
            "id": int(cid),
            "name": c.get("name", f"Card #{cid}"),
            "level": level,
            "power": power,
            "defense": defense,
            "raw": c
        })

    if not valid_cards:
        return None

    # Sort primarily by level ascending, then by power ascending, then by defense
    valid_cards.sort(key=lambda x: (x["level"], x["power"], x["defense"], x["id"]))

    # Return the single weakest available card
    return valid_cards[0]


def get_top_attack_cards(cards_list: List[Dict[str, Any]], count: int = 4) -> List[int]:
    """Find top available cards for battles."""
    usable = []
    for c in cards_list:
        if not isinstance(c, dict):
            continue
        cid = c.get("id", c.get("card_id"))
        if not cid or bool(c.get("in_cooldown", False)):
            continue
        power = int(c.get("power", c.get("attack", 0)))
        usable.append({"id": int(cid), "power": power})

    usable.sort(key=lambda x: x["power"], reverse=True)
    return [c["id"] for c in usable[:count]]


def action_account_info(bot: Client):
    """Fetch and display player account information."""
    print("\n" + "=" * 55)
    print("👤 LOADING ACCOUNT INFORMATION...")
    print("=" * 55)

    try:
        player_data = bot.loadPlayer(save_session=True)
    except CaptchaRequired:
        print("🚨 CAPTCHA REQUIRED! Please solve CAPTCHA on your device.")
        return
    except Exception as e:
        print(f"❌ Error loading account: {e}")
        return

    name = player_data.get("name", "Unknown")
    pid = player_data.get("id", "Unknown")
    level = player_data.get("level", 1)
    xp = player_data.get("xp", 0)
    gold = player_data.get("gold", 0)
    nectar = player_data.get("nectar", 0)
    potion = player_data.get("potion", 0)
    tribe = player_data.get("tribe") or {}
    tribe_name = tribe.get("name", "None")
    atk = player_data.get("attack", player_data.get("attack_power", 0))
    df = player_data.get("defense", player_data.get("defense_power", 0))

    cards = parse_cards_list(player_data)
    available_cards = [c for c in cards if isinstance(c, dict) and not c.get("in_cooldown")]

    print(f"  Player Name   : {name} (ID: {pid})")
    print(f"  Level         : {level} (XP: {xp:,})")
    print(f"  Gold 🪙       : {gold:,}")
    print(f"  Nectar / Potion: 🍯 {nectar:,} / 🧪 {potion}")
    print(f"  Tribe 🛡️      : {tribe_name}")
    print(f"  Attack / Def  : ⚔️ {atk:,} / 🛡️ {df:,}")
    print(f"  Total Cards   : {len(cards)} (Available: {len(available_cards)})")
    print("=" * 55 + "\n")


def action_auto_quest(bot: Client, count: int = 0):
    """
    Execute quest automation loop:
    1. Selects ONLY 1 card.
    2. Uses the weakest and lowest-level available card.
    3. Checks card availability before quest.
    4. Sleeps 2 seconds after each quest, then runs the next quest.
    """
    print("\n" + "=" * 65)
    print("📜 STARTING AUTO QUEST AUTOMATION")
    print("   Rule 1: Exactly 1 card selected")
    print("   Rule 2: Weakest & lowest-level available card")
    print("   Rule 3: 2-second sleep between quests")
    print(f"   Target : {'Infinite Loop (Ctrl+C to stop)' if count <= 0 else f'{count} Quests'}")
    print("=" * 65)

    completed = 0
    total_gold = 0
    total_xp = 0

    while True:
        if count > 0 and completed >= count:
            print(f"\n✅ Target reached: Completed {completed} quests.")
            break

        try:
            player_data = bot.loadPlayer()
            cards_list = parse_cards_list(player_data)

            weakest_card = get_weakest_available_card(cards_list)
            if not weakest_card:
                print("⚠️  No cards currently available (all cards might be in cooldown). Waiting 10s...")
                time.sleep(10)
                continue

            card_id = weakest_card["id"]
            card_name = weakest_card["name"]
            card_lvl = weakest_card["level"]
            card_pwr = weakest_card["power"]

            print(f"👉 [Quest #{completed + 1}] Card: '{card_name}' (ID: {card_id}, Lv.{card_lvl}, Power:{card_pwr})...", end=" ", flush=True)

            res = bot.doQuest(card_ids=[card_id])

            gold_earned = int(res.get("gold", res.get("gold_earned", 0)))
            xp_earned = int(res.get("xp", res.get("xp_earned", 0)))
            total_gold += gold_earned
            total_xp += xp_earned
            completed += 1

            print(f"✅ SUCCESS! (+{gold_earned:,} Gold 🪙, +{xp_earned:,} XP ⭐) [Total Gold: +{total_gold:,}]")

        except CaptchaRequired:
            print("\n🚨 CAPTCHA REQUIRED! Automation stopped to prevent penalties.")
            break
        except KeyboardInterrupt:
            print("\n🛑 Auto Quest stopped by user.")
            break
        except Exception as e:
            print(f"\n⚠️  Quest error: {e}. Retrying in 5s...")
            time.sleep(5)
            continue

        print("   ⏳ Sleeping 2 seconds before next quest...")
        time.sleep(2)

    print("\n" + "=" * 65)
    print(f"📊 QUEST SESSION SUMMARY:")
    print(f"   Completed Quests : {completed}")
    print(f"   Total Gold Earned: +{total_gold:,} 🪙")
    print(f"   Total XP Earned  : +{total_xp:,} ⭐")
    print("=" * 65 + "\n")


def action_auto_battle(bot: Client, count: int = 10):
    """Execute automated battles."""
    print("\n" + "=" * 60)
    print("⚔️ STARTING AUTO BATTLE")
    print(f"   Target battles: {count}")
    print("=" * 60)

    wins = 0
    losses = 0
    total_gold = 0
    total_xp = 0

    for i in range(1, count + 1):
        try:
            player_data = bot.loadPlayer()
            user_id = player_data.get("id")
            cards_list = parse_cards_list(player_data)

            battle_cards = get_top_attack_cards(cards_list, count=4)
            if not battle_cards:
                print("⚠️  No usable cards for battle. Waiting 15s...")
                time.sleep(15)
                continue

            opponents = bot.getOpponents()
            if not opponents:
                print("⚠️  No opponents found. Waiting 5s...")
                time.sleep(5)
                continue

            target = opponents[0]
            target_id = int(target.get("id", target.get("player_id")))
            target_name = target.get("name", f"Player #{target_id}")
            target_def = target.get("defense", target.get("power", 0))

            print(f"⚔️ [Battle #{i}/{count}] Attacking '{target_name}' (Def: {target_def:,}) with {len(battle_cards)} cards...", end=" ", flush=True)

            res = bot.attackOpponent(opponent_id=target_id, card_ids=battle_cards)

            battle_info = res.get("battle", res)
            winner_id = battle_info.get("winner_id", res.get("winner"))
            is_win = (winner_id == user_id) or (res.get("status") is True)

            gold = int(battle_info.get("gold", res.get("gold_earned", 0)))
            xp = int(battle_info.get("xp", res.get("xp_earned", 0)))

            if is_win:
                wins += 1
                total_gold += gold
                total_xp += xp
                print(f"🏆 WON! (+{gold:,} Gold, +{xp:,} XP)")
            else:
                losses += 1
                print(f"💀 LOST vs {target_name}")

            time.sleep(3)

        except CaptchaRequired:
            print("\n🚨 CAPTCHA REQUIRED! Stopped.")
            break
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break
        except Exception as e:
            print(f"\n⚠️  Battle error: {e}")
            time.sleep(5)

    print("\n" + "=" * 60)
    print(f"📊 BATTLE SESSION SUMMARY:")
    print(f"   Wins: {wins} | Losses: {losses} | Gold: +{total_gold:,} | XP: +{total_xp:,}")
    print("=" * 60 + "\n")


def action_collect_mine(bot: Client):
    """Collect gold from mine."""
    print("\n⛏️ Collecting mined gold...")
    try:
        res = bot.collectMinedGold()
        gold = res.get("gold", res.get("gold_collected", 0))
        print(f"✅ Successfully collected {gold:,} gold from mine!")
    except Exception as e:
        print(f"⚠️  Mine collection error: {e}")


def interactive_menu(bot: Client):
    """Interactive console menu."""
    while True:
        print("\n" + "=" * 45)
        print("🍉 FruitCraft Bot Menu")
        print("=" * 45)
        print("1. 👤 Account Information (اطلاعات اکانت)")
        print("2. 📜 Auto Quest (ماموریت با ضعیف‌ترین کارت و ۲ ثانیه اسلیپ)")
        print("3. ⚔️ Auto Battle (بتل زدن)")
        print("4. ⛏️ Collect Mined Gold (جمع‌آوری طلا از معدن)")
        print("0. ❌ Exit (خروج)")
        print("=" * 45)

        try:
            choice = input("Enter choice [0-4]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if choice == "1":
            action_account_info(bot)
        elif choice == "2":
            cnt_str = input("How many quests? (0 for continuous loop): ").strip()
            cnt = int(cnt_str) if cnt_str.isdigit() else 0
            action_auto_quest(bot, count=cnt)
        elif choice == "3":
            cnt_str = input("How many battles? (default 10): ").strip()
            cnt = int(cnt_str) if cnt_str.isdigit() else 10
            action_auto_battle(bot, count=cnt)
        elif choice == "4":
            action_collect_mine(bot)
        elif choice == "0":
            print("Exiting. Good luck!")
            break
        else:
            print("Invalid choice, please select 0-4.")
