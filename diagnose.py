"""Diagnostic script: capture raw server responses for battle/quest."""
import asyncio
import hashlib
import json
import logging

logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s")

from fruitcraft_bot.api.crypto import encrypt_payload, decrypt_response, DEFAULT_XOR_KEY
from fruitcraft_bot.config import AppSettings, DeviceConfig
from fruitcraft_bot.api.models import PlayerLoadRequest


async def diagnose():
    settings = AppSettings()
    if not settings.restore_key:
        print("ERROR: No FRUITCRAFT_RESTORE_KEY set")
        return
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
        "Host": "iran.fruitcraft.ir",
    }

    import httpx
    # Note: Use trust_env=True to pick up the user's proxy settings (e.g. socks://127.0.0.1:10808)
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), trust_env=True, follow_redirects=True) as http:
        # STEP 1: player/load
        print("=" * 60)
        print("STEP 1: POST player/load")
        print("=" * 60)
        resp = await http.post(f"{base_url}/player/load", content=encrypted, headers=headers)
        print(f"HTTP Status: {resp.status_code}")
        raw = resp.content
        print(f"Raw body length: {len(raw)} bytes")
        print(f"Raw body (first 200): {raw[:200]}")

        decrypted = decrypt_response(raw, DEFAULT_XOR_KEY)
        print(f"Decrypted type: {type(decrypted).__name__}")

        if not isinstance(decrypted, dict):
            print(f"Unexpected: {str(decrypted)[:500]}")
            return

        print(f"Top keys: {list(decrypted.keys())}")
        print(f"status={decrypted.get('status')}, code={decrypted.get('code')}, q={repr(decrypted.get('q'))}")

        player = decrypted.get("player", decrypted)
        if isinstance(player, dict):
            print(f"Player: id={player.get('id')}, name={player.get('name')}, gold={player.get('gold')}")

        cards_raw = decrypted.get("cards", player.get("cards", []) if isinstance(player, dict) else [])
        if isinstance(cards_raw, dict):
            cards_list = list(cards_raw.values())
        elif isinstance(cards_raw, list):
            cards_list = cards_raw
        else:
            cards_list = []
        print(f"Cards: {len(cards_list)} entries")

        if cards_list and isinstance(cards_list[0], dict):
            print(f"Card keys: {list(cards_list[0].keys())}")
            sorted_c = sorted(cards_list, key=lambda c: int(c.get("power", c.get("attack", 0))), reverse=True)
            for i, c in enumerate(sorted_c[:5]):
                print(f"  top{i+1}: id={c.get('id')}, power={c.get('power',c.get('attack'))}, cooldown={c.get('in_cooldown')}")

        passport = resp.cookies.get("FRUITPASSPORT")
        if not passport:
            sc = resp.headers.get("set-cookie", "")
            if "FRUITPASSPORT=" in sc:
                passport = sc.split("FRUITPASSPORT=")[1].split(";")[0]
        if passport:
            headers["Cookie"] = f"FRUITPASSPORT={passport}"
            print(f"Passport: {passport[:30]}...")
        else:
            print("WARNING: NO PASSPORT COOKIE!")

        q_val = decrypted.get("q")
        usable = []
        for c in cards_list:
            if isinstance(c, dict):
                cid = int(c.get("id", c.get("card_id", 0)))
                power = int(c.get("power", c.get("attack", 0)))
                if not bool(c.get("in_cooldown", False)) and cid:
                    usable.append({"id": cid, "power": power})
        usable.sort(key=lambda x: x["power"], reverse=True)
        top4 = [c["id"] for c in usable[:4]]

        # STEP 2: battle/quest with different formats
        print("\n" + "=" * 60)
        print("STEP 2: POST battle/quest - Testing formats")
        print("=" * 60)
        check = hashlib.md5(str(q_val).encode("utf-8")).hexdigest() if q_val else None
        print(f"q={q_val}, check={check}, top4={top4}")

        formats = {
            "A: cards=comma-str": {"cards": ",".join(str(c) for c in top4), **({"check": check} if check else {})},
            "B: cards=json-array": {"cards": top4, **({"check": check} if check else {})},
            "C: cards[0..3]=id": {**{f"cards[{i}]": cid for i, cid in enumerate(top4)}, **({"check": check} if check else {})},
            "D: cards=comma-str NO check": {"cards": ",".join(str(c) for c in top4)},
        }

        for label, payload in formats.items():
            print(f"\n--- {label} ---")
            print(f"Payload JSON: {json.dumps(payload, default=str)}")
            enc = encrypt_payload(payload, DEFAULT_XOR_KEY)
            try:
                r = await http.post(f"{base_url}/battle/quest", content=enc, headers=headers)
                d = decrypt_response(r.content, DEFAULT_XOR_KEY)
                print(f"Response: {json.dumps(d, ensure_ascii=False, default=str)[:400]}")
                np = r.cookies.get("FRUITPASSPORT")
                if np:
                    headers["Cookie"] = f"FRUITPASSPORT={np}"
                if isinstance(d, dict):
                    new_q = d.get("q")
                    if new_q:
                        q_val = new_q
                    if d.get("status") not in (False, "false", 0):
                        print(f">>> SUCCESS with {label}!")
                    else:
                        print(f">>> FAILED: status={d.get('status')}, code={d.get('code')}, msg={d.get('message','')}{d.get('error','')}{d.get('text','')}")
            except Exception as e:
                print(f"Error: {e}")

        # STEP 3: battle/battle
        print("\n" + "=" * 60)
        print("STEP 3: POST battle/battle - Testing formats")
        print("=" * 60)
        try:
            opp_enc = encrypt_payload({}, DEFAULT_XOR_KEY)
            opp_r = await http.post(f"{base_url}/battle/getopponents", content=opp_enc, headers=headers)
            opp_d = decrypt_response(opp_r.content, DEFAULT_XOR_KEY)
            print(f"Opponents: {json.dumps(opp_d, ensure_ascii=False, default=str)[:400]}")
            np = opp_r.cookies.get("FRUITPASSPORT")
            if np:
                headers["Cookie"] = f"FRUITPASSPORT={np}"

            opp_list = []
            if isinstance(opp_d, dict):
                od = opp_d.get("data", opp_d)
                if isinstance(od, list): opp_list = od
                elif isinstance(od, dict): opp_list = od.get("opponents", od.get("players", []))

            if opp_list and isinstance(opp_list[0], dict):
                tid = str(opp_list[0].get("id", ""))
                print(f"Target: id={tid}, name={opp_list[0].get('name')}")
                check2 = hashlib.md5(str(q_val).encode("utf-8")).hexdigest() if q_val else None

                battle_fmts = {
                    "A: opponent_id+cards-str": {"opponent_id": tid, "cards": ",".join(str(c) for c in top4), **({"check": check2} if check2 else {})},
                    "B: id+cards-array": {"id": tid, "cards": top4, **({"check": check2} if check2 else {})},
                    "C: id+opponent_id+cards-str": {"id": tid, "opponent_id": tid, "cards": ",".join(str(c) for c in top4), **({"check": check2} if check2 else {})},
                    "D: id+cards-str": {"id": tid, "cards": ",".join(str(c) for c in top4), **({"check": check2} if check2 else {})},
                    "E: opponent_id+cards-array": {"opponent_id": tid, "cards": top4, **({"check": check2} if check2 else {})},
                }
                for label, payload in battle_fmts.items():
                    print(f"\n--- {label} ---")
                    print(f"Payload: {json.dumps(payload, default=str)}")
                    enc = encrypt_payload(payload, DEFAULT_XOR_KEY)
                    try:
                        r = await http.post(f"{base_url}/battle/battle", content=enc, headers=headers)
                        d = decrypt_response(r.content, DEFAULT_XOR_KEY)
                        print(f"Response: {json.dumps(d, ensure_ascii=False, default=str)[:400]}")
                        np = r.cookies.get("FRUITPASSPORT")
                        if np:
                            headers["Cookie"] = f"FRUITPASSPORT={np}"
                        if isinstance(d, dict):
                            new_q = d.get("q")
                            if new_q:
                                q_val = new_q
                            if d.get("status") not in (False, "false", 0):
                                print(f">>> SUCCESS with {label}!")
                                break
                            else:
                                print(f">>> FAILED")
                    except Exception as e:
                        print(f"Error: {e}")
            else:
                print("No opponents")
        except Exception as e:
            print(f"Opponents error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
