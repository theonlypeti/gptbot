import logging
from os import getenv
from random import choice

from nextcord.ext import commands, tasks
import pyowm


class FujkinCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.fujkin.start()
        self.fujkinLogger = client.logger.getChild("FujkinLogger")
        self.does_it_fujkin = False
        self.does_it_esik = False

    @tasks.loop(minutes=30)
    async def fujkin(self):
        try:
            weather = pyowm.OWM(getenv("OWM_TOKEN")).weather_manager().weather_at_place("Gabčíkovo,sk").weather
            rain = weather.rain
            wind = round(weather.wind()["speed"] * 3.6, 2)
        except Exception as e:
            self.fujkinLogger.error(e)
        else:
            if wind > 30:
                if not self.does_it_fujkin: #ne spameljen annyit
                    self.does_it_fujkin = True
                    for channel in self.channels:
                        await channel.send("https://tenor.com/view/sz%C3%A9l-f%C3%BAj-a-sz%C3%A9l-fujkin-asz%C3%A9lfujkin-id%C5%91j%C3%A1r%C3%A1s-weather-gif-21406085")
                        await channel.send(f"{wind} km/h")
            else:
                self.does_it_fujkin = False
                self.fujkinLogger.info(f"nemfujkin ({wind} km/h)")

            if rain and not self.does_it_esik:
                self.does_it_esik = True
                for channel in self.channels:
                    gif = choice((
                         "https://tenor.com/view/bill-wurtz-weather-update-rain-raining-gif-17835062102625163877",
                        "https://tenor.com/view/good-morning-humid-raining-duck-need-umbrella-gif-5877669406246809546",
                        "https://tenor.com/view/heavy-rain-dog-drop-umbrella-gif-15721755",
                        "https://tenor.com/view/yelynnn-rain-yelynnn-yelynn-troi-mua-yelynn-rain-yelynnn-troi-mua-gif-15054810487328860910",
                        "https://tenor.com/view/raining-rain-gif-24812227",
                        "https://tenor.com/view/mice-cute-gif-12813574423840616030"
                    ))
                    await channel.send(gif)
                    await channel.send(f"{rain['1h']} mm/h")
            else:
                self.does_it_esik = False

    @fujkin.before_loop
    async def before_fujkin(self):
        await self.client.wait_until_ready()
        # self.channels = (self.client.get_channel(607897146750140457),) #rageon
        self.channels = (self.client.get_channel(897298417431240714),) #bosi


def setup(client):
    client.add_cog(FujkinCog(client))
