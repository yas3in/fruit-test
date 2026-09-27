import asyncio
import hashlib
from fruitcraft_bot.cli import get_account_config
from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import BattleService

async def main():
    cfg = get_account_config(None)
    client = FruitCraftAPIClient()
    auth = AuthService(client)
    battle = BattleService(client, auth)
    
    await auth.load_player(cfg.restore_key, cfg.device)
    q = auth.q
    if not q:
        print("Failed to get q")
        return
        
    print(f"Base q: {q}")
    
    # We need to find an opponent first
    resp = await client.request("battle/getopponents", {})
    data = resp.data if isinstance(resp.data, dict) else {}
    opps = data.get("opponents", [])
    if not opps:
        print("No opponents")
        return
    opp_id = str(opps[0]["id"])
    
    cards_list = [664166187, 690207078, 689160097, 713614037]
    cards_str = ",".join(str(c) for c in cards_list)
    
    # Let's generate a massive list of potential check hashes
    test_hashes = []
    
    # 1. Plain q
    test_hashes.append(("plain_q", q))
    
    # 2. Standard MD5
    test_hashes.append(("md5(q)", hashlib.md5(q.encode()).hexdigest()))
    
    # 3. MD5 with salts
    salts = ["fruitcraft", "FruitCraft", "battle", "quest", "check", "hash", "salt", "-fruitcraft", "_fruitcraft"]
    for s in salts:
        test_hashes.append((f"md5(q+{s})", hashlib.md5((q + s).encode()).hexdigest()))
        test_hashes.append((f"md5({s}+q)", hashlib.md5((s + q).encode()).hexdigest()))
        
    # 4. MD5 with payload fields
    for field in [opp_id, cards_str]:
        test_hashes.append((f"md5(q+{field})", hashlib.md5((q + field).encode()).hexdigest()))
        test_hashes.append((f"md5({field}+q)", hashlib.md5((field + q).encode()).hexdigest()))
        
    # 5. MD5 of MD5
    test_hashes.append(("md5(md5(q))", hashlib.md5(hashlib.md5(q.encode()).hexdigest().encode()).hexdigest()))
    
    print(f"Testing {len(test_hashes)} hash combinations...")
    
    for name, check in test_hashes:
        for use_str_cards in [True, False]:
            for use_hero in [False, True]:
                payload = {
                    "opponent_id": opp_id,
                    "cards": cards_str if use_str_cards else cards_list,
                    "check": check
                }
                if use_hero:
                    payload["hero_id"] = 0
                    
                try:
                    resp = await client.request("battle/battle", payload)
                    d = resp.data if isinstance(resp.data, dict) else {}
                    if d.get("code") != 118:
                        print(f"\nSUCCESS! Code is not 118 (Got {d.get('code')})")
                        print(f"Winning Formula: {name}")
                        print(f"Winning Payload: {payload}")
                        return
                except Exception as e:
                    if hasattr(e, 'code') and e.code == 118:
                        continue
                    if hasattr(e, 'code') and e.code == 0:
                        continue
                    print(f"Other error for {name}: {e}")
                    
    print("\nALL COMBINATIONS FAILED (Still Code 118)")

if __name__ == "__main__":
    asyncio.run(main())
