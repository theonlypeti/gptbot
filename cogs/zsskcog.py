import logging
from nextcord.ext import commands
import nextcord as discord
import os
import json
import requests
from bs4 import BeautifulSoup as html

path = "D:\\Users\\Peti.B\\Downloads\\ffmpeg-2020-12-01-git-ba6e2a2d05-full_build\\bin\\ffmpeg.exe"
root = os.getcwd()
maindir = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\R3"
os.chdir(maindir)

with open("vonatdb.json","r") as file:
    soundfiles= json.load(file)
os.chdir(root)

class TimeTable(object):
    def __init__(self,time,cities,meska,vlaktype):
        self.time = time
        self.cities = cities
        self.delay = meska
        self.vlaktype = vlaktype

class ZSSKCog(commands.Cog):
    def __init__(self,client,baselogger):
        self.client=client
        self.tt = None
        self.zsskLogger = baselogger.getChild("ZsskLogger")

    def getTimeTable(self,link):
        stranka = requests.get(link).content #TODO make into aiohttp
        soup = html(stranka, 'html.parser')
        a = soup.find_all(attrs={"title":"Zobraziť detail spoja"})[0] #TODO dont find all pls
        link=a.get("href")
        stranka = requests.get(link).content
        delay = soup.find("a",attrs={"class":"delay-bubble"})        
        if delay in (None,"meškania"):
            delay = None
        else:
            delay = delay.contents[0].split(" ")[2]
        soup = html(stranka, 'html.parser')
        a = soup.find_all("li",attrs={"class": "item"})
        b = soup.find_all("li",attrs={"class": "item inactive"})
        c = set(a).difference(set(b))
        a = [i for i in a if i in c]
        cities = [child.select("strong.name")[0].contents[0] for child in reversed(a)]
        time = soup.find("span",attrs={"class":"departure"}).contents[-1].strip()
        
        return TimeTable(time,cities,delay,None)

    @discord.slash_command(name="zssk",description="Call the announcer lady to tell you about a train´s schedule",dm_permission=False)
    async def zssk(self,ctx,
                   fromcity:str = discord.SlashOption(name="from",description="City",required=True),
                   tocity:str = discord.SlashOption(name="to",description="City",required=True),
                   time:str = discord.SlashOption(name="time",description="hh:mm",required=False),
                   date:str = discord.SlashOption(name="date",description="dd.mm.yyyy",required=False)):
        try:
            channel = ctx.user.voice.channel
            try:
                vclient = await channel.connect()
            except Exception:
                vclient = ctx.guild.voice_client
            self.vclient = vclient
            await ctx.send("Working on it...")
        except AttributeError:
        #if isinstance(channel,type(None)) or channel is None:
            await ctx.send(embed=discord.Embed(title="Command caller not in a voice channel."))
            return
        else:
            link = f"https://cp.hnonline.sk/vlakbus/spojenie/vysledky/?"+(f"date={date}&" if date else "") + (f"time={time}&" if time else "") +f"f={fromcity}&fc=1&t={tocity}&tc=1&af=true&trt=150,151,152,153"
            self.tt = self.getTimeTable(link)
            self.znelka()

##    @discord.slash_command(name="leave",description="Disconnect the bot from voice",guild_ids=[860527626100015154])
##    async def leave(self,ctx):
##        server = ctx.guild.voice_client
##        await server.disconnect(force=True)
            
    def znelka(self): #TODO make these relative paths
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\ZNELKY")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="startOld.WAV"),
                          after=lambda a: self.traintype())

    def traintype(self):
        os.chdir("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\V1")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="NFVOS.WAV"),
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
                chosencity = soundfiles[chosencity]
            except KeyError:
                self.zsskLogger.error(f"not found {chosencity}")
            except IOError:
                self.zsskLogger.error(f"no file found {chosencity}")
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

    def meskanie(self,tt):
        if tt.delay:
            delay = int(tt.delay)
            delay = round(delay//5)*5
            if delay == 0:
                delay = 5
            
            try:
                delay = str(round(delay // 10) * 10) or 5
                file = open("D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C9\\"+str(delay)+".WAV","r")
            except OSError:
                file = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\C9\\"+str(delay)+".WAV"
            finally:
                self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\BMA.WAV"),
                                  after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=file),
                                                          after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\MSMZ.WAV"),
                                                                                           after=lambda a:self.znelkaOut())))
        else:
            self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\SLOVA\\PRIDE.WAV"),
                              after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\N1\\01.WAV"),
                                            after=lambda a:self.vclient.play(discord.FFmpegPCMAudio(executable=path,source="D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\K1\\0101.WAV"),
                                                          after=lambda a:self.znelkaOut())))


    def znelkaOut(self):
        path = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK\\ZNELKY"
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=path + "\\END.WAV"))

def setup(client,baselogger):
    client.add_cog(ZSSKCog(client,baselogger))