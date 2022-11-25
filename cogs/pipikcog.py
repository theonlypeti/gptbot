import asyncio
import json
import os
import random
from copy import deepcopy
from typing import Dict, Union
import emoji
import nextcord as discord
import pyowm
from nextcord.ext import commands
from datetime import datetime, timedelta, date
from astral import moon
import pytz
from utils.antimakkcen import antimakkcen
from utils.mentionCommand import mentionCommand
from utils.mapvalues import mapvalues

mgr = pyowm.OWM(os.getenv("OWM_TOKEN")).weather_manager()
location = 'Bratislava,sk'

root = os.getcwd()  # "F:\\Program Files\\Python39\\MyScripts\\discordocska\\pipik"

good_emojis = (':smiling_face_with_hearts:', ':smiling_face_with_heart-eyes:', ':face_blowing_a_kiss:', ':kissing_face:', ':kissing_face_with_closed_eyes:')
bad_emojis = (':rolling_on_the_floor_laughing:', ':cross_mark:', ':squinting_face_with_tongue:', ':thumbs_down:')
good_words = {"affectionate", "admirable", "charm", "creative", "friend", "funny", "generous", "kind", "likable", "loyal", "polite", "sincere", "pretty", "please", "love", "goodnight", "nite", "prett", "kind", "sugar", "clever", "beaut", "star", "heart", "my", "wonderful", "legend", "neat", "good", "great", "amazing", "marvelous", "fabulous", "hot", "best", "birthday", "bday", "ador", "cute", " king", "queen", "master","daddy", "lil", "zlat", "bby", "angel", "god", "cool", "nice", "lil", "marvelous", "magnificent","lovely", "cutie","handsome","sweet"}
bad_words = {"adopt", "dirt", "die", "kill", "cring", "selfish", "ugly", "dick", "small", "devil", "drb", "ass", "autis", "deranged", "idiot", "cock", "cut ","cutt", "d1e", "fuck", "slut", "d13", "fake", "a55", "retard", "r3tard", "tard", "bitch", "nigga", "nibba", "nazi", "jew", "fag", "f4g", "feg", "feck", "pussy", "pvssy","stink", "smell", "stupid","cunt"}
pills = [{"name": "\U0001F48A Size Up Forte", "effect": 5, "effectDur": timedelta(minutes=5), #TODO make custom emojis
          "badEffectDur": timedelta(seconds=0)},
         {"name": "\U0001F608 Calvin Extra", "effect": 10, "effectDur": timedelta(minutes=20), #TODO make into class
          "badEffectDur": timedelta(minutes=20)},
         {"name": "\U0001F535 Niagara XXL", "effect": 15, "effectDur": timedelta(minutes=60),
          "badEffectDur": timedelta(hours=2, minutes=30)}]

good_responses = ("Oh youuu <3",
                  "Oh boy i think i got a stiffy already!",
                  "Casanovaaaa",
                  "Quit iiit not in front of everyone!",
                  "You know how to fire up my circuits!",
                  "You know i´ll happily measure it for you anytime!",
                  "You know how to flirt with a bot!",
                  "I´m blushing!",
                  "Omg marry me",
                  "Anytime bb!",
                  "Of course, honeybun!",
                  "Slow dooown bby!",
                  "Right away, sugarplum!",
                  "How are you hiding THAT?!")
bad_responses = ("Sorry, i´m not very impressed.",
                 "Nah, don´t like it.",
                 "Don´t embarrass yourself.",
                 "Cringe.",
                 "Are we in elementary again?",
                 "Go try it on someone else.",
                 "Really?",
                 "I wouldn't touch it with a ten foot pole.",
                 "Is this what you call a compliment?",
                 "You kiss your mother with that mouth?",
                 "You need to wash your mouth with soap!",
                 "You must be crazy.",
                 "I´m not falling for that!",
                 "I would be embarrassed.",
                 "If i were you, I would rather shut my mouth.",
                 "Don´t overestimate yourself.",
                 "Oof",
                 "Maybe next time.",
                 "Sooooo funny.",
                 "Ah well.",
                 "Too long, didn't read xd",
                 "ratio.")
duplicate_responses = ("I've heard this one before!",
                       "Boooooriiiiing!",
                       "You can do better than that!",
                       "Come on, be a little more original!",
                       "Chivalry is dead ugh.",
                       "Can't you come up with something better?",
                       "Do you really need a wingman for this?",
                       "Jeez that's embarrassing.",
                       "Wanna try again?",
                       "How original...")


default_achievements = (
("morning", emoji.emojize(':sunrise_over_mountains:'), "Morning wood", "Measure your pp in the morning"),
("one_pump", emoji.emojize(':raised_fist:'), "One pump champ", "Relapse after just one pump"),
("micropp", emoji.emojize(':pinching_hand:'), "MicroPP", "Get a measurement of <0.5cm"),
("megapp", emoji.emojize(":hugging_face:", language="alias", variant="emoji_type"), "MegaPP", "Get a measurement of >300cm"),
("nice", emoji.emojize(':Cancer:'), "Nice", "Get a measurement of 69cm"),
("flirty", emoji.emojize(':kissing_face:'), "Flirty", "Flirt your way into the bot´s heart with many compliments"),
("playa", emoji.emojize(':broken_heart:'), "Playa", "Break the bot´s heart with insults"),
("helping_hands", emoji.emojize(':handshake:'), "Helping hands", "Get help from someone holding your pp"),
("friend_need", emoji.emojize(':raising_hands:'), "A friend in need", "Help out someone by holding their pp"),
("pill_popper", emoji.emojize(':pill:'), "Pill popper", "Use a pp enlargement pill"),
("breaking_bad", emoji.emojize(":scientist:"), "Breaking bad", "Mix pills together to get a stronger pill"),
("lucky_draw", emoji.emojize(':slot_machine:'), "Lucky draw", "Get a viagra from daily pills"),
("dedicated", emoji.emojize(':partying_face:'), "Dedicated fan!", "Come back each day for a daily for over a month"),
("tested", emoji.emojize(':mouse:'), "Tried and tested", "Try out all possible pp enlargement methods"),
("desperate", emoji.emojize(':weary_face:'), "I´m desperate", "Have all possible pp enlargement methods active at the same time!"),
("contributor", emoji.emojize(':star:'), "Contributor", "Aid development with ideas, offering help with gramatical errors, translations or reporting bugs and errors"))

class Achievement(object):
    """achievement object
icon = emoji
achiid = shorthand id string to save
name = displayname in profile
desc = description in DMs
"""
    def __init__(self, achi):
        self.achiid: str
        self.name: str
        self.icon: str
        self.desc: str
        if type(achi) == tuple:
            for k, v in zip(("achiid", "icon", "name", "desc"), achi):
                setattr(self, k, v)

    def __str__(self):
        return f"{emoji.emojize(self.icon, language='alias')} {self.name}"


class PipikUser(object):
    def __init__(self, discorduser):
        if type(discorduser) == dict:
            for k, v in discorduser.items():
                if k != "xp":
                    setattr(self, k, v)
            return
        if type(discorduser) != int:
            discorduser = discorduser.id
        self.id = discorduser
        self.fap: int = 0
        self.achi = []
        self.items = []
        self.pb: int = 0
        self.pw: int = 0
        self.cd = None
        self.methods: int = 0
        self.pill = None
        self.pillPopTime = datetime.now() # placeholder
        self.dailyStreak: int = 0
        self.dailyDate = datetime.now() - timedelta(days=1)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, PipikUser):
            return self.id == other.id
        else:
            raise NotImplemented(f"Comparison between {type(self)} and {type(other)}")

    def __str__(self):
        return f"[{self.id} with {len(self.achi)} achis; {str(self.dailyStreak)} streak; {self.pb} pb {self.cd} cd and {self.methods} methods]"

    def __repr__(self):
        return f"[{self.id} with {len(self.achi)} achis; {str(self.dailyStreak)} streak; {self.pb} pb {self.cd} cd and {self.methods} methods]"

    async def takePill(self, which, cog):
        self.pill = self.items[which][0]
        self.pillPopTime = datetime.now()
        self.items[which][1] -= 1
        if self.items[which][1] == 0:
            del (self.items[which])
        cog.saveFile()

class PipikBot(commands.Cog):
    def __init__(self, client, baselogger):
        self.pipikLogger = baselogger.getChild("PipikBot")
        self.usedcompliments = {"placeholder", }
        self.client = client
        self.temperature = 0
        self.holding: Dict[int, discord.Member] = dict()
        self.weatherUpdatedTime = datetime.now()
        self.leaderboards = {}
        self.loserboards = {}
        self.sunrise_date = datetime.now()  # just a placeholder, it gets actually rewritten
        self.users = []
        self.achievements = {i[0]: Achievement(i) for i in default_achievements}
        
        try:
            self.readSettings()
        except:
            self.getTemp()
        os.makedirs(root + r"/data", exist_ok=True)
        with open(root + "/data/pipikv3top.txt", "r") as file:
            self.leaderboards = json.load(file)
        with open(root + "/data/pipikv3low.txt", "r") as file:
            self.loserboards = json.load(file)

        with open(root + "/data/pipikusersv3.txt", "r", encoding="utf-8") as file:
            users = json.load(file)
            for user in users:
                if user["cd"] not in (0, None, "none", "None"):
                    user["cd"] = datetime.fromisoformat(user["cd"])
                if user["pillPopTime"] not in (0, None, "none", "None"):
                    user["pillPopTime"] = datetime.fromisoformat(user["pillPopTime"])
                try:
                    user["dailyDate"] = datetime.fromisoformat(user["dailyDate"])
                except:
                    pass
                newUser = PipikUser(user)
                if newUser not in self.users:
                    self.users.append(newUser)
                else: #TODO: depreacate, should not happen
                    self.pipikLogger.debug(f"found and ignored duplicate entry with id: {newUser.id}")
            # self.pipikLogger.debug(f"{self.users} all-users")
            self.pipikLogger.debug(f"{len(self.users)} all users loaded")

    async def updateUserAchi(self, ctx: discord.Interaction, user: discord.Member, achi: str):
        achi: Achievement = self.achievements[achi]
        await ctx.channel.send(embed=discord.Embed(title=f"{user.display_name} just got the achievement:", description=str(achi), color=discord.Colour.gold()))
        user = self.getUserFromDC(user)
        user.achi.append(achi.achiid)
        self.saveFile() #any action that warrants an achievement already saves the users #not true lol, in pp func theres bunch of occasions where it doesnt save

    def updateLeaderBoard(self, ldb, dcid, value):
        try:
            self.leaderboards[str(ldb)]
        except KeyError:
            self.leaderboards[str(ldb)] = [] #i knew what i was doing, dont try to reinvent the wheel
        self.leaderboards[ldb].append((dcid, value))
        self.leaderboards[ldb].sort(key=lambda a: a[1], reverse=True)
        self.leaderboards[ldb] = self.leaderboards[ldb][:5]
        with open(root+"/data/pipikv3top.txt", "w") as file:
            json.dump(self.leaderboards, file, indent=4)

    def updateLoserBoard(self, ldb, dcid, value):
        try:
            self.loserboards[str(ldb)]
        except KeyError:
            self.loserboards[str(ldb)] = []
        self.loserboards[ldb].append((dcid, value))
        self.loserboards[ldb].sort(key=lambda a: a[1], reverse=False)
        self.loserboards[ldb] = self.loserboards[ldb][:5]
        with open(root+"/data/pipikv3low.txt", "w") as file:
            json.dump(self.loserboards, file, indent=4)

    def saveFile(self):
        tempusers = []
        for user in self.users:
            tempuser = deepcopy(user)
            if user.cd not in (0, "None", "none", None):
                tempuser.cd = user.cd.isoformat()
            if user.pillPopTime not in (0, "None", "none", None):
                tempuser.pillPopTime = user.pillPopTime.isoformat()
            try:
                tempuser.dailyDate = user.dailyDate.isoformat()
            except Exception as e:
                self.pipikLogger.error(e)
            tempusers.append(tempuser.__dict__)
        with open(root+"/data/pipikusersv3.txt", "w") as file:
            json.dump(tempusers, file, indent=4)
        self.pipikLogger.info("saved users")

    def saveSettings(self):
        settings = {"temperature": self.temperature, "weatherUpdTime": self.weatherUpdatedTime.isoformat(), "sunrise": self.sunrise_date.isoformat()}
        with open(root+"/data/pipisettings.txt", "w") as file:
            json.dump(settings, file)
        self.pipikLogger.debug("saved settings")

    def readSettings(self):
        with open(root+"/data/pipisettings.txt", "r") as file:
            settings = json.load(file)
        self.weatherUpdatedTime = datetime.fromisoformat(settings["weatherUpdTime"])
        if datetime.now() - self.weatherUpdatedTime > timedelta(hours=1):
            self.pipikLogger.debug("updating temp")
            self.getTemp()
        else:
            self.pipikLogger.debug("temp up to date")
            self.temperature = settings["temperature"]
            self.sunrise_date = datetime.fromisoformat(settings["sunrise"])
            
    def getUserFromDC(self, dcUser: Union[discord.Member, discord.User, int, PipikUser]):
        if isinstance(dcUser, int):
            lookingfor = dcUser
        elif isinstance(dcUser, PipikUser):
            lookingfor = dcUser.id
        elif isinstance(dcUser, discord.member.Member):
            lookingfor = dcUser.id
        else:
            raise NotImplementedError(type(dcUser))
        for i in self.users:
            if i.id == lookingfor:
                return i
        else:
            self.users.append(PipikUser(dcUser))
            self.saveFile()
            return self.users[-1]
        
    async def updateUserStats(self, user, parameter, amount):
        setattr(user, parameter, amount)
        self.saveFile()

    async def addPill(self, ctx, colorEm, user, pill, amount=0):  # This is some special bullshit
        if amount != 0:
            for item in user.items:
                if item[0] == pill:
                    item[1] += amount
                    newAmount = item[1]
                    break
            else:
                user.items.append([pill, amount])
                newAmount = amount
            embedVar = discord.Embed(title="You´ve got pills!", description=f"try {mentionCommand(self.client,'pills')} for inventory", color=colorEm)
            embedVar.add_field(name="Pill:", value=pills[pill]["name"], inline=False)
            embedVar.add_field(name="Amount:", value=amount)
            embedVar.add_field(name="In inventory:", value=newAmount)
            await ctx.channel.send(embed=embedVar)
            self.saveFile()

    def getTemp(self):
        w = mgr.weather_at_place(location).weather
        self.temperature = w.temperature("celsius")["temp"]
        self.sunrise_date = w.sunrise_time(timeformat='date')
        # self.sunrise_date = self.sunrise_date + timedelta(hours=1) #note to self, DONT do this, i am checking utc time when measuring the pp, this is FINE
        self.weatherUpdatedTime = datetime.now()
        self.saveSettings()

    @discord.user_command(name="Hold pp", dm_permission=False)
    async def holding(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != member.id:
            await interaction.send(f"You are now holding {member.display_name}'s pp. This will be in effect until the next measurement done by anyone on this server.", ephemeral=True)
            self.holding.update({interaction.guild.id: interaction.user})
            self.pipikLogger.debug(f"{interaction.user} is holding in {interaction.guild}")
        else:
            await interaction.send(f"You are now holding your own pp. Umm... I don't know what for but to be honest i don't even wanna know. \nNo effect is in place.", ephemeral=True)
            self.pipikLogger.debug(f"{interaction.user} is holding self lolololol")

    @discord.slash_command(name="help", description="Lists what all the commands do.")
    async def help(self, ctx):
        await ctx.send("""```
    -----------------------------------
    PP COMMANDS:
    pp = Measures your pp.
    min = Leaderboard of smallest pps.
    max = Leaderboard of biggest pps.
    daily = Come back each day for your daily pills!
    fap = Increases your horniness level, growing your pp.
    profile = Shows someone's profile.
    weather = Shows how does the weather affect your pp.
    achi = Shows your achievements in your DMs.
    pills = Shows your inventory of pills.
    ---------------------------------
    non-pp commands:

    topic = Gives you a question to spin up a convo with.
    └ topic_filters = if you want to exclude some sensitive topics
    weather <city> = Shows current weather at place.
    radio = Spins up a radio player, you must be in a voice channel.
    └ leave = to kick it.
    time = Make discord timestamps
    cat = Random cat pic for when you feel down
    sub <subreddit name> = Random post from a subreddit
    bored = Recommends a random thread game to play in a text chat
    clovece = Play a game of clovece
    mycolor (if enabled on server) = Set your custom role color
    mat = Solve maths problems
    ps = Calculate IP adresses
    run = Execute python commands
    brainfuck = Run brainfuck code
    caesar = Encode/decode text with caesar cipher
    zssk = Call forth the train announcer lady to tell you info about a connection
    map = RPG game in development
    wordle = Play a game of co-op wordle
    ```""")

    @discord.slash_command(name="daily", description="Collect your daily pills")
    async def daily(self, ctx: discord.Interaction):
        user = self.getUserFromDC(ctx.user)
        try:
            self.pipikLogger.debug(f"user daily date {user.dailyDate}")
            if type(user.dailyDate) == datetime:
                user.dailyDate = user.dailyDate.date()
        except AttributeError as e:
            self.pipikLogger.error(e) # TODO if does not come up, remove this #yes should not happen
            user.dailyDate = (datetime.now() - timedelta(days=1)).date()
            user.dailyStreak = 0  # kind of redundant? nvm
        finally:
            if user.dailyDate == date.today():  # if today already taken
                tomorrow = datetime.now() + timedelta(1)
                midnight = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=0, minute=0, second=0)
                embedVar = discord.Embed(title="Daily pills", description="You already collected your pills today.", color=ctx.user.color)
                timestr = "<t:" + str(int(midnight.timestamp())) + ":R>"
                embedVar.add_field(name="Come back", value=timestr)
                await ctx.send(embed=embedVar)
                return
            elif (user.dailyDate - date.today()) < timedelta(days=-1):  # if streak broken
                embedVar = discord.Embed(title="Daily pills", description="Daily streak lost.", color=ctx.user.color)
                embedVar.add_field(name="Previous streak", value=user.dailyStreak)
                user.dailyStreak = 1
            elif (user.dailyDate - date.today()) == timedelta(days=-1):  # if picking up daily
                user.dailyStreak += 1
                if user.dailyStreak >= 30:
                    if "dedicated" not in user.achi:
                        await self.updateUserAchi(ctx,ctx.user, "dedicated")
                embedVar = discord.Embed(title="Daily pills", color=ctx.user.color)
                embedVar.add_field(name="Current streak", value=user.dailyStreak)
            else:
                self.pipikLogger.warning(f"something is wrong {user.dailyDate}, {date.today()}, {user.dailyDate - date.today()}")
                return
            await ctx.send(embed=embedVar)
            user.dailyDate = datetime.now().date()
            await self.addPill(ctx, ctx.user.color, user, 0, random.randint(1, 3))  # yellow pill
            if user.dailyStreak >= random.randint(0, 99):
                await self.addPill(ctx, ctx.user.color, user, 1, random.choices((1, 2), weights=(0.8, 0.2))[0])  # red pill
            if user.dailyStreak / 10 >= random.randint(0, 99):
                await self.addPill(ctx, ctx.user.color, user, 2, 1)  # blue pill
                if "lucky_draw" not in user.achi:
                    await self.updateUserAchi(ctx,ctx.user, "lucky_draw")
            #self.saveFile() saving happens in addpill() too

    @discord.slash_command(name="max", description="Leaderboard of biggest pps", dm_permission=False)
    async def max(self, ctx: discord.Interaction, server: str = discord.SlashOption("leaderboard", description="User leaderboard or server leaderboards", required=False, choices=("This server", "Between servers"), default="This server")):
        embedVar = discord.Embed(title="Leaderboard of {} biggest pps".format(ctx.guild.name + '\'s' if server == 'This server' else ''), description=25 * "-") #cant do f string
        if server == "This server":
            try:
                ldb = self.leaderboards[str(ctx.guild_id)]
            except KeyError:
                await ctx.send(embed=discord.Embed(title="Leaderboard empty",description=f"Use the {mentionCommand(self.client,'pp')} command to measure your pp first"))
                return
        elif server == "Between servers":
            ldb = sorted([(self.client.get_guild(int(id)).name, round(sum(map(lambda user: user[1], users)), 3)) for id, users in self.leaderboards.items()], key=lambda x: x[1], reverse=True)[:5]
        for i in ldb:
            try:
                user = ctx.guild.get_member(int(i[0])).display_name
                if user is None:
                    user = self.client.get_user(int(i[0])).name
            except ValueError:
                user = i[0]
            embedVar.add_field(name=user, value=f"{i[1]} cm {'total' if server == 'Between servers' else ''}", inline=False)
        await ctx.send(embed=embedVar)

    @discord.slash_command(name="min", description="Leaderboard of smallest pps", dm_permission=False)
    async def min(self, ctx: discord.Interaction, server: str = discord.SlashOption("leaderboard", description="User leaderboard or server leaderboards",required=False, choices=("This server", "Between servers"), default="This server")):

        if server == "This server":
            try:
                ldb = self.loserboards[str(ctx.guild_id)]
            except KeyError:
                await ctx.send(embed=discord.Embed(title="Loserboard empty", description=f"Use the {mentionCommand(self.client,'pp')} command to measure your pp first"))
                return
        elif server == "Between servers":
            ldb = sorted([(self.client.get_guild(int(id)).name, round(sum(map(lambda user: user[1], users)), 5)) for id, users in self.loserboards.items()], key=lambda x: x[1], reverse=False)[:5]
        embedVar = discord.Embed(title="Leaderboard of {} smallest pps".format(ctx.guild.name + '\'s' if server == 'This server' else ''), description=25 * "-") #cant do f string
        for i in ldb:
            try:
                user = ctx.guild.get_member(int(i[0])).display_name
                if user is None:
                    user = self.client.get_user(int(i[0])).name
            except ValueError:
                user = i[0]
            embedVar.add_field(name=user, value=f"{i[1]} cm {'total' if server == 'Between servers' else ''}", inline=False)
        await ctx.send(embed=embedVar)

    @discord.slash_command(name="weather", description="Current weather at location, or simply see how your pp is affected at the moment.")
    async def weather(self, ctx, location: str = discord.SlashOption(name="city", description="City name, for extra precision add a comma and a country code e.g. London,UK",required=False)):
        await ctx.response.defer()
        if not location:
            self.getTemp()
            offset = ((7 - abs(7 - datetime.now().month)) - 1) * 3  # average temperature okolo ktorej bude pocitat <zcvrk alebo rast>
            embedVar = discord.Embed(title=f"It´s {self.temperature} degrees in Bratislava.", description="You can expect {} {} pps".format(("quite", "slightly")[int(abs(self.temperature - offset) < 5)],("shorter", "longer")[int(self.temperature - offset > 0)]), color=(0x17dcff if self.temperature < offset - 5 else 0xbff5ff if self.temperature <= offset else 0xff3a1c if self.temperature > offset + 5 else 0xffa496 if self.temperature > offset else ctx.user.color))
            offsettime = self.sunrise_date.astimezone(pytz.timezone("Europe/Vienna"))
            embedVar.add_field(name="And the sun is coming up at", value="{}:{:0>2}.".format(offsettime.hour, offsettime.minute))
        else:
            if location == "me":
                try:
                    location = {617840759466360842: "Bardoňovo", 756092460265898054: "Plechotice", 677496112860626975: "Giraltovce", 735473733753634827: "Veľký Šariš"}[ctx.user.id]
                except KeyError:
                    pass
            else:
                try:
                    location = {"ds": "Dunajská Streda", "ba": "Bratislava", "temeraf": "Piešťany", "piscany": "Piešťany","pistany": "Piešťany", "mesto snov": "Piešťany", "terebes": "Trebišov", "eperjes": "Prešov", "blava": "Bratislava", "diera": "Stropkov", "saris": "Veľký Šariš", "ziar": "Žiar nad Hronom","pelejte": "Plechotice", "bardonovo": "Bardoňovo", "rybnik": "Rybník,SK"}[antimakkcen(location.casefold())]
                except KeyError:
                    if "better than" in location.casefold():
                        description = "Yeah babe, you are the best!"
                    elif any(word in location.casefold() for word in
                             ("dick", "pp", "penis", "cock", "schlong", "pussy", "humanity", "faith", "tits", "titty")):
                        description = "Very funny."
                    elif "to live" in location.casefold():
                        description = "Please seek help, do not suffer alone!"
                    elif "someone like you" == location:
                        description = "Keep searching Adele, maybe go deeper!"
                    elif "asked" in location:
                        description = "Oof what a burn! Your kindergarten friends must be impressed."
                    elif "someone" in location:
                        description = "Keep searching, babe."
                    elif any(word in location.casefold() for word in
                             ("gf", "bf", "girlfriend", "boyfriend", "girl friend", "boy friend")):
                        description = "I'm not a cupid, yo!"
                    else:
                        description = "Please check your spelling or specify the countrycode e.g. London,uk"
            # a = (mgr.weather_at_places(location, 'like', limit=1)[0]).weather some items are missing :(
            try:
                b = mgr.weather_at_place(location)
                a = b.weather
            except pyowm.commons.exceptions.NotFoundError:
                await ctx.send(embed=discord.Embed(title=f"{location} not found.", description=description))
                return
            else:
                embedVar = discord.Embed(title=f"Current weather at ** {b.location.name},{b.location.country}**", color=ctx.user.color)
                for k, v in {"Weather": a.detailed_status, "Temperature": str(a.temperature("celsius")["temp"]) + "°C",
                             "Feels like": str(a.temperature("celsius")["feels_like"]) + "°C",
                             "Clouds": str(a.clouds) + "%", "Wind": str(a.wind()["speed"] * 3.6)[:6] + "km/h",
                             "Humidity": str(a.humidity) + "%", "Visibility": str(a.visibility_distance) + "m",
                             "Sunrise": str(a.sunrise_time(timeformat="date") + timedelta(seconds=a.utc_offset))[11:19],
                             "Sunset": str(a.sunset_time(timeformat="date") + timedelta(seconds=a.utc_offset))[11:19],
                             "UV Index": a.uvi, "Atm. Pressure": str(a.pressure["press"]) + " hPa",
                             "Precip.": str(a.rain["1h"] if "1h" in a.rain else 0) + " mm/h"}.items():
                    embedVar.add_field(name=k, value=v)
                embedVar.set_thumbnail(url=a.weather_icon_url())
                moonphases = (':new_moon:', ':waning_crescent_moon:', ':last_quarter_moon:', ':waning_gibbous_moon:', ':full_moon:', ':waxing_gibbous_moon:', ':first_quarter_moon:', ':waxing_crescent_moon:')
                currphase = int(mapvalues(moon.phase(), 0, 28, 0, len(moonphases)))
                embedVar.set_footer(text=f"Local time: {str(datetime.utcnow() + timedelta(seconds=a.utc_offset))[11:19]} | Moon phase: {emoji.emojize(moonphases[currphase])}")
        await ctx.send(embed=embedVar)

    @discord.slash_command(name="tips", description="Read some tips on how to increase your pp size")
    async def tips(self, ctx):
        text = """```ansi
    [41m[37mDisclaimer: EVERYTHING IS RANDOM, NOTHING GUARANTEES BIGGER PPS, ONLY BETTER CHANCES FOR A BIG PP![0m

    [34mA lot of things can influence your pp's size.
    For your convenience i'll share some tips and tricks
    for you here:
    [0m--------------------------------------------------
    
    [32mI´ve heaRd your pp looks Mightier in other people´s hands But not in yours, so try asking others to hold it for you.

    [32mThe bot likes compliments, try some sweet words on it.

    [31mThe bot however dislikes insults.

    [32mFull moon is the best time to get a big pp.

    [31mLower temperatures may cause your pp to shrink, consider measuring it when it´s warmer outside.

    [32mMorning woods are a normal healthy occurrence each morning, try to use them to your advantage.

    [32mIf you overslept this wakeup routine, don't worry, you can try to excite your pp with the [35mfap [32mcommand
    But be wary of your endurance, relapsing causes you to go into a recharge state when your pp becomes more shy than usual.

    [34mIf nothing else helps, you can turn to pills for help. But beware as overusing them might bring unforeseen side effects, like impotency.
    You can get free pills each day with the [35mdaily [34mcommand
    ```"""
        if ctx.user.is_on_mobile():
            text = text.replace("[34m", "")
            text = text.replace("[32m", "")
            text = text.replace("[33m", "")
            text = text.replace("[35m", "")
            text = text.replace("[41m", "")
            text = text.replace("[0m", "")
        await ctx.send(text)
        
    class PillCraftDropdown(discord.ui.Select):
        def __init__(self, user, cog):
            self.user = user
            self.cog = cog
            pillselect = [discord.SelectOption(label="Cancel", value="-1", emoji=emoji.emojize(":cross_mark:"))] #TODO please migrate to a dict alredy so i dont have to juggle these *which* values and remove the enum
            for n,pill in enumerate([item for item in self.user.items if item[0] != len(pills) - 1 and item[1] >= 10]):  # populating the select component with options
                pillselect.append(discord.SelectOption(label=pills[pill[0]]["name"], value=f"{n}", description=f"in inventory: {pill[1]}"))
            super().__init__(placeholder="Select pills to crush up", options=pillselect)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user.id:
                if self.values[0] == "-1":
                    await interaction.response.edit_message(embed=discord.Embed(description="Cancelled.", color=interaction.user.color), view=None, delete_after=5.0)
                else:
                    which = int(self.values[0])
                    # amount = int(attr[2] or 1) #TODO: do multiselect again or just add it as options,# resend view with updated dropdown options? but then need to edit msg too, then take it out into a different function
                    amount = 1
                    if self.user.items[which][1] >= 10:
                        self.user.items[which][1] -= amount * 10
                        if "breaking_bad" not in self.user.achi:
                            await self.cog.updateUserAchi(interaction, interaction.user, "breaking_bad") #moved this up so achi adding happens before savefile gets called in addpill
                        await self.cog.addPill(interaction, interaction.user.color, self.user, (self.user.items[which][0]) + 1, amount) #TODO really reimagine this
                        embedVar = discord.Embed(description=f"You crushed up 10 {pills[int(self.values[0])]['name']}", color=interaction.user.color)
                        await interaction.response.edit_message(embed=embedVar, view=None)
                        if self.user.items[which][1] == 0:
                            del (self.user.items[which])
                    else: #TODO remove this shouldnt be possible
                        self.cog.pipikLogger.warning(f"{interaction.user} with {self.user.items} wanted to craft up 10 {which}")

            else:
                await interaction.send(f"This is not your prompt, use {mentionCommand(self.cog.client,'pills')} to use your pills.", ephemeral=True) # i won't bother embedizing

    class PillsButtonsConsume(discord.ui.Button):
        def __init__(self, user: PipikUser, cog):
            self.user = user
            self.cog = cog
            canConsume = len(user.items) != 0 and self.user.pill not in range(0, len(pills))
            super().__init__(label="Consume", disabled=not canConsume, style=discord.ButtonStyle.gray,emoji=emoji.emojize(":face_with_hand_over_mouth:"))

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.send(f"This is not your inventory, use {mentionCommand(self.cog.client,'pills')} to see your pills.", ephemeral=True) #neither this
                return
            # self.style = discord.ButtonStyle.green
            # for child in self.view.children:
            #     child.disabled = True
            # await interaction.response.edit_message(view=self.view)
            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.PillTakeDropdown(self.user, self.cog))
            await interaction.message.edit(embed=discord.Embed(title="Pill consumption", color=interaction.user.color), view=viewObj)

    class PillsButtonsCraft(discord.ui.Button):
        def __init__(self, user, cog):
            self.user = user
            self.cog = cog
            canCraft = any((i[1] >= 10 for i in user.items))
            super().__init__(label="Craft", disabled=not canCraft, style=discord.ButtonStyle.gray, emoji=emoji.emojize(":hammer:"))

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.send(f"This is not your inventory, use {mentionCommand(self.cog.client,'pills')} to see your pills.", ephemeral=True)
                return
            #self.style = discord.ButtonStyle.green
            #for child in self.view.children:
            #    child.disabled = True
            #await interaction.response.edit_message(view=self.view)

            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.PillCraftDropdown(self.user, self.cog))
            await interaction.message.edit(embed=discord.Embed(title="Pill crafting", color=interaction.user.color), view=viewObj)

    class PillTakeDropdown(discord.ui.Select):
        def __init__(self, user: PipikUser, cog):
            self.user = user
            self.cog = cog
            pillselect = [discord.SelectOption(label=pills[pill[0]]["name"], value=str(pill[0]),description=f"in inventory: {pill[1]}") for pill in self.user.items if pill[1] > 0] + [discord.SelectOption(label="Cancel",value="-1",emoji=emoji.emojize(":cross_mark:"))]

            super().__init__(placeholder="Select a pill to consume", options=pillselect)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user.id:
                if self.values[0] == "-1":
                    await interaction.response.edit_message(content="Cancelled.", embed=None, view=None, delete_after=5.0)
                else:
                    await interaction.response.edit_message(content=None, embed=discord.Embed(title=f"You took a {pills[int(self.values[0])]['name']}",description="Now go measure your pp before it wears out!",color=interaction.user.color),view=None)
                    if "pill_popper" not in self.user.achi:
                        await self.cog.updateUserAchi(interaction, interaction.user, "pill_popper") #moved this above takepill so achi adding happens before savefile gets called
                    await self.user.takePill(int(self.values[0]), self.cog)

            else:
                await interaction.send(f"This is not your prompt, use {mentionCommand(self.cog.client,'pills')} to use your pills.",ephemeral=True)

    @discord.slash_command(description="See, manage and use your pill inventory.")
    async def pills(self, ctx):
        user = self.getUserFromDC(ctx.user)
        user.items = [item for item in user.items if item[1] > 0] #removnig ones that you dont own, idk where this is implemented, maybe got lost in the migration
        user.items = sorted(user.items, key=lambda a: a[0])
        text = "```py\n"
        text += "Pills".center(25) + "\nCrafting takes 10 pills and crafts a better quality one\nBetter pills equals bigger pps\nExcessive use might result in impotency!\n{:-^25}\n".format("-")
        text += "\n".join(["{:<15} ({:<2} min)| amount: {}".format(pills[i[0]]["name"],(pills[i[0]]["effectDur"].seconds) // 60, i[1]) for i in list(user.items)])
        if len(user.items) == 0:
            text += f"You have no pills. Use {mentionCommand(self.client,'daily')} to get some!"
        text += "\n```"

        if user.pill in range(0, len(pills)):
            self.pipikLogger.debug(f"uh oh pill already in you {user.pill}")
            takenAgo = datetime.now() - user.pillPopTime
            if takenAgo < pills[user.pill]["effectDur"] + pills[user.pill]["badEffectDur"]:
                self.pipikLogger.debug("nem jart le")
            else:
                user.pill = None

        viewObj = discord.ui.View()
        viewObj.add_item(self.PillsButtonsConsume(user, self))
        viewObj.add_item(self.PillsButtonsCraft(user, self))
        await ctx.send(content=text, view=viewObj)

    class FapButton(discord.ui.Button):
        def __init__(self, user, cog):
            self.user = user
            self.cog = cog
            if user.cd is None:
                color = discord.ButtonStyle.green
                label = f"Combo: {user.fap}"
                emojiLabel = emoji.emojize(":fist:", language="alias")
                disabled = False
            else:
                disabled = True
                color = discord.ButtonStyle.red
                label = "Refractory period"
                emojiLabel = emoji.emojize(":cross_mark:")
            super().__init__(label=label, disabled=disabled, style=color, emoji=emojiLabel)

        async def callback(self, interaction):
            if interaction.user.id != self.user.id:
                await interaction.send(f"This is not your button, use your own by using {mentionCommand(self.cog.client,'fap')}", ephemeral=True)
                return
            if random.randint(0, 10 + (self.user.fap * 2)) < 10:
                self.user.fap += 1
                self.label = f"Combo: {self.user.fap}"
            else:
                self.style = discord.ButtonStyle.red
                self.emoji = emoji.emojize(':sweat_droplets:')
                self.disabled = True
                self.label = "Oops, too much!"
                if self.user.fap == 0:
                    if "one_pump" not in self.user.achi:
                        await self.cog.updateUserAchi(interaction, interaction.user, "one_pump")
                self.user.cd = datetime.now() + timedelta(minutes=5)
                self.user.fap = 0
            await interaction.response.edit_message(view=self.view)

    @discord.slash_command(name="fap", description="Increase your pp length by repeatedly mashing a button.")
    async def fap(self, ctx):
        user = self.getUserFromDC(ctx.user)
        if user.cd is not None:
            if user.cd == 0 or user.cd - datetime.now() < timedelta(seconds=0):
                user.cd = None
        if user.cd is None:
            embedVar = discord.Embed(description="Use repeatedly to increase length.", color=ctx.user.color)
        else:
            timestr = "<t:" + str(int(user.cd.timestamp())) + ":R>"
            embedVar = discord.Embed(description=f"Come back {timestr}.", color=ctx.user.color)
        viewObj = discord.ui.View()
        viewObj.add_item(self.FapButton(user, self))
        await ctx.send(embed=embedVar, view=viewObj)

    @discord.slash_command(name="profile", description="See your, or someone else's pp profile") #oh my god this is ugly
    async def profile(self, ctx: discord.Interaction, user: discord.User = discord.SlashOption(name="user", description="User to display", required=False)):
        usertocheck = user or ctx.user
        user = self.getUserFromDC(usertocheck)

        temppill = False #todo make this a separate function
        if user.pill not in (None, "None", "none"):
            temppill = True
            takenAgo = datetime.now() - user.pillPopTime
            if takenAgo > pills[user.pill]["effectDur"]:
                temppill = None
                badEffectStart = user.pillPopTime + pills[user.pill]["effectDur"]
                user.cd = datetime.now() + (pills[user.pill]["badEffectDur"] - (datetime.now() - badEffectStart))
                if takenAgo > pills[user.pill]["effectDur"] + pills[user.pill]["badEffectDur"]:
                    user.pill = None

        if user.cd is not None:
            if user.cd == 0 or user.cd - datetime.now() < timedelta(seconds=0):
                user.cd = None
            else:
                dysf_left = user.cd - datetime.now()

        temphorniness = user.fap + (pills[user.pill]["effect"] if user.pill not in (None, "None", "none") else 0)
        user.items = sorted(user.items, key=lambda a: a[0])

        text = usertocheck.name.center(25, "=")
        text += f"\nPersonal best: {user.pb}\nPersonal worst: {user.pw}\n"
        text += f"Horniness: {temphorniness}\n" if user.cd is None else ""
        text += "Pill: {} | {} minutes left.\n".format(pills[user.pill]["name"], ((pills[user.pill]["effectDur"] - takenAgo).seconds // 60) + 1) if temppill else ""
        text += "Erectyle disfunction: {} hours {} minutes\n".format(dysf_left.seconds // 3600, (dysf_left.seconds // 60 % 60) + 1) if user.cd is not None else ""
        text += "{:-^25}".format("Items") + "\n"
        text += "\n".join(["{:<20} | amount: {}".format(pills[i[0]]["name"], i[1]) for i in list(user.items)])
        text += "\n{:-^25}\n".format("Achievements")
        text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) for achi in self.achievements.values())
        text += "\n" + "{:-^25}".format("-")
        await ctx.send("```\n" + text + "\n```" + f"for more info, try {mentionCommand(self.client,'achi')}") #lord forgive me for what ive done

    @discord.slash_command(name="achi", description="See your achievements")
    async def achi(self, ctx):
        user = self.getUserFromDC(ctx.user)
        achievements = self.achievements
        text = "Your achievements".center(60,"=")+"\n"
        text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) + (("= " + achi.desc) if achi.achiid in user.achi else "= ???") for achi in achievements.values())
        await ctx.send("```\n" + text + "\n```", ephemeral=True)

    @discord.slash_command(name="pp", description="For measuring your pp.",dm_permission=False)
    async def pp(self, ctx: discord.Interaction, message: str = discord.SlashOption(name="message", description="Would you like to tell me something?", required=False, default=None)):
        await ctx.response.defer()
        msg = None
        embedMsg = discord.Embed(description=".", color=ctx.user.color)  # placeholders
        user = self.getUserFromDC(ctx.user)
        currmethods = 0  # this is for keeping track of what pp enlargement methods were used. Im gonna perform bitwise operations on this
        self.pipikLogger.debug(f"{datetime.now() - self.weatherUpdatedTime}, weatherupdatetimer, how long ago was updated")
        if datetime.now() - self.weatherUpdatedTime > timedelta(hours=1):
            self.pipikLogger.debug("updating temp")
            self.getTemp()
        else:
            self.pipikLogger.debug("temp up to date")

        curve = 2
        multiplier = 100

        # pill checker
        if user.pill in range(0, len(pills)) and user.pill not in (None, "none", "None"):  # fucking inconsistent
            takenAgo = datetime.now() - user.pillPopTime
            if takenAgo < pills[user.pill]["effectDur"]:
                currmethods = currmethods | 32
                curve -= pills[user.pill]["effect"] / 15
                multiplier += pills[user.pill]["effect"]
            elif takenAgo < pills[user.pill]["effectDur"] + pills[user.pill]["badEffectDur"]:
                badEffectStart = user.pillPopTime + pills[user.pill]["effectDur"]
                user.cd = datetime.now() + (pills[user.pill]["badEffectDur"] - (datetime.now() - badEffectStart))
            else:
                user.cd = None
                user.pill = None

        # fap checker
        if user.cd is not None:
            if user.cd == 0 or user.cd - datetime.now() < timedelta(seconds=0):
                user.cd = None
            else:
                multiplier -= 20
                curve += 1
        else:
            multiplier += user.fap * 4
            curve -= user.fap / 8
            if user.fap > 0:
                user.fap -= 1
                currmethods = currmethods | 16

        # morning wood checker
        tz_info = self.sunrise_date.tzinfo
        sunrise = self.sunrise_date - datetime.now(tz_info)
        self.pipikLogger.debug(f"morning wood check, {self.sunrise_date}, sunrise date (gmt) # {sunrise}, until sunrise {datetime.now(tz_info)}, current time (gmt)")
        if timedelta(hours=1) > sunrise > timedelta(hours=-1):
            multiplier += 10
            curve -= 0.5
            currmethods = currmethods | 8
            if "morning" not in user.achi:
                await self.updateUserAchi(ctx, ctx.user, "morning")

        # compliment checker
        compliments = 0
        if message:
            if antimakkcen(str(message.split(" ")[0].casefold()).strip("!")) in ("ahoy", "hello", "hi", "hey", "hellou", "sup", "ahoj", "cau", "cauky"):
                embedMsg = discord.Embed(description=f"Heya {ctx.user.display_name}! \\\(^.^)/",color=ctx.user.color)
            else:
                embedMsg = discord.Embed(description="Oh so you are trying to impress me with your sweet honeyed words...",color=ctx.user.color)
            await ctx.send(embed=embedMsg)
            msg = await ctx.original_message()
            await asyncio.sleep(2)
            if message not in self.usedcompliments:
                #messagelist = [antimakkcen(word.casefold()) for word in message.split(" ")]
                #compliments = len(good_words.intersection(messagelist)) - len(bad_words.intersection(messagelist))

                for word in good_words:
                    if word in message.casefold():
                        compliments += 1
                for word in bad_words:
                    if word in message.casefold():
                        compliments -= 1

                multiplier += 2.2 * min(5, compliments)
                curve -= min(5, compliments) * 0.12

                if compliments < 1:
                    embedMsg.add_field(name=random.choice(bad_responses), value=emoji.emojize(random.choice(bad_emojis)), inline=False)
                else:
                    embedMsg.add_field(name=random.choice(good_responses), value=emoji.emojize(random.choice(good_emojis)), inline=False)
                    currmethods = currmethods | 2
                # compliment achi checker
                if compliments > 4 and "flirty" not in user.achi:
                    await self.updateUserAchi(ctx, ctx.user, "flirty")
                elif compliments < -4 and "playa" not in user.achi:
                    await self.updateUserAchi(ctx, ctx.user, "playa")

                #compliment logger
                if len(self.usedcompliments) > 5:
                    self.usedcompliments.pop()
                self.usedcompliments.add(message)
            else:
                embedMsg.add_field(name=random.choice(duplicate_responses),value=emoji.emojize(random.choice(bad_emojis)),inline=False)


        # temperature adjustment
        pocasieOffset = ((7 - abs(7 - datetime.now().month)) - 1) * 3  # average temperature okolo ktorej bude pocitat <zcvrk alebo rast> #TODO make this dynamic and global to whole world
        if self.temperature > pocasieOffset + 5:
            currmethods = currmethods | 4
        curve -= (self.temperature - pocasieOffset) / 20
        multiplier += self.temperature - pocasieOffset

        #moon phase checker
        if int(moon.phase()) in range(14,21):
            multiplier += 10
            curve -= 0.1
            currmethods = currmethods | 64

        # holding checker
        try:
            self.pipikLogger.debug(f"holdings table {self.holding} curr server {ctx.guild.id}, author {ctx.user.id}")
            #if True:
            if ctx.guild.id in self.holding and self.holding[ctx.guild.id] != ctx.user:
                currmethods = currmethods | 1
                curve -= 0.4
                multiplier += 11
                holder = self.holding[ctx.guild.id]
                held: PipikUser = self.getUserFromDC(ctx.user)
                embedMsg.add_field(name="With helping hands from:", value=holder.display_name)
                holderpp = self.getUserFromDC(holder)
                if msg:
                    await msg.edit(embed=embedMsg)
                if "helping_hands" not in held.achi:  # helpout
                    await self.updateUserAchi(ctx,ctx.user, "helping_hands")  # holding achis
                if "friend_need" not in holderpp.achi:
                    await self.updateUserAchi(ctx,holder, "friend_need")
            del self.holding[ctx.guild.id]
        except KeyError as e: #redundant
            self.pipikLogger.debug(str(e) + " - in this guild noone is holding anything")

        # final calculation
        if curve < 0:
            self.pipikLogger.warning(25 * "#" + "uh oh stinky")
            curve = -curve * 0.01
        pipik = round((random.expovariate(curve) * multiplier), 3)
        self.pipikLogger.debug(f"{ctx.user.display_name}, pipik, {pipik}, curve, {curve}, mult, {multiplier}, compl, {compliments}, temp,{self.temperature}, fap, {user.fap}, cd, {user.cd}")

        # personal record checker
        if pipik > user.pb:
            await self.updateUserStats(user, "pb", pipik)
        if not user.pw or pipik < user.pw:
            await self.updateUserStats(user, "pw", pipik)

        # rekord checker
        try:
            self.pipikLogger.debug(f"this server´s leaderboard {self.leaderboards[str(ctx.guild_id)]}")
        except KeyError:
            self.leaderboards[str(ctx.guild_id)] = []
        if len(self.leaderboards[str(ctx.guild_id)]) > 4 and len(self.loserboards[str(ctx.guild_id)]) > 4:  # if leaderboard fully populated go check if the new measurement is better,
            if pipik > self.leaderboards[str(ctx.guild_id)][0][1] or pipik < self.loserboards[str(ctx.guild_id)][0][1]:  # otherwise just automatically populate it on the leaderboard without announing a record
                star = emoji.emojize(':glowing_star:')
                await ctx.channel.send(embed=discord.Embed(title=(str(3 * star) + "Wow! {} has made a new record!" + str(3 * star)).format(ctx.user.name),description="Drumroll please... " + emoji.emojize(":drum:"), color=discord.Colour.gold()))
                await asyncio.sleep(2)
            if pipik > self.leaderboards[str(ctx.guild_id)][4][1]:  # if bigger than the smallest on the leaderboard
                self.updateLeaderBoard(str(ctx.guild_id), ctx.user.id, pipik)
            if pipik < self.loserboards[str(ctx.guild_id)][4][1]:  # if smaller than the biggest on the leaderboard
                self.updateLoserBoard(str(ctx.guild_id), ctx.user.id, pipik)
        else:
            self.updateLeaderBoard(str(ctx.guild_id), ctx.user.id, pipik)
            self.updateLoserBoard(str(ctx.guild_id), ctx.user.id, pipik)

        # size achi checker
        if pipik > 300:
            if "megapp" not in user.achi:
                await self.updateUserAchi(ctx,ctx.user, "megapp")
        elif pipik < 0.5:
            if "micropp" not in user.achi:
                await self.updateUserAchi(ctx,ctx.user, "micropp")
        elif 69 <= pipik < 70:
            if "nice" not in user.achi:
                await self.updateUserAchi(ctx,ctx.user, "nice")

        # pp enlargement methods achi checker
        try:
            user.methods
        except KeyError:
            user.methods = 0
        if currmethods == 127 and "desperate" not in user.achi:
            await self.updateUserAchi(ctx,ctx.user, "desperate")
        if currmethods | user.methods != user.methods:
            await self.updateUserStats(user, "methods", user.methods | currmethods)
        if user.methods == 127 and "tested" not in user.achi:
            await self.updateUserAchi(ctx,ctx.user, "tested")

        # final printer
        footertext = f'{emoji.emojize(":handshake:",language="alias") if currmethods & 1 else ""}{emoji.emojize(":heart_eyes:",language="alias") if currmethods & 2 else ""}{emoji.emojize(":thermometer:",language="alias") if currmethods & 4 else ""}{emoji.emojize(":sunrise:",language="alias") if currmethods & 8 else ""}{emoji.emojize(":fist:",language="alias") if currmethods & 16 else ""}{emoji.emojize(":pill:",language="alias") if currmethods & 32 else ""}{emoji.emojize(":waning_gibbous_moon:",language="alias") if currmethods & 64 else ""}'
        embedMsg.title = f"*{ctx.user.display_name}* has **{pipik}** cm long pp!"
        embedMsg.description = str("o" + (min(4094, (int(pipik) // 10)) * "=") + "3")
        embedMsg.set_footer(text=footertext,icon_url=ctx.user.avatar.url)
        embedMsg.timestamp = datetime.now()
        if msg:
            await msg.edit(embed=embedMsg)
        else:
            await ctx.send(embed=embedMsg)
    
def setup(client,baselogger):
    client.add_cog(PipikBot(client,baselogger))
