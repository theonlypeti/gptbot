import random
import aiohttp
from math import ceil
from nextcord.ext import commands
import nextcord as discord
import os
import json
from bs4 import BeautifulSoup as html
from utils.antimakkcen import antimakkcen

path = "D:\\Users\\Peti.B\\Downloads\\ffmpeg-2020-12-01-git-ba6e2a2d05-full_build\\bin\\ffmpeg.exe" #TODO now this is bad
root = os.getcwd()
maindir = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\R3"

with open(r"data\vonatdb.json", "r") as file:
    soundfiles = json.load(file)


class TimeTable(object):
    def __init__(self, time: str, cities: list[str], meska: str, vlaktype: str|None):
        self.time: str = time
        self.cities: list[str] = cities
        self.delay: str = meska
        self.vlaktype: str|None = vlaktype


def custom_round(num: int) -> str:
    if num <= 60:
        return str(ceil(num / 5) * 5)
    elif num<=180:
        return str(round(num, -1))
    elif num<=300:
        return str(ceil(num / 20) * 20)
    elif num<=480:
        return str(ceil(num / 30) * 30)
    else:
        return "VICE480"


class ZSSKCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.tt = None
        self.zsskLogger = client.logger.getChild(f"{__name__}Logger")

    async def getTimeTable(self, link): #dont judge pls
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as req:
                stranka = await req.content.read()
            soup = html(stranka, 'html.parser')
            try:
                a = soup.find("a", attrs={"title": "Zobraziť detail spoja"})
                self.zsskLogger.debug(a)
            except Exception as e:
                self.zsskLogger.error(e)
                return None
            link = a.get("href") #ez szokott errorozni mert nonetype az a
            async with session.get(link) as req:
                stranka = await req.content.read()
        delay = soup.find("a", attrs={"class": "delay-bubble"})
        if delay.contents[0].startswith("Aktuálne"):
            delay = delay.contents[0].split(" ")[2]
        else:
            delay = None
        soup = html(stranka, 'html.parser')
        a = soup.find_all("li", attrs={"class": "item"})
        b = soup.find_all("li", attrs={"class": "item inactive"})
        c = set(a).difference(set(b))
        a = [i for i in a if i in c]
        cities = [child.select("strong.name")[0].contents[0] for child in reversed(a)]
        time = soup.find("span", attrs={"class": "departure"}).contents[-1].strip()
        
        return TimeTable(time, cities, delay, None)

    @discord.slash_command(name="zssk", description="Call the announcer lady to tell you about a train´s schedule", dm_permission=False)
    async def zssk(self, ctx: discord.Interaction, #todo make it print tt to chat, so u dont have to be in voice
                   fromcity: str = discord.SlashOption(name="from", description="City", required=True),
                   tocity: str = discord.SlashOption(name="to", description="City", required=True),
                   time: str = discord.SlashOption(name="time", description="hh:mm", required=False),
                   date: str = discord.SlashOption(name="date", description="dd.mm.yyyy", required=False)):
        await ctx.response.defer()
        try:
            channel = ctx.user.voice.channel
            self.zsskLogger.info(f"{ctx.user} in {channel} used zssk {fromcity} {tocity}")
            try:
                vclient = await channel.connect()
            except Exception as e:
                self.zsskLogger.error(f"{e}")
                vclient = ctx.guild.voice_client
            self.vclient = vclient
            await ctx.send("Working on it...", delete_after=10)
        except AttributeError:
        #if isinstance(channel,type(None)) or channel is None:
            await ctx.send(embed=discord.Embed(title="Command caller not in a voice channel."))
            return
        else:
            link = f"https://cp.hnonline.sk/vlakbus/spojenie/vysledky/?"+(f"date={date}&" if date else "") + (f"time={time}&" if time else "") +f"f={fromcity}&fc=100003&t={tocity}&tc=100003&af=true&trt=150,151,152,153"
            self.zsskLogger.debug(f"{link=},{len(link)=}")
            self.tt = await self.getTimeTable(link)
            if self.tt is None:
                await ctx.send("Not found.", delete_after=5)
            self.znelka()

    @zssk.on_autocomplete("fromcity")
    @zssk.on_autocomplete("tocity")
    async def stanica_autocomplete(self, interaction: discord.Interaction, city: str):
        if city:
            get_near_city = {i:antimakkcen(i).replace(" ", "%20") for i in soundfiles.keys() if antimakkcen(i.casefold()).startswith(antimakkcen(city.casefold()))}
            get_near_city = dict(list(get_near_city.items())[:25])
            self.zsskLogger.debug(get_near_city)
            await interaction.response.send_autocomplete(get_near_city)

    # #not sure if i can use one func for both autocomplete decorators so i just split them
    # async def stanica_autocomplete2(self,interaction, city: str):
    #     if city:
    #         get_near_city = [i for i in soundfiles.keys() if i.casefold().startswith(city.casefold())]
    #         get_near_city = get_near_city[:25]
    #         await interaction.response.send_autocomplete(get_near_city)
            
    def znelka(self): #TODO make these relative paths
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\ZNELKY")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="startOld.WAV"),
                          after=lambda a: self.traintype())

    def traintype(self):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\V1")
        sound = random.choice(os.listdir())
        self.vclient.play(discord.FFmpegPCMAudio(executable=path, source=sound), #NFVOS
                          after=lambda a: self.smerom())

    def smerom(self):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="SM2.WAV"),
                          after=lambda a: self.city(self.tt.cities))

    def city(self, cities):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\R3")
        if len(cities) > 0:
            chosencity = cities.pop()
            try:
                self.zsskLogger.debug(f"{chosencity=}")
                chosencity = soundfiles[chosencity]
            except KeyError:
                self.zsskLogger.error(f"not found {chosencity}")
                self.city(cities)
            except IOError:
                self.zsskLogger.error(f"no file found {chosencity}")
                self.city(cities)
            else:
                self.vclient.play(discord.FFmpegPCMAudio(executable=path, source=chosencity+".WAV"),
                          after=lambda a: self.city(cities))
        else:
            self.prichod(self.tt)
            
    def prichod(self, tt):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="PRPR.WAV"),
                          after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C1\\"+tt.time.split(":")[0]+".WAV"),
                                                  after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C3\\"+str(int(tt.time.split(":")[1]))+".WAV"),
                                                                                            after=lambda a: self.meskanie(tt))))

    def meskanie(self, tt):
        if tt.delay:
            try:
                delay = custom_round(int(tt.delay))
                if delay == 0:
                    delay = "5"
            except Exception:
                delay = "5"
            try:
                file = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C9\\"+delay+".WAV"
            except OSError:
                file = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C9\\"+delay+".WAV"
            finally:
                self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\BMA.WAV"),
                                  after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path, source=file),
                                                          after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\MSMZ.WAV"),
                                                                                           after=lambda a: self.znelkaOut())))
        else:
            nastupiste = random.choice(("01", "02", "03"))
            kolaj = random.choice(os.listdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\K1"))
            self.vclient.play(discord.FFmpegPCMAudio(executable=path, source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\PRIDE.WAV"),
                              after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path, source=f"D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\N1\\{nastupiste}.WAV"),
                                            after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path, source=f"D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\K1\\{kolaj}"),
                                                          after=lambda a:self.znelkaOut())))

    def znelkaOut(self):
        mypath = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\ZNELKY"
        self.vclient.play(discord.FFmpegPCMAudio(executable=path, source=mypath + "\\END.WAV"))


def setup(client):
    client.add_cog(ZSSKCog(client))
