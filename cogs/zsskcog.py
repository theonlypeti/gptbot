import random
import aiohttp
from nextcord.ext import commands
import nextcord as discord
import os
import json
from bs4 import BeautifulSoup as html

path = "D:\\Users\\Peti.B\\Downloads\\ffmpeg-2020-12-01-git-ba6e2a2d05-full_build\\bin\\ffmpeg.exe"
root = os.getcwd()
maindir = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\R3"
os.chdir(maindir)

with open("vonatdb.json", "r") as file:
    soundfiles = json.load(file)
os.chdir(root)

class TimeTable(object):
    def __init__(self, time, cities, meska, vlaktype):
        self.time = time
        self.cities = cities
        self.delay = meska
        self.vlaktype = vlaktype

class ZSSKCog(commands.Cog):
    def __init__(self, client, baselogger):
        self.client = client
        self.tt = None
        self.zsskLogger = baselogger.getChild("ZsskLogger")

    async def getTimeTable(self, link): #dont judge pls
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as req:
                stranka = await req.content.read()
            soup = html(stranka, 'html.parser')
            try:
                a = soup.find("a", attrs={"title": "Zobraziť detail spoja"})
            except Exception as e:
                self.zsskLogger.error(e)
                return None
            link = a.get("href")
            async with session.get(link) as req:
                stranka = await req.content.read()
        delay = soup.find("a", attrs={"class": "delay-bubble"})
        if delay in (None, "meškania"):
            delay = None
        else:
            delay = delay.contents[0].split(" ")[2]
        soup = html(stranka, 'html.parser')
        a = soup.find_all("li", attrs={"class": "item"})
        b = soup.find_all("li", attrs={"class": "item inactive"})
        c = set(a).difference(set(b))
        a = [i for i in a if i in c]
        cities = [child.select("strong.name")[0].contents[0] for child in reversed(a)]
        time = soup.find("span",attrs={"class": "departure"}).contents[-1].strip()
        
        return TimeTable(time, cities, delay, None)

    @discord.slash_command(name="zssk", description="Call the announcer lady to tell you about a train´s schedule", dm_permission=False)
    async def zssk(self, ctx: discord.Interaction,
                   fromcity: str = discord.SlashOption(name="from", description="City", required=True),
                   tocity: str = discord.SlashOption(name="to", description="City", required=True),
                   time: str = discord.SlashOption(name="time", description="hh:mm", required=False),
                   date: str = discord.SlashOption(name="date", description="dd.mm.yyyy", required=False)):
        await ctx.response.defer()
        try:
            channel = ctx.user.voice.channel
            try:
                vclient = await channel.connect()
            except Exception as e:
                self.zsskLogger.info(f"{e}")
                vclient = ctx.guild.voice_client
            self.vclient = vclient
            await ctx.send("Working on it...", delete_after=10)
        except AttributeError:
        #if isinstance(channel,type(None)) or channel is None:
            await ctx.send(embed=discord.Embed(title="Command caller not in a voice channel."))
            return
        else:
            link = f"https://cp.hnonline.sk/vlakbus/spojenie/vysledky/?"+(f"date={date}&" if date else "") + (f"time={time}&" if time else "") +f"f={fromcity}&fc=1&t={tocity}&tc=1&af=true&trt=150,151,152,153"
            self.tt = await self.getTimeTable(link)
            if self.tt is None:
                await ctx.send("Not found.", delete_after=5)
            self.znelka()

    @zssk.on_autocomplete("tocity")
    async def stanica_autocomplete(self,interaction, city: str):
        if city:
            get_near_city = [i for i in soundfiles.keys() if i.casefold().startswith(city.casefold())]
            get_near_city = get_near_city[:25]
            await interaction.response.send_autocomplete(get_near_city)

    @zssk.on_autocomplete("fromcity") #not sure if i can use one func for both autocomplete decorators so i just split them
    async def stanica_autocomplete2(self,interaction, city: str):
        if city:
            get_near_city = [i for i in soundfiles.keys() if i.casefold().startswith(city.casefold())]
            get_near_city = get_near_city[:25]
            await interaction.response.send_autocomplete(get_near_city)
            
    def znelka(self): #TODO make these relative paths
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\ZNELKY")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="startOld.WAV"),
                          after=lambda a: self.traintype())

    def traintype(self):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\V1")
        sound = random.choice(os.listdir())
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=sound), #NFVOS
                          after=lambda a: self.smerom())

    def smerom(self):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="SM2.WAV"),
                          after=lambda a: self.city(self.tt.cities))

    def city(self,cities):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\R3")
        if len(cities) > 0:
            chosencity = cities.pop()
            try:
                self.zsskLogger.debug(f"{chosencity}")
                chosencity = soundfiles[chosencity]
            except KeyError:
                self.zsskLogger.error(f"not found {chosencity}")
                self.city(cities)
            except IOError:
                self.zsskLogger.error(f"no file found {chosencity}")
                self.city(cities)
            else:
                self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=chosencity+".WAV"),
                          after=lambda a: self.city(cities))
        else:
            self.prichod(self.tt)
            
    def prichod(self,tt):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="PRPR.WAV"),
                          after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C1\\"+tt.time.split(":")[0]+".WAV"),
                                                  after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C3\\"+str(int(tt.time.split(":")[1]))+".WAV"),
                                                                                            after=lambda a: self.meskanie(tt))))

    def meskanie(self, tt):
        if tt.delay:
            try:
                delay = int(tt.delay)
                delay = round(delay//5)*5
                if delay == 0:
                    delay = 5
            except Exception:
                delay = 5
            try:
                delay = str((round(delay // 10) * 10) or 5)
                file = open("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C9\\"+str(delay)+".WAV","r")
            except OSError:
                file = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C9\\"+str(delay)+".WAV"
            finally:
                self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\BMA.WAV"),
                                  after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=file),
                                                          after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\MSMZ.WAV"),
                                                                                           after=lambda a:self.znelkaOut())))
        else:
            nastupiste = random.choice(("01","02","03"))
            kolaj = random.choice(os.listdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\K1"))
            self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\PRIDE.WAV"),
                              after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=f"D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\N1\\{nastupiste}.WAV"),
                                            after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=f"D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\K1\\{kolaj}"),
                                                          after=lambda a:self.znelkaOut())))


    def znelkaOut(self):
        mypath = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\ZNELKY"
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=mypath + "\\END.WAV"))

def setup(client,baselogger):
    client.add_cog(ZSSKCog(client,baselogger))
