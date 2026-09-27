from fruitbot import Client
from fruitbot.enums import CardPackTypes

bot = Client(session_name="fruit", restore_key="head9229burst65")

data = bot.loadPlayer(save_session=True)
print(f"name: {data['name']},   amount of gold: {data['gold']},  id: {data['id']}")
print(bot.buyCardPack(CardPackTypes.BROWN_PACK))