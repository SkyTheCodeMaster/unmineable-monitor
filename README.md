# unmineable-monitor
This is a simple webserver script to host a monitoring program for Unmineable workers.

## Configuration
Configuration is simple, edit the variables at the top of the `main.py` script for where the server is hosted (ip, and port). Default is `0.0.0.0:6969`.

## config.json
The config.json file is where the workers are stored.
The format is as follows:
```json
{
  "Friendly name here": {"wallet":"0x1234567890","coin":"AVAX"}
}
```
This can be repeated for as many addresses that you have, and as many coins as you have.

Once this is done and the server is running, go to `IP:PORT` and you will see a friendly breakdown of everything.