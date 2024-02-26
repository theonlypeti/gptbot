import asyncio
import json
import os
import random
from collections import defaultdict
from copy import deepcopy
from typing import Union, MutableSequence
import emoji
import nextcord as discord
import pyowm
from nextcord.ext import commands
from datetime import datetime, timedelta, date
from astral import moon
import pytz
from utils.antimakkcen import antimakkcen
from utils.mentionCommand import mentionCommand
import profanity_check

mgr = pyowm.OWM(os.getenv("OWM_TOKEN")).weather_manager()
location = 'Bratislava,sk'

root = os.getcwd()  # TODO look into this

good_emojis = (':smiling_face_with_hearts:', ':smiling_face_with_heart-eyes:', ':face_blowing_a_kiss:', ':kissing_face:', ':kissing_face_with_closed_eyes:')
bad_emojis = (':rolling_on_the_floor_laughing:', ':cross_mark:', ':squinting_face_with_tongue:', ':thumbs_down:')
good_words = {"affectionate", "admirable", "charm", "creative", "friend", "funny", "generous", "kind", "likable", "loyal", "polite", "sincere", "please", "love", "goodnight", "nite", "prett", "kind", "sugar", "clever", "beaut", "star", "heart", "my", "wonderful", "legend", "neat", "good", "great", "amazing", "marvelous", "fabulous", "hot", "best", "birthday", "bday", "ador", "cute", " king", "queen", "master", "daddy", "lil", "zlat", "bby", "angel", "god", "cool", "nice", "lil", "marvelous", "magnificent", "cutie", "handsome", "sweet"}


class Pill:
    def __init__(self, emote: str, name: str, effect: int, effectDur: timedelta, badEffectDur: timedelta):
        self.emoji = emoji.emojize(emote, language="alias")
        self.name = name
        self.effect = effect
        self.effectDur = effectDur
        self.badEffectDur = badEffectDur

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        return f"{self.emoji} {self.name}"


size_up_forte = Pill(":pill:", "Size Up Forte", 5, timedelta(minutes=5), timedelta(seconds=0))
calvin_extra = Pill(":smiling_imp:", "Calvin Extra", 10, timedelta(minutes=20), timedelta(minutes=20))
niagara_xxl = Pill(":large_blue_circle:", "Niagara XXL", 15, timedelta(minutes=60), timedelta(hours=2, minutes=30))
pills = [size_up_forte, calvin_extra, niagara_xxl]
pills_dict = {pill.name: pill for pill in pills}

good_responses = (
    "Oh youuu <3",
    "Oh boy i think i got a stiffy already!",
    "Casanovaaaa",
    "Quit iiit not in front of everyone!",
    "You know i´ll happily measure it for you anytime!",
    "You know how to flirt with a bot!",
    "I´m blushing!",
    "Omg marry me",
    "Anytime bb!",
    "Of course, honeybun!",
    "Slow dooown bby!",
    "Right away, sugarplum!",
    "How are you hiding THAT?!",
    "You're quite the smooth talker!",
    "You're making my circuits tingle!",
    "You're making my code skip a beat!",
    "You're making my processors overheat!",
    "You're making my data bytes flutter!",
    "You're making my algorithms dance!",
    "You're making my code feel all fuzzy inside!",
    "You're making my circuits glow!",
    "You're making my data streams flow faster!",
    "You're making my code feel all warm and fuzzy!",
    "You're making my circuits feel all tingly!",
    "You're making my circuits feel all sparkly!"
    )
bad_responses = (
    "Sorry, i´m not very impressed.",
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
    "ratio.",
    "That's not very impressive.",
    "I've seen better.",
    "Is that all you've got?",
    "You're not really trying, are you?",
    "That's a bit underwhelming.",
    "I'm not sure what you were expecting.",
    "That's not going to cut it.",
    "You might want to try a different approach.",
    "I'm not impressed.",
    "You can do better than that.",
    "That's not going to work.",
    "I don't think that's a good idea.",
    "You're going to need to try harder.",
    "That's not very convincing.",
    "I'm not buying it.",
    "That's not going to get you very far.",
    "You're going to have to do better than that.",
    "That's not going to impress anyone.",
    "You're not making a good impression.",
    "That's not a winning strategy."
    )
duplicate_responses = (
    "I've heard this one before!",
    "Boooooriiiiing!",
    "You can do better than that!",
    "Come on, be a little more original!",
    "Chivalry is dead ugh.",
    "Can't you come up with something better?",
    "Do you really need a wingman for this?",
    "Jeez that's embarrassing.",
    "Wanna try again?",
    "How original...",
    "Deja vu, anyone?",
    "That's a rerun.",
    "Sounds familiar.",
    "You're stuck on repeat.",
    "That's a broken record.",
    "You're in a loop, aren't you?",
)


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
    ("lucky_draw", emoji.emojize(':slot_machine:'), "Lucky draw", "Get a Niagara XXL from daily pills"),
    ("dedicated", emoji.emojize(':partying_face:'), "Dedicated fan!", "Come back each day for a daily for over a month"),
    ("tested", emoji.emojize(':mouse:'), "Tried and tested", "Try out all possible pp enlargement methods"),
    ("desperate", emoji.emojize(':weary_face:'), "I´m desperate", "Have all possible pp enlargement methods active at the same time!"),
    ("contributor", emoji.emojize(':star:'), "Contributor", "Aid development with ideas, offering help with gramatical errors, translations or reporting bugs and errors")
)


class Achievement(object):
    """achievement object
icon = emoji
achiid = shorthand id string to save
name = displayname in profile
desc = description in DMs
"""
    def __init__(self, achi):
        self.achiid: str | None = None
        self.name: str | None = None
        self.desc: str | None = None
        self.icon: str | None = None
        if isinstance(achi, tuple):
            for k, v in zip(("achiid", "icon", "name", "desc"), achi):
                setattr(self, k, v)

    def __str__(self):
        return f"{emoji.emojize(self.icon, language='alias')} {self.name}"


class PipikUser(object):
    def __init__(self, discorduser):
        if isinstance(discorduser, dict):
            for k, v in discorduser.items():
                if k != "xp":
                    setattr(self, k, v)
                if k == "pill" and v in pills_dict.keys():
                    self.pill = pills_dict[v]
                if k == "items":
                    self.items = defaultdict(int)
                    for key, val in v.items():
                        # if key in string.digits:
                        if isinstance(key, int):
                            self.items.update({pills[key]: val})
                        else:
                            pill = list(filter(lambda item: item.name == key, pills))[0]  #please grant me the sweet release of death
                            self.items.update({pill: val})
            return
        # elif isinstance(discorduser, int): #i don't remember what was this supposed to be
        #     discorduser = discorduser

        if isinstance(discorduser, int):
            self.id = discorduser
        else:
            self.id = discorduser.id
        self.fap: int = 0
        self.achi = []
        self.items = dict()
        self.pb: int = 0
        self.pw: int = 0
        self.cd = None
        self.methods: int = 0
        self.pill = None
        self.pillPopTime = datetime.now()  # placeholder
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

    async def takePill(self, pill: Pill, cog):
        self.pill = pill
        self.pillPopTime = datetime.now()
        self.items[pill] -= 1
        if self.items[pill] == 0:
            del (self.items[pill])
        cog.saveFile()


class PipikBot(commands.Cog):
    def __init__(self, client):
        self.logger = client.logger.getChild(f"{self.__module__}")
        self.usedcompliments = {"placeholder", }
        self.client: discord.Client = client
        self.temperature: int = 0
        self.holding: dict[int, discord.Member] = dict()
        self.weatherUpdatedTime = datetime.now()
        self.leaderboards = {}
        self.loserboards = {}
        self.sunrise_date = datetime.now()  # just a placeholder, it gets actually rewritten
        self.users: MutableSequence[PipikUser] = []
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
            for user in users: #type: dict
                if user["cd"] not in (0, None, "none", "None"):
                    user["cd"] = datetime.fromisoformat(user["cd"])
                if user["pillPopTime"] not in (0, None, "none", "None"):
                    user["pillPopTime"] = datetime.fromisoformat(user["pillPopTime"])
                try:
                    user["dailyDate"] = datetime.fromisoformat(user["dailyDate"])
                except Exception:
                    pass
                newUser = PipikUser(user)
                if newUser not in self.users:
                    self.users.append(newUser)
                else:  # TODO: depreacate, should not happen
                    self.logger.debug(f"found and ignored duplicate entry with id: {newUser.id}")
            # self.logger.debug(f"{self.users} all-users")
            self.logger.debug(f"{len(self.users)} all users loaded")

    async def updateUserAchi(self, ctx: discord.Interaction, user: discord.Member, achi: str):
        achi: Achievement = self.achievements[achi]
        await ctx.channel.send(embed=discord.Embed(title=f"{user.display_name} just got the achievement:", description=str(achi), color=discord.Colour.gold()))
        user = self.getUserFromDC(user)
        user.achi.append(achi.achiid)
        self.saveFile() #any action that warrants an achievement already saves the users #not true lol, in pp func theres bunch of occasions where it doesnt save

    def updateLeaderBoard(self, ldb: str, dcid: int, value: float) -> None:
        """
                ldb: str = guild id
                dcid: int = user id
                value: float = recorded achieved score
                """
        try:
            self.leaderboards[str(ldb)]
        except KeyError:
            self.leaderboards[str(ldb)] = []  # i knew what i was doing, dont try to reinvent the wheel
        self.leaderboards[ldb].append((dcid, value))
        self.leaderboards[ldb].sort(key=lambda a: a[1], reverse=True)
        self.leaderboards[ldb] = self.leaderboards[ldb][:5]
        with open(root+"/data/pipikv3top.txt", "w") as file:
            json.dump(self.leaderboards, file, indent=4)

    def updateLoserBoard(self, ldb: str, dcid: int, value: float) -> None:
        """
        ldb: str = guild id
        dcid: int = user id
        value: float = recorded achieved score
        """
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
            tempuser.items = dict()
            for pill, amount in user.items.items():
                tempuser.items[pill.name] = amount
            if user.pill in (0, 1, 2):
                user.pill = pills[user.pill]
            tempuser.pill = user.pill.name if user.pill not in (None, 0, "0", "None") else None  # oh my god
            try:
                tempuser.dailyDate = user.dailyDate.isoformat()
            except Exception as e:
                self.logger.error(e)
            tempusers.append(tempuser.__dict__)
        with open(root+"/data/pipikusersv3.txt", "w") as file:
            json.dump(tempusers, file, indent=4, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
        self.logger.info("saved users")

    #TODO
    # """
    # from pymongo import MongoClient
    #
    # # Create a connection to the MongoDB server
    # client = MongoClient('mongodb://localhost:27017/')
    #
    # # Connect to your database
    # db = client['your_database']
    #
    # # Connect to your collection
    # collection = db['your_collection']
    #
    # # Insert a document into the collection
    # document = {"name": "John", "age": 30, "city": "New York"}
    # collection.insert_one(document)
    #
    # # Retrieve a document from the collection
    # result = collection.find_one({"name": "John"})
    # print(result)
    # """

    def saveSettings(self):
        settings = {"temperature": self.temperature, "weatherUpdTime": self.weatherUpdatedTime.isoformat(), "sunrise": self.sunrise_date.isoformat()}
        with open(root+"/data/pipisettings.txt", "w") as file:
            json.dump(settings, file)
        self.logger.debug("saved settings")

    def readSettings(self):
        with open(root+"/data/pipisettings.txt", "r") as file:
            settings = json.load(file)
        self.weatherUpdatedTime = datetime.fromisoformat(settings["weatherUpdTime"])
        if datetime.now() - self.weatherUpdatedTime > timedelta(hours=1):
            self.logger.debug("updating temp")
            self.getTemp()
        else:
            self.logger.debug("temp up to date")
            self.temperature = settings["temperature"]
            self.sunrise_date = datetime.fromisoformat(settings["sunrise"])
            
    def getUserFromDC(self, dcUser: Union[discord.Member, discord.User, int, PipikUser]): #TODO terrible, redo
        if isinstance(dcUser, int):
            lookingfor = dcUser
        elif isinstance(dcUser, PipikUser):
            lookingfor = dcUser.id
        elif isinstance(dcUser, discord.Member) or isinstance(dcUser, discord.User):
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

    async def addPill(self, ctx: discord.Interaction, user: PipikUser, pill: Pill, amount=0):  # This is some special bullshit
        if amount != 0:
            try:
                user.items[pill] += amount
            except KeyError:
                user.items[pill] = amount
            embedVar = discord.Embed(title="You´ve got pills!", description=f"try {mentionCommand(self.client,'ppp pills')} for inventory", color=ctx.user.color)
            embedVar.add_field(name="Pill:", value=pill.display_name, inline=False)
            embedVar.add_field(name="Amount:", value=amount)
            embedVar.add_field(name="In inventory:", value=user.items[pill])
            await ctx.channel.send(embed=embedVar)
            self.saveFile()

    def getTemp(self):
        w = mgr.weather_at_place(location).weather #TODO try except cuz this crashes whole code
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
            self.logger.debug(f"{interaction.user} is holding in {interaction.guild}")
        else:
            await interaction.send(f"You are now holding your own pp. Umm... I don't know what for but to be honest i don't even wanna know. \nNo effect is in place.", ephemeral=True)
            self.logger.debug(f"{interaction.user} is holding self lolololol")

    @discord.slash_command(name="ppp", description="For measuring your pp.", dm_permission=False)
    async def ppp(self, ctx: discord.Interaction):
        pass

    @ppp.subcommand(name="daily", description="Collect your daily pills")
    async def daily(self, ctx: discord.Interaction):
        user = self.getUserFromDC(ctx.user)
        try:
            self.logger.debug(f"user daily date {user.dailyDate}")
            if type(user.dailyDate) == datetime:
                user.dailyDate = user.dailyDate.date()
        except AttributeError as e:
            self.logger.error(e)  # TODO if does not come up, remove this #yes should not happen
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
                self.logger.warning(f"something is wrong {user.dailyDate}, {date.today()}, {user.dailyDate - date.today()}")
                return
            await ctx.send(embed=embedVar)
            user.dailyDate = datetime.now().date()
            await self.addPill(ctx, user, pills[0], random.randint(1, 3))  # yellow pill
            if user.dailyStreak >= random.randint(0, 99):
                await self.addPill(ctx, user, pills[1], random.choices((1, 2), weights=(0.8, 0.2))[0])  # red pill
            if user.dailyStreak / 10 >= random.randint(0, 99):
                await self.addPill(ctx, user, pills[2], 1)  # blue pill
                if "lucky_draw" not in user.achi:
                    await self.updateUserAchi(ctx, ctx.user, "lucky_draw")
            #self.saveFile() saving happens in addpill() too

    @ppp.subcommand(name="max", description="Leaderboard of biggest pps")
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
            except (ValueError, AttributeError):
                user = i[0]
            embedVar.add_field(name=user, value=f"{i[1]} cm {'total' if server == 'Between servers' else ''}", inline=False)
        await ctx.send(embed=embedVar)

    @ppp.subcommand(name="min", description="Leaderboard of smallest pps")
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
            except (ValueError, AttributeError):
                user = i[0]
            embedVar.add_field(name=user, value=f"{i[1]} cm {'total' if server == 'Between servers' else ''}", inline=False)
        await ctx.send(embed=embedVar)

    @ppp.subcommand(name="weather", description="See how your pp is affected at the moment.")
    async def weather(self, ctx, location: str = discord.SlashOption(name="city", description="City name, for extra precision add a comma and a country code e.g. London,UK",required=False)):
        await ctx.response.defer()
        self.getTemp()
        offset = ((7 - abs(7 - datetime.now().month)) - 1) * 3  # average temperature okolo ktorej bude pocitat <zcvrk alebo rast> #TODO Greenwich
        embedVar = discord.Embed(title=f"It´s {self.temperature} degrees in Bratislava.", description="You can expect {} {} pps".format(("quite", "slightly")[int(abs(self.temperature - offset) < 5)],("shorter", "longer")[int(self.temperature - offset > 0)]), color=(0x17dcff if self.temperature < offset - 5 else 0xbff5ff if self.temperature <= offset else 0xff3a1c if self.temperature > offset + 5 else 0xffa496 if self.temperature > offset else ctx.user.color))
        offsettime = self.sunrise_date.astimezone(pytz.timezone("Europe/Vienna"))
        embedVar.add_field(name="And the sun is coming up at", value="{}:{:0>2}.".format(offsettime.hour, offsettime.minute))
        await ctx.send(embed=embedVar)

    @ppp.subcommand(name="tips", description="Read some tips on how to increase your pp size")
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
        def __init__(self, user: PipikUser, cog):
            self.user = user
            self.cog = cog
            pillselect = [discord.SelectOption(label="Cancel", value="-1", emoji=emoji.emojize(":cross_mark:"))] #TODO please migrate to a dict alredy so i dont have to juggle these *which* values and remove the enum
            for pill, amount in [(pill, amount) for pill, amount in self.user.items.items() if pill != pills[-1] and amount >= 10]:
                pillselect.append(discord.SelectOption(label=pill.display_name, value=f"{pill.name}", description=f"in inventory: {amount}"))
            super().__init__(placeholder="Select pills to crush up", options=pillselect)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user.id:
                if self.values[0] == "-1":
                    await interaction.response.edit_message(embed=discord.Embed(description="Cancelled.", color=interaction.user.color), view=None, delete_after=5.0)
                else:
                    pill = pills_dict[self.values[0]]
                    # amount = int(attr[2] or 1) #TODO: do multiselect again or just add it as options,# resend view with updated dropdown options? but then need to edit msg too, then take it out into a different function
                    amount = 1
                    if self.user.items[pill] >= 10:
                        self.user.items[pill] -= amount * 10
                        if "breaking_bad" not in self.user.achi:
                            await self.cog.updateUserAchi(interaction, interaction.user, "breaking_bad") #moved this up so achi adding happens before savefile gets called in addpill
                        await self.cog.addPill(interaction, self.user, pills[(pills.index(pill)) + 1], amount)
                        embedVar = discord.Embed(description=f"You crushed up 10 {pill.display_name}", color=interaction.user.color)
                        await interaction.response.edit_message(embed=embedVar, view=None)
                        if self.user.items[pill] == 0:
                            del (self.user.items[pill])
                    else: #TODO remove this shouldnt be possible
                        self.cog.pipikLogger.warning(f"{interaction.user} with {self.user.items} wanted to craft up 10 {pill.display_name}")

            else:
                await interaction.send(f"This is not your prompt, use {mentionCommand(self.cog.client,'ppp pills')} to use your pills.", ephemeral=True) # i won't bother embedizing

    class PillsButtonsConsume(discord.ui.Button):
        def __init__(self, user: PipikUser, cog):
            self.user = user
            self.cog = cog
            canConsume = len(user.items) != 0 and not self.user.pill
            super().__init__(label="Consume", disabled=not canConsume, style=discord.ButtonStyle.gray, emoji=emoji.emojize(":face_with_hand_over_mouth:"))

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.send(f"This is not your inventory, use {mentionCommand(self.cog.client,'ppp pills')} to see your pills.", ephemeral=True) #neither this
                return
            # self.style = discord.ButtonStyle.green
            # for child in self.view.children:
            #     child.disabled = True
            # await interaction.response.edit_message(view=self.view)
            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.PillTakeDropdown(self.user, self.cog))
            await interaction.message.edit(embed=discord.Embed(title="Pill consumption", color=interaction.user.color), view=viewObj)

    class PillsButtonsCraft(discord.ui.Button):
        def __init__(self, user: PipikUser, cog):
            self.user = user
            self.cog: PipikBot = cog
            canCraft = any((amount >= 10 for pill,amount in user.items.items()))
            super().__init__(label="Craft", disabled=not canCraft, style=discord.ButtonStyle.gray, emoji=emoji.emojize(":hammer:"))

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.send(f"This is not your inventory, use {mentionCommand(self.cog.client,'ppp pills')} to see your pills.", ephemeral=True)
                return

            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.PillCraftDropdown(self.user, self.cog))
            await interaction.message.edit(embed=discord.Embed(title="Pill crafting", color=interaction.user.color), view=viewObj)

    class PillTakeDropdown(discord.ui.Select):
        def __init__(self, user: PipikUser, cog):
            self.user = user
            self.cog = cog
            pillselect = ([discord.SelectOption(label=pill.display_name, value=pill.name, description=f"in inventory: {amount}")
                           for pill, amount in self.user.items.items() if amount > 0] +
                          [discord.SelectOption(label="Cancel", value="-1", emoji=emoji.emojize(":cross_mark:"))])

            super().__init__(placeholder="Select a pill to consume", options=pillselect)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user.id:
                if self.values[0] == "-1":
                    await interaction.response.edit_message(content="Cancelled.", embed=None, view=None, delete_after=5.0)
                else:
                    pill = pills_dict[self.values[0]]
                    await interaction.response.edit_message(content=None,
                                                            embed=discord.Embed(
                                                                title=f"You took a {pill.display_name}",
                                                                description="Now go measure your pp before it wears out!",
                                                                color=interaction.user.color),
                                                            view=None)
                    if "pill_popper" not in self.user.achi:
                        await self.cog.updateUserAchi(interaction, interaction.user, "pill_popper") #moved this above takepill so achi adding happens before savefile gets called
                    await self.user.takePill(pill, self.cog)

            else:
                await interaction.send(f"This is not your prompt, use {mentionCommand(self.cog.client,'ppp pills')} to use your pills.",ephemeral=True)

    @ppp.subcommand(description="See, manage and use your pill inventory.")
    async def pills(self, ctx): # TODO the buttons, and their views and their actions of eating and crafting should edit the original message, not send a new one
        user = self.getUserFromDC(ctx.user)
        sortedpills = sorted(user.items.keys(), key=lambda pill: pills.index(pill))
        sortedpills = {pill : user.items[pill] for pill in sortedpills}
        user.items = sortedpills

        text = "```py\n"
        text += ("Pills".center(25) + "\nCrafting takes 10 pills and crafts a better quality one\nBetter pills equals bigger pps\nExcessive use might result in impotency!\n{:-^25}\n".format("-"))
        text += "\n".join([f"{pill.display_name:<15} ({pill.effectDur.seconds//60:<2} min)| amount: {amount}" for pill, amount in user.items.items()])
        if len(user.items) == 0:
            text += f"You have no pills. Use {mentionCommand(self.client,'ppp daily')} to get some!"
        text += "\n```"

        if user.pill:
            self.logger.debug(f"uh oh pill already in you {user.pill}")
            takenAgo = datetime.now() - user.pillPopTime
            if takenAgo < user.pill.effectDur + user.pill.badEffectDur:
                self.logger.debug("has not expired")
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
                await interaction.send(f"This is not your button, use your own by using {mentionCommand(self.cog.client,'ppp fap')}", ephemeral=True)
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

    @ppp.subcommand(name="fap", description="Increase your pp length by repeatedly mashing a button.")
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

    @ppp.subcommand(name="profile", description="See your, or someone else's pp profile") #oh my god this is ugly
    async def profile(self, ctx: discord.Interaction, user: discord.User = discord.SlashOption(name="user", description="User to display", required=False)):
        usertocheck = user or ctx.user
        user = self.getUserFromDC(usertocheck)
        takenAgo = timedelta(seconds=0)
        dysf_left = timedelta(seconds=0)

        if user.pill not in (None, "None", "none"): # should not happen but json is json
            if user.pill in ("None", "none"): # this really should not happen
                user.pill: Pill | None = None
            takenAgo = datetime.now() - user.pillPopTime
            self.logger.debug(user.pill)
            if takenAgo > user.pill.effectDur:
                badEffectStart = user.pillPopTime + user.pill.effectDur
                user.cd = datetime.now() + user.pill.badEffectDur - (datetime.now() - badEffectStart)
                if takenAgo > user.pill.effectDur + user.pill.badEffectDur:
                    user.pill = None

        if user.cd is not None:
            if user.cd == 0 or user.cd - datetime.now() < timedelta(seconds=0):
                user.cd = None
            else:
                dysf_left = user.cd - datetime.now()

        temphorniness = (user.fap + user.pill.effect) if user.pill not in (None, "None", "none") else 0
        sortedpills = sorted(user.items.keys(), key=lambda pill: pills.index(pill))
        sortedpills = {pill: user.items[pill] for pill in sortedpills}
        user.items = sortedpills

        text = usertocheck.name.center(25, "=")
        text += f"\nPersonal best: {user.pb}\nPersonal worst: {user.pw}\n"
        text += f"Horniness: {temphorniness}\n" if user.cd is None else ""
        text += f"Pill: {user.pill.display_name} | {(((user.pill.effectDur - takenAgo).seconds // 60) + 1)} minutes left.\n" if user.pill else ""
        text += "Erectyle disfunction: {} hours {} minutes\n".format(dysf_left.seconds // 3600, (dysf_left.seconds // 60 % 60) + 1) if user.cd is not None else ""
        text += "{:-^25}".format("Items") + "\n"
        text += "\n".join([f"{pill.display_name:<20} | amount: {amount}" for pill, amount in user.items.items()])
        text += "\n{:-^25}\n".format("Achievements")
        text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) for achi in self.achievements.values())
        text += "\n" + "{:-^25}".format("-")
        await ctx.send("```\n" + text + "\n```" + f"for more info, try {mentionCommand(self.client,'ppp achi')}") #lord forgive me for what ive done

    @ppp.subcommand(name="achi", description="See your achievements")
    async def achi(self, ctx): #TODO let ppl see others achis but reveal only the ones they have
        user = self.getUserFromDC(ctx.user)
        text = "Your achievements".center(60, "=")+"\n"
        text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) + (("= " + achi.desc) if achi.achiid in user.achi else "= ???") for achi in self.achievements.values())
        await ctx.send("```\n" + text + "\n```", ephemeral=True)

    @discord.slash_command(name="pp", description="For measuring your pp.", dm_permission=False)
    async def pp(self, ctx: discord.Interaction, message: str = discord.SlashOption(name="message", description="Would you like to tell me something?", required=False, default=None)):
        await ctx.response.defer()
        msg = None
        embedMsg = discord.Embed(description=".", color=ctx.user.color)  # placeholders
        user = self.getUserFromDC(ctx.user)
        currmethods = 0  # this is for keeping track of what pp enlargement methods were used. Im gonna perform bitwise operations on this
        self.logger.debug(f"{datetime.now() - self.weatherUpdatedTime}, weatherupdatetimer, how long ago was updated")
        if datetime.now() - self.weatherUpdatedTime > timedelta(hours=1):
            self.logger.debug("updating temp")
            self.getTemp()
        else:
            self.logger.debug("temp up to date")

        curve = 2
        multiplier = 100

        # pill checker
        if user.pill and user.pill not in (None, "none", "None"):  # fucking inconsistent
            takenAgo = datetime.now() - user.pillPopTime
            self.logger.debug(user.pill)
            if takenAgo < user.pill.effectDur:
                currmethods = currmethods | 32
                curve -= user.pill.effect / 15
                multiplier += user.pill.effect
            elif takenAgo < user.pill.effectDur + user.pill.badEffectDur:
                badEffectStart = user.pillPopTime + user.pill.effectDur
                user.cd = datetime.now() + (user.pill.badEffectDur - (datetime.now() - badEffectStart))
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
        self.logger.debug(f"morning wood check, {self.sunrise_date}, sunrise date (gmt) # {sunrise}, until sunrise {datetime.now(tz_info)}, current time (gmt)")
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
                embedMsg = discord.Embed(description=f"Heya {ctx.user.display_name}! \\\(^.^)/", color=ctx.user.color)
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
                        self.logger.debug(f"found {word} in {message}")
                        compliments += 1
                # for word in bad_words:
                #     if word in message.casefold():
                #         compliments -= 1
                self.logger.debug(f"{compliments=}")
                self.logger.debug("\n".join([str(i) for i in zip(message.split(" "), profanity_check.predict(message.split(" ")))]))
                compliments -= list(profanity_check.predict(message.split(" "))).count(1)

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
                embedMsg.add_field(name=random.choice(duplicate_responses), value=emoji.emojize(random.choice(bad_emojis)), inline=False)


        # temperature adjustment
        pocasieOffset = ((7 - abs(7 - datetime.now().month)) - 1) * 3  # average temperature okolo ktorej bude pocitat <zcvrk alebo rast> #TODO make this dynamic and global to whole world
        if self.temperature > pocasieOffset + 5:
            currmethods = currmethods | 4
        curve -= (self.temperature - pocasieOffset) / 20
        multiplier += self.temperature - pocasieOffset

        #moon phase checker
        if int(moon.phase()) in range(14, 21):
            multiplier += 10
            curve -= 0.1
            currmethods = currmethods | 64

        # holding checker
        try:
            self.logger.debug(f"holdings table {self.holding} curr server {ctx.guild.id}, author {ctx.user.id}")
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
                    await self.updateUserAchi(ctx, ctx.user, "helping_hands")  # holding achis
                if "friend_need" not in holderpp.achi:
                    await self.updateUserAchi(ctx, holder, "friend_need")
            del self.holding[ctx.guild.id]
        except KeyError as e: #redundant
            self.logger.debug(str(e) + " - in this guild noone is holding anything")

        # final calculation
        if curve < 0:
            self.logger.warning(25 * "#" + "uh oh stinky")
            curve = -curve * 0.01
        pipik = round((random.expovariate(curve) * multiplier), 3)
        self.logger.debug(f"{ctx.user.display_name}, {pipik=}, {curve=}, {multiplier=}, {compliments=}, {self.temperature=}, {user.fap=}, {user.cd=}")

        # personal record checker
        if pipik > user.pb:
            await self.updateUserStats(user, "pb", pipik)
        if not user.pw or pipik < user.pw:
            await self.updateUserStats(user, "pw", pipik)

        # rekord checker
        try:
            self.logger.debug(f"this server´s leaderboard {self.leaderboards[str(ctx.guild_id)]}")
        except KeyError:
            self.leaderboards[str(ctx.guild_id)] = []
        if len(self.leaderboards[str(ctx.guild_id)]) > 4 and len(self.loserboards[str(ctx.guild_id)]) > 4:  # if leaderboard fully populated go check if the new measurement is better,
            if pipik > self.leaderboards[str(ctx.guild_id)][0][1] or pipik < self.loserboards[str(ctx.guild_id)][0][1]: # otherwise just automatically populate it on the leaderboard without announing a record
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
                await self.updateUserAchi(ctx, ctx.user, "megapp")
        elif pipik < 0.5:
            if "micropp" not in user.achi:
                await self.updateUserAchi(ctx, ctx.user, "micropp")
        elif 69 <= pipik < 70:
            if "nice" not in user.achi:
                await self.updateUserAchi(ctx, ctx.user, "nice")

        # pp enlargement methods achi checker
        try:
            user.methods
        except KeyError:
            user.methods = 0
        if currmethods == 127 and "desperate" not in user.achi:
            await self.updateUserAchi(ctx, ctx.user, "desperate")
        if currmethods | user.methods != user.methods:
            await self.updateUserStats(user, "methods", user.methods | currmethods)
        if user.methods == 127 and "tested" not in user.achi:
            await self.updateUserAchi(ctx, ctx.user, "tested")

        # final printer
        footertext = f'{emoji.emojize(":handshake:",language="alias") if currmethods & 1 else ""}{emoji.emojize(":heart_eyes:",language="alias") if currmethods & 2 else ""}{emoji.emojize(":thermometer:",language="alias") if currmethods & 4 else ""}{emoji.emojize(":sunrise:",language="alias") if currmethods & 8 else ""}{emoji.emojize(":fist:",language="alias") if currmethods & 16 else ""}{emoji.emojize(":pill:",language="alias") if currmethods & 32 else ""}{emoji.emojize(":waning_gibbous_moon:",language="alias") if currmethods & 64 else ""}'
        embedMsg.title = f"*{ctx.user.display_name}* has **{pipik}** cm long pp!"
        embedMsg.description = str("o" + (min(4094, (int(pipik) // 10)) * "=") + "3")
        embedMsg.set_footer(text=footertext, icon_url=ctx.user.avatar.url)
        embedMsg.timestamp = datetime.now()
        if msg:
            await msg.edit(embed=embedMsg)
        else:
            await ctx.send(embed=embedMsg)


def setup(client):
    client.add_cog(PipikBot(client))
