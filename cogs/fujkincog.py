import logging
from os import getenv
from nextcord.ext import commands, tasks
import pyowm


class FujkinCog(commands.Cog):
    def __init__(self, client, logger: logging.Logger):
        self.client = client
        self.fujkin.start()
        self.fujkinLogger = logger.getChild("FujkinLogger")
        self.does_it_fujkin = False

    @tasks.loop(minutes=30)
    async def fujkin(self):
        try:
            wind = round(pyowm.OWM(getenv("OWM_TOKEN")).weather_manager().weather_at_place("Bratislava,sk").weather.wind()["speed"] * 3.6, 2)
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

    @fujkin.before_loop
    async def before_fujkin(self):
        await self.client.wait_until_ready()
        # self.channels = (self.client.get_channel(607897146750140457),) #rageon
        self.channels = (self.client.get_channel(897298417431240714),) #rageon


def setup(client, baselogger): #bot shit
    client.add_cog(FujkinCog(client, baselogger))
