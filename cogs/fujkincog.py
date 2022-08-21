from nextcord.ext import commands,tasks
import pyowm

class FujkinCog(commands.Cog):
    def __init__(self,client):
        self.client = client
        self.fujkin.start()
        self.does_it_fujkin = False

    @tasks.loop(minutes=30)
    async def fujkin(self):
        wind = round(pyowm.OWM("385bfdf19d55e8f1d667cad1fad28568").weather_manager().weather_at_place("Dunajská Streda,sk").weather.wind()["speed"] * 3.6, 2)
        if wind > 30:
            if not self.does_it_fujkin: #ne spameljen annyit
                self.does_it_fujkin = True
                for channel in self.channels:
                    await channel.send("https://tenor.com/view/sz%C3%A9l-f%C3%BAj-a-sz%C3%A9l-fujkin-asz%C3%A9lfujkin-id%C5%91j%C3%A1r%C3%A1s-weather-gif-21406085")
                    await channel.send(f"{wind} km/h")
        else:
            self.does_it_fujkin = False

    @fujkin.before_loop
    async def before_fujkin(self):
        await self.client.wait_until_ready()
        self.channels = (self.client.get_guild(601381789096738863).get_channel(607897146750140457),) #rageon

def setup(client,baselogger): #bot shit
    client.add_cog(FujkinCog(client))
