from nextcord.ext import commands
import nextcord as discord
import os
from random import choice, choices
import inspect
import emoji

root = "F:\\Program Files\\Python39\\MyScripts\\discordocska\\pipik"
path = "D:\\Users\\Peti.B\\Downloads\\ffmpeg-2020-12-01-git-ba6e2a2d05-full_build\\bin\\ffmpeg.exe"
maindir = "D:\\Users\\Peti.B\\Music\\San Andreas Radio Constructor\\San Andreas Radio Constructor"

radio_icons_station = {"<:BounceFM:957469538599985223>":"Bounce FM","<:CSR1039:957469539518545960> ":"CSR 103.9","<:KDST:957469532816048159> ":"K-DST","<:KJAHWest:957469552168558732>":"K-Jah West","<:KRose:957469547760345109>":"K-Rose","<:MasterSounds:957469544681725972>":"Master Sounds 98.3","<:PlaybackFMLogo:957469525211766855>":"Playback FM","<:RadioLosSantos:957469549270294568>":"Radio Los Santos","<:RadioX:957469523387232256>":"Radio X","<:SFUR:957469545428299836>":"SF-UR"}
station_emojis = {v:k for k,v in radio_icons_station.items()}    


station_descs = {k.split(" - ")[0]:k.split(" - ")[1] for k in """Bounce FM - Funk, Disco
CSR 103.9 - New Jack Swing, Contemporary Soul
K-DST - Classic Rock
K-Jah West - Reggae, Dancehall
K-Rose - Classic Country
Master Sounds 98.3 - Rare Groove, Classic Funk
Playback FM - Classic East Coast Hip Hop
Radio Los Santos - West Coast Hip Hop, Gangsta Rap
Radio X - Funk, Disco
SF-UR - House""".split("\n")}

class RadioCog(commands.Cog):
    def __init__(self,client,baselogger):
        global radioLogger
        #self.radios = []
        self.client = client
        radioLogger = baselogger.getChild("radioLogger")
        self.stations = []
        
        for station in os.listdir(maindir)[2:-3]:
            self.stations.append(self.Station(station,emoji=station_emojis[station],desc=station_descs[station])) #TODO dont do this, initialize them only when called by join
        self.ads = os.listdir(maindir+"\\!Commercials")

    class Station(object):
        def __init__(self, folder, emoji="", desc=""):
            self.name = folder
            self.emoji = emoji
            self.desc = desc
            self.djchatter = []
            self.songs = []
            self.call = []
            self.story = []
            self.stationAnnounce = []
            songlist = []

            files = os.listdir(maindir+"\\"+self.name)
            for file in files:
                if file.startswith("(DJ)") or file.startswith("(Atmosphere)"):
                    self.djchatter.append(file)
                elif file.startswith("(Caller)"):
                    self.call.append(file)
                elif file.startswith("(Story)"):
                    self.story.append(file)
                elif file.startswith("(ID)"):
                    self.stationAnnounce.append(file)
                elif file.startswith("(Bridge"):
                    pass
                else:
                    songlist.append(file)

            self.songs = []
            self.songs.append([songlist[0], [songlist[0]], [], []])
            for song in songlist:
                until = self.songs[-1][0].find("(")
                #print(until)
                if song.startswith(self.songs[-1][0][:until]):
                    if "(Intro" in song:
                        self.songs[-1][1].append(song)
                    elif "(Outro" in song:
                        self.songs[-1][3].append(song)
                    else:
                        self.songs[-1][2].append(song)
                else:
                    del(self.songs[-1][0])
                    self.songs.append([song,[song],[],[]])
            del(self.songs[-1][0])

    class StationDropdown(discord.ui.Select):
        def __init__(self,voice,cog):
            self.cog = cog
            self.voice = voice
            options = [discord.SelectOption(label=station.name,description=station.desc,emoji=station.emoji,value=station.emoji) for station in self.cog.stations]
            super().__init__(options=options)

        async def callback(self,inter):
            station = self.values[0]
            embedVar = discord.Embed(title="You are now listening to",description=radio_icons_station[station])
            viewObj = discord.ui.View(timeout=None)
            viewObj.add_item(self.DisconnectButton())

            emoji = self.cog.client.get_emoji(station.split(":")[2][:-4]) #try without an api call
            if not emoji: #intentless fallback
                radioLogger.info(station)
                try:
                    emoji = await self.cog.client.get_guild(957469186798518282).fetch_emoji(station.split(":")[2][:-2])
                except discord.errors.NotFound:  
                #if not emoji: #local file fallback
                    icondir ="F:/Program Files/Python39/MyScripts/discordocska/zene/radio icons/"
                    file = discord.File(icondir+station.split(":")[1]+".png",filename="image.png")
                    embedVar.set_thumbnail(url="attachment://image.png")
                    await inter.response.edit_message(file=file,embed=embedVar,view=viewObj)
                else:
                    embedVar.set_thumbnail(url=emoji.url)
                    await inter.response.edit_message(embed=embedVar,view=viewObj)
            else:
                embedVar.set_thumbnail(url=emoji.url)
                await inter.response.edit_message(embed=embedVar,view=viewObj)
            
            try:
                vclient = await self.voice.connect()
            except Exception:
                vclient = inter.guild.voice_client
            newRadio = Radio(vclient,radio_icons_station[station],self.cog)
            newRadio.announceStation()

        class DisconnectButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Disconnect",emoji=emoji.emojize(':waving_hand:'),style=discord.ButtonStyle.danger)

            async def callback(self,ctx):
                server = ctx.guild.voice_client
                await server.disconnect(force=True)
                self.disabled = True
                await ctx.response.edit_message(view=self.view)

    @discord.slash_command(name="radio", description="Hop in a voice channel and tune into a radio from the 90's from the videogame GTA San Andreas.", dm_permission=False)
    async def radio(self, ctx: discord.Interaction):
        try:
            vchannel = ctx.user.voice.channel
        except AttributeError:
        #if isinstance(channel,type(None)) or channel is None:
            await ctx.send(embed=discord.Embed(title="Command caller not in a voice channel.", color=discord.Colour.red()))
            return
        viewObj = discord.ui.View()
        viewObj.add_item(self.StationDropdown(vchannel, self))
        await ctx.send(embed=discord.Embed(title="Choose a station"), view=viewObj)

    @discord.slash_command(name="leave", description="Kicks the bot if playing in a voice channel.")
    async def leave(self, ctx: discord.Interaction):
        server = ctx.guild.voice_client
        await server.disconnect(force=True)
        os.chdir(root)
        await ctx.send("Left voice channel.", delete_after=2.0)
        #radiocog.radios.remove(self)

class Radio(object):
    def __init__(self, vclient, station, cog):
        self.cog = cog
        self.played = []
        self.vclient = vclient
        self.station = self.getStation(station)
        self.adChance = 15 #Random advertisement chance between songs
        self.DJTalkChance = 30 #DJ nonsense chatter chance btwn songs
        self.storyChance= 10 #DJ telling a short story chance
        self.callChance = 10 #DJ getting a phonecall chance
        self.announceChance = 30 #Station name/catchphrase announce chance
        # ^ - Above values are in percents%, they dont have to add up to 100%
        self.noRepeats = 6 #noRepeats #How many songs to play until they can be repeated
        self.noneChance = max(0,100-(self.DJTalkChance+self.callChance+self.adChance+self.storyChance+self.announceChance))
        self.chancelist = (self.DJTalkChance/100,self.callChance/100,self.adChance/100,self.storyChance/100,self.announceChance/100,self.noneChance/100)
        radioLogger.info("radio initialised i guess")

    def getStation(self,stationName):
        for station in self.cog.stations:
            if station.name == stationName:
                return station
        
    def playSong(self):
        song = choice(self.station.songs)
        radioLogger.debug(song)
        if song not in self.played:
            self.played.append(song)
            if len(self.played) > self.noRepeats:
                del self.played[0]
            self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=choice(song[0])),
                     after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=song[1][0]),
                                                  after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=choice(song[2])),
                                                                                    after=lambda a: self.playerloop())))
            radioLogger.debug(f"{len(inspect.stack(0))} inspect stack")
            
            print("♪ Now playing -",song[1][0][:-9],"♪")
            return 
        else:
            radioLogger.warning("retrying")
            self.playSong()

    def djtalk(self):
        radioLogger.debug("talk")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=choice(self.station.djchatter)),
                          after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\silence.ogg"),
                                                  after=lambda a: self.playSong()))
        radioLogger.debug("talk end")

    def djcall(self):
        radioLogger.debug("call")
        if len(self.station.call) < 1:
            self.playSong()
        else:
            self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=choice(self.station.call)),
                              after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\silence.ogg"),
                                                                after=lambda a: self.playSong()))
        radioLogger.debug("call end")

    def djstory(self):
        radioLogger.debug("story")
        if len(self.station.stationAnnounce) < 1:
            radioLogger.debug("nvm talk")
            self.djtalk()
            radioLogger.debug("nvmtalk over")
        else:
            self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=choice(self.station.story)),
                              after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\silence.ogg"),
                                                      after=lambda a: self.playSong()))
            radioLogger.debug("story end")

    def announceStation(self):
        radioLogger.debug("gonna announce")
        if len(self.station.stationAnnounce) < 1:
            radioLogger.debug("nvm talk")
            self.djtalk()
            radioLogger.debug("nvmtalk over")
        else:
            self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=choice(self.station.stationAnnounce)),
                              after=lambda a: self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\silence.ogg"),
                                                                after=lambda a: self.playSong()))
        radioLogger.debug("announced")
        
    def doNothing(self):
        radioLogger.debug("nothing")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\silence.ogg"),
                                                  after=lambda a: self.playSong())
        radioLogger.debug("nothing end")

    def adbreak(self):
        radioLogger.debug("ad")
        self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\!Commercials\\"+choice(self.cog.ads)),
                          after=self.vclient.play(discord.FFmpegPCMAudio(executable=path,source=maindir+"\\silence.ogg"),
                                                  after=lambda a: self.playSong()))

    def playerloop(self):
        radioLogger.debug("were back in the playerloop")
        os.chdir(maindir+"\\"+self.station.name)
        a = (choices(("self.djtalk()","self.djcall()","self.adbreak()","self.djstory()","self.announceStation()","self.doNothing()"),weights=self.chancelist)[0])
        radioLogger.debug(f"{a} choice")
        eval(a)

def setup(client,baselogger):
    client.add_cog(RadioCog(client,baselogger))
