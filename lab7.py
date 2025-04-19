import json
import os
import aiohttp
import asyncio
from dotenv import load_dotenv


load_dotenv()
X_API_KEY = os.getenv('X_API_KEY')


class OrdersChecker:

    def __init__(self, session: aiohttp.ClientSession, path_to_json: str, symbol: str):
        self.session = session
        self.path_to_json = path_to_json
        self.base_url = "https://api.ataix.kz/api"
        self.symbol = symbol
        self.payload = {
            "page": 1,
            "itemsPerPage": 100,
            "symbol": symbol, # Все операции были только с 1 инч
            "startDate": 0,
            "endDate": 0,
            "hideCanceled": "true"
        }
        self.headers = {
            "X-API-KEY": X_API_KEY,
            "Content-Type": "application/json"
        }


    async def history_orders_check(self):
        """
            Функция просматривающая историю ордеров на сайте через API или считывающая из .json
        """
        if self.path_to_json:
            with open(self.path_to_json, 'r', encoding='utf-8') as file:
                response_js = json.load(file)
                filled_orders_data = [{"OrderID": elem["orderID"], "price": float(elem["price"]), "quantity": int(elem["quantity"])}
                    for index, elem in enumerate(response_js["result"]) if response_js["result"][index]["status"] == "filled"]

                return filled_orders_data

        url = f"{self.base_url}/orders/history"
        async with self.session.get(url=url, headers=self.headers, params=self.payload) as response:
            if response.status == 200:
                response_js = await response.json()
                filled_orders_data = [{"OrderID": elem["orderID"], "price": float(elem["price"]), "quantity": int(elem["quantity"])}
                                      for index, elem in enumerate(response_js["result"])
                                    if response_js["result"][index]["status"] == "filled"]
                return filled_orders_data


    async def post_orders(self):
        """
            Функция которая постит ордера со статусом filled на 2% больше
        """
        orders_data = await self.history_orders_check()
        for order in orders_data[:3]:
            print(order)
            json_payload = {
                "symbol": self.symbol,
                "side": "sell",
                "type": "limit",
                "quantity": order["quantity"],
                "price": round(order["price"] + (order["price"] / 100 * 2), 4), # увеличиваем цену на 2 %
                "subType": "gtc"
            }
            print(json_payload)
            async with self.session.post(url=f"{self.base_url}/orders", headers=self.headers, json=json_payload) as response:
                response_js = await response.json()
                if response_js["status"]:
                    print("Ордер создан!")
                    print(json.dumps(response_js, indent=4))
                    with open("result.json", "a", encoding="utf-8") as f:
                        f.write(json.dumps(response_js, indent=4))
                else:
                    print(json.dumps(response_js, indent=4))
                    print("Замечено отклонение от рыночной цены более чем на 10% Ордер не может выполниться")



async def main():
    """
        Запусти меня!
    """
    async with aiohttp.ClientSession() as session:
        absum = OrdersChecker(session, os.path.abspath("myjsOrders.json"), "1INCH/USDT")
        await absum.history_orders_check()


if __name__ == "__main__":
    asyncio.run(main())