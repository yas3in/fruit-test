"""
Core bot actions and automation routines using fruitbot library.
Supports:
- Auto quest with 1 weakest card, 10-card fallback rotation, and 2s delay.
- Auto battle with top attack cards.
- Mine collection.
- Persistent session management (fixing Error 124 / PlayingOnAnotherDevice).
- Proxy support on port 10501.
"""

import os
import sys
import time
import shutil
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
from fruitbot.exceptions import (
    FruitCraftException,
    CaptchaRequired,
    AccountBlocked,
    PlayingOnAnotherDevice,
    OnlineOnAnotherDevice,
    CardCoolingDown,
    CardInUse,
    TooManyRequests
)

logger = logging.getLogger("FruitBot")


def ensure_session_files():
    """Ensure fruit.fb and fruit_session.fb exist and stay in sync."""
    source = None
    if os.path.exists("fruit.fb"):
        source = "fruit.fb"
    elif os.path.exists("fruit_session.fb"):
        source = "fruit_session.fb"
    elif os.path.exists("myfriutlib/fruit.fb"):
        source = "myfriutlib/fruit.fb"

    if source:
        for target in ("fruit.fb", "fruit_session.fb"):
            if not os.path.exists(target) or os.path.getsize(target) == 0:
                try:
                    shutil.copy(source, target)
                except Exception:
                    pass


def get_configured_client(
    session_name: str = "fruit",
    restore_key: Optional[str] = None,
    proxy_url: Optional[str] = None,
    base_url: Optional[str] = None,
    no_proxy: bool = False,
    timeout: int = 15
) -> Client:
    """
    Initialize fruitbot.Client with persistent session and optional proxy on port 10501.
    Reuses fruit.fb (fixed passport, udid, mobile_model) to prevent session conflicts (Error 124).
    """
    ensure_session_files()

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

    print(f"🍉 تنظیم کلاینت FruitCraft (FruitBot v1.6.1)...")
    print(f"   نام سشن  : {session_name} (فایل: {session_name}.fb)")
    print(f"   آدرس سرور : {b_url}")
    if p_url:
        print(f"   پروکسی    : {p_url} (پورت 10501)")
    else:
        print("   پروکسی    : اتصال مستقیم (No proxy)")

    bot = Client(
        session_name=session_name,
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
                    print(f"   ✅ پروکسی SOCKS5 متصل شد.")
                else:
                    print("⚠️ کتابخانه PySocks نصب نیست. اجرای بدون SOCKS.")
            elif p_url.startswith("http://") or p_url.startswith("https://"):
                network_instance.http = urllib3.ProxyManager(
                    p_url,
                    timeout=timeout,
                    headers=headers
                )
                print(f"   ✅ پروکسی HTTP متصل شد.")
        except Exception as e:
            print(f"⚠️ امکان اتصال پراکسی وجود نداشت: {e}")

    return bot


def safe_load_player(bot: Client, max_retries: int = 5, retry_delay: int = 25) -> Dict[str, Any]:
    """
    Safely load player info with automatic handling and retries for Error 124 (PlayingOnAnotherDevice).
    """
    for attempt in range(1, max_retries + 1):
        try:
            data = bot.loadPlayer(save_session=True)
            return data
        except (PlayingOnAnotherDevice, OnlineOnAnotherDevice) as e:
            print("\n" + "!" * 70)
            print("🚨 خطای ۱۲۴: دستگاه دیگری در حال بازی است (یا بازی روی گوشی باز است)!")
            print("💡 راهکار:")
            print("   ۱. بازی فروت کرافت را روی گوشی خود کامل ببندید (Swipe Away / Force Stop).")
            print("   ۲. سرور بازی بعد از قطع ارتباط تا ۶۰ ثانیه سشن را نگه می‌دارد.")
            if attempt < max_retries:
                print(f"   ⏳ تلاش {attempt}/{max_retries} - منتظر انقضای سشن سرور می‌مانیم ({retry_delay} ثانیه)...")
                print("!" * 70 + "\n")
                for sec in range(retry_delay, 0, -5):
                    print(f"      ... {sec} ثانیه تا تلاش مجدد ...")
                    time.sleep(5)
            else:
                print("❌ تعداد تلاش‌ها به پایان رسید. لطفاً بازی را روی گوشی ببندید و دوباره اسکریپت را اجرا کنید.")
                print("!" * 70 + "\n")
                raise e
        except CaptchaRequired as e:
            print("\n🚨 کپچا لازم است! لطفاً کپچا را در بازی برطرف کنید.")
            raise e
        except Exception as e:
            err_str = str(e).lower()
            if "124" in err_str or "another device" in err_str or "دیگری" in err_str:
                print(f"\n🚨 تداخل سشن سرور: {e}")
                if attempt < max_retries:
                    print(f"⏳ {retry_delay} ثانیه صبر برای آزاد شدن سشن...")
                    time.sleep(retry_delay)
                    continue
            raise e

    raise RuntimeError("Failed to load player data after multiple retries.")


def parse_cards_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract card dictionaries from player data."""
    cards_raw = data.get("cards", [])
    if isinstance(cards_raw, dict):
        cards_list = list(cards_raw.values())
    elif isinstance(cards_raw, list):
        cards_list = cards_raw
    else:
        cards_list = []

    clean_cards = []
    for c in cards_list:
        if isinstance(c, dict):
            cid = c.get("id", c.get("card_id"))
            if cid is not None:
                clean_cards.append(c)
    return clean_cards


def get_sorted_weakest_cards(cards_list: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Parses and sorts cards by:
      1. level (ascending - lowest level first)
      2. power / attack (ascending - weakest power first)
      3. defense (ascending)
      4. id (ascending)
    Returns the top `limit` (default 10) weakest cards.
    """
    parsed = []
    for c in cards_list:
        if not isinstance(c, dict):
            continue
        cid = c.get("id", c.get("card_id"))
        if cid is None:
            continue
        level = int(c.get("level", 1))
        power = int(c.get("power", c.get("attack", 0)))
        defense = int(c.get("defense", 0))
        name = c.get("name", f"کارت #{cid}")

        parsed.append({
            "id": int(cid),
            "name": name,
            "level": level,
            "power": power,
            "defense": defense,
            "raw": c
        })

    # Sort primarily by lowest level, then lowest power (weakest), then defense
    parsed.sort(key=lambda x: (x["level"], x["power"], x["defense"], x["id"]))
    return parsed[:limit]


def is_card_ready(card_entry: Dict[str, Any], cooldown_cache: Optional[Dict[int, float]] = None) -> bool:
    """
    Checks if a card is currently available (not in cooldown and usable).
    """
    cid = card_entry["id"]
    now = time.time()

    # 1. Local cooldown cache
    if cooldown_cache and cid in cooldown_cache:
        if cooldown_cache[cid] > now:
            return False
        else:
            del cooldown_cache[cid]

    # 2. Raw card status from server
    raw = card_entry.get("raw", {})
    cd = raw.get("in_cooldown") or raw.get("cooling_down")
    if cd:
        if isinstance(cd, bool) and cd is True:
            return False
        elif isinstance(cd, (int, float)):
            if cd > now or (0 < cd < 1000000):
                return False
        elif isinstance(cd, str) and cd.isdigit():
            val = int(cd)
            if val > now or (0 < val < 1000000):
                return False

    return True


def get_weakest_available_card(cards_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Helper to return the single weakest available card."""
    candidates = get_sorted_weakest_cards(cards_list, limit=10)
    for c in candidates:
        if is_card_ready(c):
            return c
    return candidates[0] if candidates else None


def get_top_attack_cards(cards_list: List[Dict[str, Any]], count: int = 4) -> List[int]:
    """Find top available cards with highest power for battles."""
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
    """Fetch and display player account information and top 10 weakest cards."""
    print("\n" + "=" * 65)
    print("👤 در حال دریافت اطلاعات اکانت...")
    print("=" * 65)

    try:
        player_data = safe_load_player(bot)
    except Exception as e:
        print(f"❌ خطا در دریافت اطلاعات: {e}")
        return

    name = player_data.get("name", "نامشخص")
    pid = player_data.get("id", "نامشخص")
    level = player_data.get("level", 1)
    xp = player_data.get("xp", 0)
    gold = player_data.get("gold", 0)
    nectar = player_data.get("nectar", 0)
    potion = player_data.get("potion", 0)
    tribe = player_data.get("tribe") or {}
    tribe_name = tribe.get("name", "ندارد")
    atk = player_data.get("attack", player_data.get("attack_power", 0))
    df = player_data.get("defense", player_data.get("defense_power", 0))

    cards = parse_cards_list(player_data)
    weakest_10 = get_sorted_weakest_cards(cards, limit=10)

    print(f"  نام بازیکن   : {name} (شناسه: {pid})")
    print(f"  سطح (Level)  : {level} (تجربه: {xp:,})")
    print(f"  سکه طلا 🪙   : {gold:,}")
    print(f"  شهد و معجون  : 🍯 {nectar:,} شهد  |  🧪 {potion} معجون")
    print(f"  قبیله 🛡️     : {tribe_name}")
    print(f"  قدرت حمله/دفاع: ⚔️ {atk:,} / 🛡️ {df:,}")
    print(f"  تعداد کل کارت‌ها: {len(cards)}")
    print("-" * 65)
    print("📋 فهرست ۱۰ کارت ضعیف اکانت (اولویت ماموریت):")
    for i, c in enumerate(weakest_10, 1):
        status = "آماده ✅" if is_card_ready(c) else "در کول‌داون ⏳"
        print(f"   {i:2d}. {c['name']:<18} | لول: {c['level']} | قدرت: {c['power']:<4} | وضعیت: {status} (ID: {c['id']})")
    print("=" * 65 + "\n")


def action_auto_quest(bot: Client, count: int = 0):
    """
    Quest Automation Loop:
    1. Selects exactly ONE card per quest.
    2. Uses the weakest and lowest-level available card.
    3. Checks cards in order from weakest (1) to 10th weakest:
       - Weakest card is checked. If available, use it for quest.
       - If in cooldown, move to next weakest card (up to 10 cards).
       - If all 10 cards are in cooldown, pause 5s and restart check from weakest.
    4. Sleeps 2 seconds after each quest, then runs the next quest.
    """
    print("\n" + "=" * 65)
    print("📜 شروع اجرای خودکار ماموریت‌ها (Auto Quest)")
    print("   قانون ۱: انتخاب دقیقاً ۱ کارت برای هر ماموریت")
    print("   قانون ۲: اولویت با ضعیف‌ترین و پایین‌ترین لول کارت")
    print("   قانون ۳: بررسی ترتیبی تا ۱۰ کارت در صورت در دسترس نبودن")
    print("   قانون ۴: شروع مجدد از کارت ۱ در صورت پر بودن کول‌داون هر ۱۰ کارت")
    print("   قانون ۵: ۲ ثانیه اسلیپ بعد از هر ماموریت")
    print(f"   تعداد هدف: {'نامحدود (حلقه بی‌نهایت - با Ctrl+C متوقف می‌شود)' if count <= 0 else f'{count} ماموریت'}")
    print("=" * 65 + "\n")

    completed = 0
    total_gold = 0
    total_xp = 0
    cooldown_cache: Dict[int, float] = {}

    while True:
        if count > 0 and completed >= count:
            print(f"\n🎉 تعداد ماموریت‌های مشخص‌شده ({completed}) به اتمام رسید.")
            break

        try:
            # 1. Fetch player & card state
            player_data = safe_load_player(bot)
            cards_list = parse_cards_list(player_data)

            # 2. Get top 10 weakest cards
            candidates = get_sorted_weakest_cards(cards_list, limit=10)
            if not candidates:
                print("⚠️ کارتی در اکانت یافت نشد! ۱۰ ثانیه توقف...")
                time.sleep(10)
                continue

            quest_done_in_this_cycle = False

            # 3. Check candidates sequentially from weakest (1) to 10th weakest
            for idx, candidate in enumerate(candidates, 1):
                cid = candidate["id"]
                cname = candidate["name"]
                clevel = candidate["level"]
                cpower = candidate["power"]

                if not is_card_ready(candidate, cooldown_cache):
                    print(f"   ⏳ کارت ضعیف #{idx}: {cname} (ID: {cid}, لول {clevel}, قدرت {cpower}) در کول‌داون است. رفتن به کارت بعدی...")
                    continue

                # Found ready card! Execute quest with this 1 card
                print(f"👉 [ماموریت #{completed + 1}] کارت ضعیف #{idx}: '{cname}' (ID: {cid}, لول {clevel}, قدرت {cpower})...", end=" ", flush=True)

                try:
                    res = bot.doQuest(card_ids=[cid])
                except (CardCoolingDown, CardInUse) as cd_err:
                    print(f"\n⚠️ سرور پاسخ داد کارت #{cid} در کول‌داون/استفاده است. بررسی کارت بعدی...")
                    cooldown_cache[cid] = time.time() + 60
                    continue
                except (PlayingOnAnotherDevice, OnlineOnAnotherDevice):
                    print("\n🚨 خطای ۱۲۴: دستگاه دیگری در حال بازی است! منتظر می‌مانیم سشن آزاد شود...")
                    time.sleep(30)
                    break

                # Success!
                if isinstance(res, dict) and res.get("q"):
                    bot.queue_number = res["q"]

                gold_earned = int(res.get("gold", res.get("gold_earned", 0)))
                xp_earned = int(res.get("xp", res.get("xp_earned", 0)))
                total_gold += gold_earned
                total_xp += xp_earned
                completed += 1

                # Mark this card locally in cooldown for 30s
                cooldown_cache[cid] = time.time() + 30

                print(f"✅ موفق! (+{gold_earned:,} سکه 🪙, +{xp_earned:,} تجربه ⭐) [مجموع سکه: +{total_gold:,}]")
                quest_done_in_this_cycle = True
                break

            # 4. If none of the 10 weakest cards were available
            if not quest_done_in_this_cycle:
                print(f"\n⚠️ تمامی {len(candidates)} کارت ضعیف در کول‌داون هستند.")
                print("🔄 ۵ ثانیه استراحت، سپس بررسی مجدد از ضعیف‌ترین کارت...")
                time.sleep(5)
                continue

            # 5. Sleep 2 seconds before next quest
            print("   ⏳ ۲ ثانیه اسلیپ قبل از ماموریت بعدی...")
            time.sleep(2)

        except KeyboardInterrupt:
            print("\n🛑 اجرای ماموریت‌ها توسط کاربر متوقف شد.")
            break
        except CaptchaRequired:
            print("\n🚨 کپچا مورد نیاز است! اجرای خودکار متوقف شد.")
            break
        except (PlayingOnAnotherDevice, OnlineOnAnotherDevice):
            print("\n🚨 خطای ۱۲۴: دستگاه دیگر متصل است. ۳۰ ثانیه صبر...")
            time.sleep(30)
            continue
        except Exception as e:
            print(f"\n⚠️ خطا در انجام ماموریت: {e}. تلاش مجدد در ۵ ثانیه...")
            time.sleep(5)
            continue

    print("\n" + "=" * 65)
    print("📊 گزارش جلسه ماموریت‌ها:")
    print(f"   تعداد ماموریت‌های انجام شده : {completed}")
    print(f"   مجموع سکه به دست آمده      : +{total_gold:,} 🪙")
    print(f"   مجموع تجربه به دست آمده    : +{total_xp:,} ⭐")
    print("=" * 65 + "\n")


def action_auto_battle(bot: Client, count: int = 10):
    """Execute automated battles with top cards."""
    print("\n" + "=" * 60)
    print("⚔️ شروع نبرد خودکار (Auto Battle)")
    print(f"   تعداد نبرد هدف: {count}")
    print("=" * 60)

    wins = 0
    losses = 0
    total_gold = 0
    total_xp = 0

    for i in range(1, count + 1):
        try:
            player_data = safe_load_player(bot)
            user_id = player_data.get("id")
            cards_list = parse_cards_list(player_data)

            battle_cards = get_top_attack_cards(cards_list, count=4)
            if not battle_cards:
                print("⚠️ کارتی برای نبرد در دسترس نیست (احتمالاً در کول‌داون). ۱۰ ثانیه توقف...")
                time.sleep(10)
                continue

            opponents = bot.getOpponents()
            if not opponents:
                print("⚠️ حریفی یافت نشد. ۵ ثانیه توقف...")
                time.sleep(5)
                continue

            target = opponents[0]
            target_id = int(target.get("id", target.get("player_id")))
            target_name = target.get("name", f"Player #{target_id}")
            target_def = target.get("defense", target.get("power", 0))

            print(f"⚔️ [نبرد #{i}/{count}] حمله به '{target_name}' (دفاع: {target_def:,}) با {len(battle_cards)} کارت...", end=" ", flush=True)

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
                print(f"🏆 پیروزی! (+{gold:,} سکه، +{xp:,} تجربه)")
            else:
                losses += 1
                print(f"💀 شکست در برابر {target_name}")

            time.sleep(3)

        except CaptchaRequired:
            print("\n🚨 کپچا مورد نیاز است! فرآیند نبرد متوقف شد.")
            break
        except KeyboardInterrupt:
            print("\n🛑 توسط کاربر متوقف شد.")
            break
        except (PlayingOnAnotherDevice, OnlineOnAnotherDevice):
            print("\n🚨 خطای ۱۲۴: دستگاه دیگری متصل است. ۳۰ ثانیه صبر...")
            time.sleep(30)
            continue
        except Exception as e:
            print(f"\n⚠️ خطای نبرد: {e}")
            time.sleep(5)

    print("\n" + "=" * 60)
    print("📊 گزارش جلسه نبردها:")
    print(f"   بردها: {wins} | باخت‌ها: {losses} | سکه: +{total_gold:,} | تجربه: +{total_xp:,}")
    print("=" * 60 + "\n")


def action_collect_mine(bot: Client):
    """Collect gold from mine."""
    print("\n⛏️ در حال جمع‌آوری طلای معدن...")
    try:
        res = bot.collectMinedGold()
        gold = res.get("gold", res.get("gold_collected", 0))
        print(f"✅ با موفقیت {gold:,} سکه از معدن جمع‌آوری شد!")
    except Exception as e:
        print(f"⚠️ خطای جمع‌آوری طلا از معدن: {e}")


def interactive_menu(bot: Client):
    """Interactive console menu."""
    while True:
        print("\n" + "=" * 50)
        print("🍉 منوی ربات فروت‌کرافت (FruitCraft Bot)")
        print("=" * 50)
        print("1. 👤 اطلاعات اکانت (Account Information)")
        print("2. 📜 ماموریت خودکار (Auto Quest - کارت ضعیف و ۲ ثانیه اسلیپ)")
        print("3. ⚔️ نبرد خودکار (Auto Battle)")
        print("4. ⛏️ جمع‌آوری طلای معدن (Collect Mined Gold)")
        print("0. ❌ خروج (Exit)")
        print("=" * 50)

        try:
            choice = input("شماره گزینه را وارد کنید [0-4]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nخداحافظ!")
            break

        if choice == "1":
            action_account_info(bot)
        elif choice == "2":
            cnt_str = input("تعداد ماموریت (0 برای اجرای نامحدود): ").strip()
            cnt = int(cnt_str) if cnt_str.isdigit() else 0
            action_auto_quest(bot, count=cnt)
        elif choice == "3":
            cnt_str = input("تعداد نبردها (پیش‌فرض 10): ").strip()
            cnt = int(cnt_str) if cnt_str.isdigit() else 10
            action_auto_battle(bot, count=cnt)
        elif choice == "4":
            action_collect_mine(bot)
        elif choice == "0":
            print("خروج از برنامه. موفق باشید!")
            break
        else:
            print("گزینه نامعتبر است! لطفاً عددی بین 0 تا 4 وارد کنید.")
