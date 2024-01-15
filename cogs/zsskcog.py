import random
import aiohttp
from math import ceil
from nextcord.ext import commands
import nextcord as discord
import os
import json
from bs4 import BeautifulSoup as html
from utils import embedutil
from utils.antimakkcen import antimakkcen

path = "D:\\Users\\Peti.B\\Downloads\\ffmpeg-2020-12-01-git-ba6e2a2d05-full_build\\bin\\ffmpeg.exe" #TODO now this is bad
maindir = "D:\\Users\\Peti.B\\Documents\\ZSSK\\iniss_orig\\rawbank\\SK"
# TODO parse the stranka when inputting stuff and add another param called current stanica so and i can autocomplete the stanica between from and to and then i can say ktory pokracuje smer

with open(r"data\vonatdb.json", "r") as file:
    soundfiles = json.load(file)

#//    "Ko\u0161ice\" //ko\u0161ice": "5614616", taken out, that sound file does not even exist


class TimeTable(object):
    def __init__(self, time: str, date: str, cities: list[str], meska: str, vlaktype: str | None):
        self.time: str = time
        self.date: str = date #TODO this is not used and make these datetime
        self.cities: list[str] = cities
        self.delay: str = meska
        self.vlaktype: str | None = vlaktype

    def __repr__(self):
        return f"{self.__class__}({self.time}, {self.cities}, {self.delay}, {self.vlaktype})"


def custom_round(num: int) -> str:
    if num <= 60:
        return str(ceil(num / 5) * 5)
    elif num <= 180:
        return str(round(num, -1))
    elif num <= 300:
        return str(ceil(num / 20) * 20)
    elif num <= 480:
        return str(ceil(num / 30) * 30)
    else:
        return "VICE480"


class ZSSKCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.zsskLogger = client.logger.getChild(f"{__name__}Logger")

    async def getTimeTable(self, link): #dont judge pls
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as req:
                stranka = await req.content.read()
            soup = html(stranka, 'html.parser')
            try:
                timeelem = soup.find("h2", attrs={"class": "reset date"}) or soup.find("h2", attrs={"class": "reset date color-red"}) or soup.find("h2")
                date = timeelem.find("span").text
                time = timeelem.text.removesuffix(date)
                spoj = soup.find("div", attrs={"class": "connection-details"})
                a = spoj.find_all("a", attrs={"title": "Zobraziť detail spoja"})
                traintype = spoj.find("img").get("alt")
                self.zsskLogger.debug(a)
            except Exception as e:
                self.zsskLogger.error(e)
                return None
            try:
                links = []
                for vlak in a:
                    links.append(vlak.get("href"))
                # links = a.get("href") #ez szokott errorozni mert nonetype az a
            except AttributeError as e:
                self.zsskLogger.error(e)
                return None

            tts = []
            for link in links:
                async with session.get(link) as req:
                    stranka = await req.content.read()

                delay = soup.find("a", attrs={"class": "delay-bubble"})
                if delay and delay.contents[0].text.startswith("Aktuálne"):
                    dly = delay.contents[0].text.split(" ")[2].strip()
                    if dly == "meškania":
                        delay = 0
                    else:
                        delay = dly
                else:
                    delay = 0
                soup = html(stranka, 'html.parser')
                a = soup.find_all("li", attrs={"class": "item"})
                b = soup.find_all("li", attrs={"class": "item inactive"})
                c = set(a).difference(set(b))
                a = [i for i in a if i in c]  # do not touch lol
                cities = [child.select("strong.name")[0].contents[0] for child in reversed(a)]
                # time = soup.find("span", attrs={"class": "departure"}).contents[-1].text.strip() # LOL THATS WRONG

                tt = TimeTable(time, date, cities, delay, traintype or None)
                tts.append(tt)
        self.zsskLogger.info(f"{tts=}")
        return tts

    @discord.slash_command(name="zssk", description="Call the announcer lady to tell you about a train´s schedule", dm_permission=False)
    async def zssk(self, ctx: discord.Interaction,
                   fromcity: str = discord.SlashOption(name="from", description="City", required=True),
                   tocity: str = discord.SlashOption(name="to", description="City", required=True),
                   time: str = discord.SlashOption(name="time", description="hh:mm", required=False),
                   date: str = discord.SlashOption(name="date", description="dd.mm.yyyy", required=False)):
        await ctx.response.defer()
        self.zsskLogger.info(f"{ctx.user} used zssk in {ctx.channel}: {fromcity} {tocity}")

        link = f"https://cp.hnonline.sk/vlakbus/spojenie/vysledky/?"+(f"date={date}&" if date else "") + (f"time={time}&" if time else "") +f"f={fromcity}&fc=100003&t={tocity}&tc=100003&af=true&&trt=150,151,152,153" #direct=true
        self.zsskLogger.debug(f"{link=},{len(link)=}")
        tts: list[TimeTable] = await self.getTimeTable(link)
        if tts is None:
            await embedutil.error(ctx, f"Žiadne spoje medzi {fromcity} a {tocity}.")
        else:
            for tt in tts:
                embedVar = discord.Embed(title=f"{fromcity.replace('%20', ' ')} >> {tocity.replace('%20', ' ')}", description=f"Departure at {tt.time}, {tt.delay} min delay\n")
                [embedVar.add_field(name=i, value="\u200b", inline=False) for i in reversed(tt.cities)]
                await ctx.send(embed=embedVar)

        try:
            channel = ctx.user.voice.channel
            try:
                vclient: discord.VoiceClient = await channel.connect()
            except Exception as e:
                self.zsskLogger.error(f"{e}")
                vclient: discord.VoiceClient = ctx.guild.voice_client  # TODO if its lavalink player this will error out
                if vclient is None:
                    await embedutil.error(ctx, "Could not connect to voice channel. Maybe I don´t have permissions to join it.")
                    return

        except AttributeError:
            # if isinstance(channel,type(None)) or channel is None:
            await embedutil.error(ctx, "Command caller not in voice channel. Announcement not played.")
            # return
        else:
            self.znelka(vclient, tts[0])

    @zssk.on_autocomplete("fromcity")
    @zssk.on_autocomplete("tocity")
    async def stanica_autocomplete(self, interaction: discord.Interaction, city: str):
        if city:
            get_near_city = {i: i.replace(" ", "%20") for i in soundfiles.keys() if antimakkcen(i.casefold()).startswith(antimakkcen(city.casefold()))}
            get_near_city = dict(list(get_near_city.items())[:25])
            await interaction.response.send_autocomplete(get_near_city)

    # #not sure if i can use one func for both autocomplete decorators so i just split them
    # async def stanica_autocomplete2(self,interaction, city: str):
    #     if city:
    #         get_near_city = [i for i in soundfiles.keys() if i.casefold().startswith(city.casefold())]
    #         get_near_city = get_near_city[:25]
    #         await interaction.response.send_autocomplete(get_near_city)
            
    def znelka(self, vclient: discord.VoiceClient, tt: TimeTable):
        vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\ZNELKY\\startOld.WAV"),
                          after=lambda a: self.traintype(vclient, tt))

    def traintype(self, vclient: discord.VoiceClient, tt: TimeTable):
        basesound = {"normal":"NFV","medzistatny":"NFM","medzistatny povinne miestenkovy":"NRM","povinne miestenkovy":"NRV","zmeskany medzistatny":"ZFM","zmeskany medzistatny povinne miestenkovy":"ZRM","zmeskany povinne miestenkovy":"ZRV"}
        types = {"osobný vlak":"OS","rýchlik":"R","RegioJet":"REX","EuroCity":"EC","InterCity":"IC","EuroNight":"ER","EuroRegional":"ER","RegionalExpress":"REX","Expres":"EX"}
        self.zsskLogger.debug(f"\\{basesound['normal']}{types[tt.vlaktype]}.WAV")
        self.zsskLogger.debug(os.path.exists(maindir + f"\\V1\\{basesound['normal']}{types[tt.vlaktype]}.WAV"))
        if os.path.exists(maindir + f"\\V1\\{basesound['normal']}{types[tt.vlaktype]}.WAV"):
            sound = f"{basesound['normal']}{types[tt.vlaktype]}.WAV"
        else:
            sound = random.choice(os.listdir(maindir + "\\V1"))
        vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\V1\\" + sound), #NFVOS
                          after=lambda a: self.smerom(vclient, tt))

    def smerom(self, vclient, tt: TimeTable):
        vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\SLOVA\\SM2.WAV"),
                          after=lambda a: self.city(vclient, tt))

    def city(self, vclient, tt: TimeTable):
        cities = tt.cities
        if len(cities) > 0:
            chosencity = cities.pop()
            try:
                self.zsskLogger.debug(f"{chosencity=}")
                chosencity = soundfiles[chosencity]
            except KeyError:
                self.zsskLogger.error(f"not found {chosencity}")
                self.city(vclient, tt)
            except IOError:
                self.zsskLogger.error(f"no file found {chosencity}")
                self.city(vclient, tt)
            else:
                vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\R3\\" + chosencity+".WAV"),
                          after=lambda a: self.city(vclient, tt))
        else:
            self.prichod(vclient, tt)
            
    def prichod(self, vclient, tt):
        vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\SLOVA\\PRPR.WAV"),
                          after=lambda a: vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\C1\\"+tt.time.split(":")[0]+".WAV"),
                                                  after=lambda a: vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\C3\\"+str(int(tt.time.split(":")[1]))+".WAV"),
                                                                                            after=lambda a: self.meskanie(vclient, tt))))

    def meskanie(self, vclient, tt):
        if tt.delay:
            try:
                delay = custom_round(int(tt.delay))
                if delay == 0: #this should not be possible lol
                    delay = "5"
            except Exception:
                delay = "5"
            try:
                file = maindir + "\\C9\\"+delay+".WAV"
            except OSError:
                file = maindir + "\\C9\\"+delay+".WAV"
            finally:
                vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\SLOVA\\BMA.WAV"),
                                  after=lambda a:vclient.play(discord.FFmpegPCMAudio(executable=path, source=file),
                                                          after=lambda a: vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\SLOVA\\MSMZ.WAV"),
                                                                                           after=lambda a: self.znelkaOut(vclient))))
        else:
            nastupiste = random.choice(("01", "02", "03"))
            kolaj = random.choice(os.listdir(maindir + "\\K1"))
            vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\SLOVA\\PRIDE.WAV"),
                              after=lambda a: vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + f"\\N1\\{nastupiste}.WAV"),
                                            after=lambda a:vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + f"\\K1\\{kolaj}"),
                                                          after=lambda a: self.znelkaOut(vclient))))

    def znelkaOut(self, vclient: discord.VoiceClient):
        sound = random.choice(os.listdir(maindir + "\\DODATKY"))
        vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\DODATKY\\" + sound), after=lambda a:
            vclient.play(discord.FFmpegPCMAudio(executable=path, source=maindir + "\\ZNELKY\\END.WAV")))


def setup(client):
    client.add_cog(ZSSKCog(client))
