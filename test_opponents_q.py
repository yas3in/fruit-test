import asyncio
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
    print(f"q after load: {auth.q}")
    
    resp = await client.request("battle/getopponents", {})
    data = resp.data if isinstance(resp.data, dict) else {}
    print(f"Data keys in getopponents: {data.keys() if isinstance(data, dict) else type(data)}")
    if isinstance(data, dict) and "q" in data:
        print(f"q after getopponents: {data['q']}")
    else:
        print("NO 'q' IN getopponents response!")

asyncio.run(main())
