IP = "0.0.0.0"
PORT = 6969
CACHE_LENGTH = 300 # Time in seconds between cache update

API_VERSION = "v4"

import asyncio
import datetime
import json
import math
import logging

import aiohttp
import django.template
from aiohttp import web
from django.conf import settings

settings.configure()

fmt = "[%(filename)s][%(asctime)s][%(levelname)s] %(message)s"
datefmt = "%Y/%m/%d-%H:%M:%S"

logging.basicConfig(
  handlers = [
    #logging.FileHandler('log.txt'),
    logging.StreamHandler()
  ],
  format= fmt,
  datefmt = datefmt,
  level=logging.INFO,
)

LOG = logging.getLogger()

with open("config.json") as f:
  config = json.loads(f.read())

engine = django.template.Engine()

with open("template.html") as f:
  tmpl = engine.from_string(f.read())


cache = {}
cacheTime = datetime.datetime.now()

class Wallet:
  def __init__(self,wallet,coin,name):
    self.wallet = wallet
    self.coin = coin
    self.name = name
    self.info = {}

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
      sortStageOne = {}

      for k,v in data["data"].items():
        if not v["workers"]: continue
        totalHash = 0

        for worker in v["workers"]:
          if not k in sortStageOne: sortStageOne[k]={"workers":[]}
          totalHash += int(worker["rhr"])
          w = {"name":worker["name"],"hashrate":worker["rhr"],"referral":worker["referral"]}
          sortStageOne[k]["workers"].append(w)
        sortStageOne[k]["hashrate"] = str(totalHash)

      for k,v in sortStageOne.items():
        out["workers"].append({"algo":k,"hashrate":sortStageOne[k]['hashrate'],"workers":sortStageOne[k]["workers"]})
    
    self.info = out
    return out

wallets = []

for k,v in config.items():
  wallets.append(Wallet(v["wallet"],v["coin"],k))

async def assembleTemplate():
  wallet_list = []
  for k,v in cache.items():
    wallet_list.append(v)
  return tmpl.render(django.template.Context({"wallet_list":wallet_list,"current_time":cacheTime.strftime("%c")}))

routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
  # Render template.
  html = await assembleTemplate()
  return web.Response(text=html,content_type="text/html")

@routes.post("/api/updatecache")
async def cacheEndpoint(request):
  await updateCache(request.app.client)
  return web.Response(text="OK",status=200)

app = web.Application()
app.add_routes(routes)
app.add_routes([web.static("/","static")])

async def updateCache(client):
  for wallet in wallets:
    cache[wallet.name] = await wallet.getInformation(client)
  global cacheTime;cacheTime = datetime.datetime.now()

async def updateCacheRunner(client):
  while True:
    await updateCache(client)
    await asyncio.sleep(CACHE_LENGTH)

backgroundTasks = set() # This stores references to the tasks or something

async def startup():
  try:
    LOG.info("Starting webserver")

    # Setup the aiohttp webserver
    app.client = aiohttp.ClientSession()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,IP,PORT)
    await site.start()

    # Setup the cache updating task
    cacheTask = asyncio.create_task(updateCacheRunner(app.client),name="cache_update")
    backgroundTasks.add(cacheTask)
    cacheTask.add_done_callback(backgroundTasks.discard)

    LOG.info("Webserver started")
    await asyncio.sleep(math.inf)
  except KeyboardInterrupt:pass
  finally:
    await site.stop()
    await app.client.close()

asyncio.run(startup())
