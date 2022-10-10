IP = "0.0.0.0"
PORT = 6969

API_VERSION = "v4"

import asyncio
import json
import math

import aiohttp
from aiohttp import web
import django.template

with open("config.json") as f:
  config = json.loads(f.read())

engine = django.template.Engine()

with open("template.djt") as f:
  tmpl = engine.from_string(f.read())


class Wallet:
  def __init__(self,wallet,coin,name):
    self.wallet = wallet
    self.coin = coin
    self.name = name

  # {
  #   "balance": str, "1.234"
  #   "wallet": str, - COIN:WALLET
  #   "name": str, - Set by config
  #   "workers": [
  #     {"name": str, "algo": str "hashrate": str}
  #   ]
  # }
  async def getInformation(self,client):
    out = {
      "wallet": self.wallet,
      "name": self.name,
      "coin": self.coin,
      "workers": [],
    }
    async with client.get(f"https://api.unmineable.com/{API_VERSION}/address/{self.wallet}?coin={self.coin}") as resp:
      data = (await resp.json())["data"]
      uuid = data["uuid"]
      out["balance"] = data["balance"]
    async with client.get(f"https://api.unmineable.com/{API_VERSION}/account/{uuid}/workers") as workerInfo:
      data = (await workerInfo.json())
      for k,v in data["data"].items():
        for worker in v["workers"]:
          w = {"name":worker["name"],"algo":k,"hashrate":worker["rhr"]}
          out["workers"].append(w)
    return out

wallets = []

for k,v in config.items():
  wallets.append(Wallet(v["wallet"],v["coin"],k))

async def assembleTemplate(client):
  wallet_list = []
  for wallet in wallets:
    wallet_list.append(await wallet.getInformation(client))
  return tmpl.render(django.template.Context({"wallet_list":wallet_list}))

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
  # Render template.
  html = await assembleTemplate(request.app.client)
  return web.Response(text=html,content_type="text/html")

@routes.get("/styles.css")
async def styles(request):
  return web.FileResponse("./styles.css")

app = web.Application()
app.add_routes(routes)

async def startup():
  try:
    print("Starting")
    app.client = aiohttp.ClientSession()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,IP,PORT)
    await site.start()
    print("Started")
    await asyncio.sleep(math.inf)
  except KeyboardInterrupt:pass
  finally:
    await site.stop()
    await app.client.close()

asyncio.run(startup())
