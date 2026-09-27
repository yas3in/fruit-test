import asyncio
import hashlib
import json
import logging
import subprocess
import urllib.parse
from fruitcraft_bot.api.crypto import encrypt_payload, decrypt_response, DEFAULT_XOR_KEY
from fruitcraft_bot.config import AppSettings, DeviceConfig
from fruitcraft_bot.api.models import PlayerLoadRequest

def run_curl(url, data_str, headers_dict, passport=None):
    cmd = ["curl", "-s", "-X", "POST", url, "-d", data_str]
    for k, v in headers_dict.items():
        if k.lower() == "host": continue  # curl adds this
        cmd.extend(["-H", f"{k}: {v}"])
    if passport:
        cmd.extend(["-H", f"Cookie: FRUITPASSPORT={passport}"])
    
    # We need to capture headers to get the cookie
    cmd.extend(["-i"])
    
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", errors="ignore")
        # Split headers and body
        parts = out.split("\r\n\r\n", 1)
        if len(parts) == 2:
            head, body = parts
        else:
            head, body = out, ""
            
        new_pass = None
        for line in head.split("\r\n"):
            if line.lower().startswith("set-cookie:"):
                if "FRUITPASSPORT=" in line:
                    new_pass = line.split("FRUITPASSPORT=")[1].split(";")[0]
        
        return body, new_pass
    except subprocess.CalledProcessError as e:
        print(f"Curl failed: {e.output.decode('utf-8', errors='ignore')}")
        return "", None

async def diagnose():
    settings = AppSettings()
    key = settings.restore_key.get_secret_value()
    dc = DeviceConfig()
    base_url = settings.base_url.rstrip("/")

    req = PlayerLoadRequest(
        game_version=dc.game_version, udid=dc.udid, os_type=dc.os_type,
        restore_key=key, os_version=dc.os_version, model=dc.model,
        metrix_uid=dc.metrix_uid, appsflyer_uid=dc.appsflyer_uid,
        device_name=dc.device_name, store_type=dc.store_type,
    )
    encrypted = encrypt_payload(req, DEFAULT_XOR_KEY)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; google pixel 2 Build/N2G47H)",
    }

    print("=" * 60)
    print("STEP 1: POST player/load via curl")
    print("=" * 60)
    raw, passport = run_curl(f"{base_url}/player/load", encrypted, headers)
    
    decrypted = decrypt_response(raw, DEFAULT_XOR_KEY)
    if not isinstance(decrypted, dict):
        print("Failed to decode player/load")
        return

    print(f"status={decrypted.get('status')}, code={decrypted.get('code')}")
    q_val = decrypted.get("q")
    print(f"q={q_val}")

    player = decrypted.get("player", decrypted)
    cards_raw = decrypted.get("cards", player.get("cards", []) if isinstance(player, dict) else [])
    if isinstance(cards_raw, dict): cards_list = list(cards_raw.values())
    elif isinstance(cards_raw, list): cards_list = cards_raw
    else: cards_list = []

    usable = []
    for c in cards_list:
        if isinstance(c, dict):
            cid = int(c.get("id", c.get("card_id", 0)))
            power = int(c.get("power", c.get("attack", 0)))
            if not bool(c.get("in_cooldown", False)) and cid:
                usable.append({"id": cid, "power": power})
    usable.sort(key=lambda x: x["power"], reverse=True)
    top4 = [c["id"] for c in usable[:4]]

    print("\n" + "=" * 60)
    print("STEP 2: POST battle/getopponents")
    print("=" * 60)
    opp_enc = encrypt_payload({}, DEFAULT_XOR_KEY)
    opp_raw, new_pass = run_curl(f"{base_url}/battle/getopponents", opp_enc, headers, passport)
    if new_pass: passport = new_pass
    
    opp_d = decrypt_response(opp_raw, DEFAULT_XOR_KEY)
    opp_list = []
    if isinstance(opp_d, dict):
        # Update q if present
        if "q" in opp_d: q_val = opp_d["q"]
        od = opp_d.get("data", opp_d)
        if isinstance(od, list): opp_list = od
        elif isinstance(od, dict): opp_list = od.get("opponents", od.get("players", []))
        elif isinstance(opp_d.get("opponents"), list): opp_list = opp_d["opponents"]

    if not opp_list or not isinstance(opp_list[0], dict):
        print("No opponents found")
        return

    tid = str(opp_list[0].get("id", ""))
    print(f"Target opponent: {tid}")

    print("\n" + "=" * 60)
    print("STEP 3: POST battle/quest formats")
    print("=" * 60)

    check = hashlib.md5(str(q_val).encode("utf-8")).hexdigest() if q_val else None

    # Test permutations for quest cards format
    quest_fmts = {
        "A: cards as string": {"cards": ",".join(str(c) for c in top4), "check": check},
        "B: cards as array": {"cards": top4, "check": check},
        "C: cards as dict": {"cards": {str(i): c for i, c in enumerate(top4)}, "check": check},
        "D: cards string + hero_id": {"cards": ",".join(str(c) for c in top4), "hero_id": 0, "check": check},
        "E: NO cards (empty)": {"check": check},
    }

    for label, payload in quest_fmts.items():
        print(f"\n--- {label} ---")
        enc = encrypt_payload(payload, DEFAULT_XOR_KEY)
        b_raw, np = run_curl(f"{base_url}/battle/quest", enc, headers, passport)
        d = decrypt_response(b_raw, DEFAULT_XOR_KEY)
        if isinstance(d, dict):
            print(f"Response: {json.dumps(d, ensure_ascii=False)[:300]}")
            if d.get("status") not in (False, "false", 0):
                print(f"✅ FORMAT {label} WORKED!")
                break
            else:
                data_val = d.get("data", {})
                code = data_val.get("code") if isinstance(data_val, dict) else d.get("code")
                print(f"❌ FAILED (code: {code})")
        else:
            print(f"Failed to parse: {str(d)[:100]}")

    print("\n" + "=" * 60)
    print("STEP 4: POST battle/battle formats")
    print("=" * 60)

    battle_fmts = {
        "A: opponent_id + cards(str)": {"opponent_id": tid, "cards": ",".join(str(c) for c in top4), "check": check},
        "B: opponent_id + cards(list)": {"opponent_id": tid, "cards": top4, "check": check},
        "C: id + cards(str)": {"id": tid, "cards": ",".join(str(c) for c in top4), "check": check},
        "D: id + cards(list)": {"id": tid, "cards": top4, "check": check},
    }

    for label, payload in battle_fmts.items():
        print(f"\n--- {label} ---")
        enc = encrypt_payload(payload, DEFAULT_XOR_KEY)
        b_raw, np = run_curl(f"{base_url}/battle/battle", enc, headers, passport)
        d = decrypt_response(b_raw, DEFAULT_XOR_KEY)
        if isinstance(d, dict):
            print(f"Response: {json.dumps(d, ensure_ascii=False)[:300]}")
            if d.get("status") not in (False, "false", 0):
                print(f"✅ FORMAT {label} WORKED!")
                break
            else:
                data_val = d.get("data", {})
                code = data_val.get("code") if isinstance(data_val, dict) else d.get("code")
                print(f"❌ FAILED (code: {code})")
        else:
            print(f"Failed to parse: {str(d)[:100]}")

if __name__ == "__main__":
    asyncio.run(diagnose())
