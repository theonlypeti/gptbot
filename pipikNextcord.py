import sys
import nextcord as discord
import random
from nextcord.ext import commands
import asyncio
from datetime import datetime, date, timedelta
import json
from copy import deepcopy
import pyowm
import pytz
import unicodedata
import emoji
import os
import argparse
import time as time_module
import logging
from dotenv import load_dotenv

start = time_module.perf_counter()

load_dotenv(r"./credentials/main.env")
parser = argparse.ArgumentParser(prog="PipikBot V3.2",description='A fancy discord bot.',epilog="Written by theonlypeti.")
parser.add_argument("--minimal",action="store_true",help="Disable most of the extensions.")
parser.add_argument("--debug",action="store_true",help="Enable debug mode.")
parser.add_argument("--no_gifsaver",action="store_true",help="Disable gif saver module.")
parser.add_argument("--no_ais",action="store_true",help="Disable ais témy module.")
parser.add_argument("--no_radio",action="store_true",help="Disable radio module.")
parser.add_argument("--no_wordle",action="store_true",help="Disable wordle module.")
parser.add_argument("--no_zssk",action="store_true",help="Disable zssk module.")
parser.add_argument("--no_maths",action="store_true",help="Disable maths module.")
parser.add_argument("--no_fujkin",action="store_true",help="Disable fujkin module.")
parser.add_argument("--no_rpg",action="store_true",help="Disable rpg module.")
parser.add_argument("--no_clovece",action="store_true",help="Disable clovece module.")
parser.add_argument("--no_topic",action="store_true",help="Disable topic module.")
parser.add_argument("--no_currency",action="store_true",help="Disable currency exchange module.")
parser.add_argument("--no_testing",action="store_true",help="Disable testing module.")
args = parser.parse_args()

pipikLogger = logging.getLogger("PipikBot")
ch = logging.StreamHandler()
#ch = logging.FileHandler("pipikLog.txt")
if args.debug:
    pipikLogger.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)
else:
    pipikLogger.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)
pipikLogger.addHandler(ch)

if not args.minimal and not args.no_maths:
    import MyScripts.matstatMn
    prikazy = list(filter(lambda a: not a.startswith("_"), dir(MyScripts.matstatMn)))
    [prikazy.remove(i) for i in ("lru_cache", "graf", "plt", "prod", "kocka", "minca", "napoveda")]

    from MyScripts.matstatMn import *
    from utils.bf import *

root = os.getcwd()  # "F:\\Program Files\\Python39\\MyScripts\\discordocska\\pipik"

protocol = False
spehmode = True
already_checked = []

# TODO play with this @commands.has_permissions(manage_server=True)
# TODO colored ansi text
# TODO video.py
# TODO json module has parse_int inside it
# TODO orjson
# TODO add modal to pill taking and crafting asking how many to use
# TODO continue the gifsaver add a normal command without reply
# TODO properly integrate matstat stuff
# TODO make emojis for pills
# TODO make a better help command
# TODO line counter for the utils
# TODO implement anti compliment stealing
# TODO pyowm onecall api has a moon phase attr!!!!!!!! but only 1000 calls/day
# TODO redo the leaderboards because i am storing a pair of (user, score) in a list lol, actually not even a user, but only their name
# TODO make pipikbot users a dict of id:user instead of a list of users, also redo the getUserFromDC func then
# TODO make an actual lobby extension

def antimakkcen(slovo):  # it just works
    normalized = unicodedata.normalize('NFD', slovo)
    slovo2 = u"".join([c for c in normalized if not unicodedata.combining(c)])
    return slovo2

intents = discord.Intents.all() #TODO remember what do i use members intent for?!?!! update: members is used when checking if guild is premium for example
intents.presences = False

client = commands.Bot(command_prefix='&', intents=intents,chunk_guilds_at_startup=True) #TODO chunk_guilds_at_startup=False might help me
client.remove_command('help')
owm = pyowm.OWM(os.getenv("OWM_TOKEN"))
location = 'Bratislava,sk'
mgr = owm.weather_manager()

#T9 = ({key * i: letter for i, key, letter in zip([(num % 3) + 1 for num in range(0, 26)], [str(q // 3) for q in range(6, 30)],sorted({chr(a) for a in range(ord("A"), ord("Z") + 1)} - {"S", "Z"}))} | {"7777": "S", "9999": "Z","0": " "})
#T9rev = {v: k for k, v in T9.items()}

##@client.message_command(name="T9ize",guild_ids=[860527626100015154])
##async def t9(interaction, text):
##    await interaction.send(" ".join([T9rev[letter.upper()] for letter in text.content]))
##
##@client.message_command(name="T9rev",guild_ids=[860527626100015154])
##async def t9r(interaction, text):
##    await interaction.send("".join([T9[letters] for letters in text.content.split(" ")]))

@client.message_command(name="En-/Decrypt")
async def caesar(interaction, text):
    if text.type == discord.MessageType.chat_input_command and text.embeds[0].title == "Message":
        text = text.embeds[0].description
    else:
        text = text.content
    await interaction.send("".join([chr(((ord(letter) - 97 + 13) % 26) + 97) if letter.isalpha() and letter.islower() else chr(((ord(letter) - 65 + 13) % 26) + 65) if letter.isalpha() and letter.isupper() else letter for letter in text]))

class CaesarModal(discord.ui.Modal):
    def __init__(self, title):
        super().__init__(title=title)
        self.inputtext = discord.ui.TextInput(label="Input the text",style=discord.TextInputStyle.paragraph)
        self.add_item(self.inputtext)

    async def callback(self, ctx):
        text = self.inputtext.value
        textik = ("".join([chr(((ord(letter) - 97 + 13) % 26) + 97) if letter.isalpha() and letter.islower() else chr(((ord(letter) - 65 + 13) % 26) + 65) if letter.isalpha() and letter.isupper() else letter for letter in text]))
        embedVar = discord.Embed(title="Message", type="rich", description=textik)
        embedVar.set_author(name=ctx.user.display_name, icon_url=ctx.user.avatar.url)
        await ctx.send(embed=embedVar)

@client.slash_command(description="Encrypt/Decrypt", name="caesar")
async def caesar_modal(ctx):
    modal = CaesarModal(title="ROT13 cypher")
    await ctx.response.send_modal(modal)

class BfModal(discord.ui.Modal):
    def __init__(self, title):
        super().__init__(title=title)
        self.codetext = discord.ui.TextInput(label="Input the code", style=discord.TextInputStyle.paragraph,default_value="+[-->-[>>+>-----<<]<--<---]>-.>>>+.>>..+++[.>]<<<<.+++.------.<<-.>>>>+.")
        self.add_item(self.codetext)

        self.inputtext = discord.ui.TextInput(label="input from user (if any)", required=False,style=discord.TextInputStyle.paragraph, placeholder="123")
        self.add_item(self.inputtext)

    async def callback(self, ctx):
        output = bf(self.codetext.value, self.inputtext.value)
        embedVar = discord.Embed(title="Brainfuck", type="rich", description=output)
        embedVar.set_author(name=ctx.user.display_name, icon_url=ctx.user.avatar.url)
        await ctx.send(embed=embedVar)

@client.slash_command(description="Brainfuck interpreter",name="brainfuck")
async def bf_modal(ctx):
    modal = BfModal(title="Brainfuck")
    await ctx.response.send_modal(modal)

@client.slash_command(name="pfp", description="chooses a random emote for the servers profile pic.",guild_ids=[860527626100015154],dm_permission=False)
async def pfp(interaction: discord.Interaction):
    os.chdir("D:\\Users\\Peti.B\\Pictures\\microsoft\\emotes")
    emotes = [emote for emote in os.listdir() if not emote.endswith(".gif") or interaction.guild.premium_tier]
    await interaction.send(f"Picking from {len(emotes)} emotes...")
    img = random.choice(emotes)
    print(img)
    with open(img, "rb") as file:
        await interaction.guild.edit(icon=file.read())
    os.chdir(root)

@client.slash_command(name="time", description="/time help for more info")
async def time(ctx,
               time:str =discord.SlashOption(name="time", description="Y.m.d H:M or H:M or relative (minutes=30 etc...)"),
               arg:str = discord.SlashOption(name="format", description="raw = copypasteable, full = not relative", required=False,choices=["raw", "full", "raw+full"]),
               message:str =discord.SlashOption(name="message",description="Your message to insert the timestamp into, use {} as a placeholder",required=False)):
    try:
        if "." in time and ":" in time:  # if date and time is given
            timestr = datetime.strptime(time, "%Y.%m.%d %H:%M")
        elif "H:M" in time:
            await ctx.send("Nono, you need to input actual TIME in there not the string H:M")
            return
        elif ":" in time:  # if only time is given
            timestr = datetime.now().replace(**{"hour": int(time.split(":")[0]), "minute": int(time.split(":")[1]),"second": 0})  # i could have done strptime %H:%M but it would have given me a 1970 date
        elif "=" in time:  # if relative
            timestr = datetime.now() + timedelta(**{k.strip(): int(v.strip()) for k, v in [i.split("=") for i in time.split(",")]})
        else:  # if no time is given
            embedVar = discord.Embed(title="Timestamper", description="Usage examples", color=ctx.user.color)
            embedVar.add_field(name="/time 12:34", value="Today´s date with time given")
            embedVar.add_field(name="/time 2022.12.31 12:34", value="Full date format")
            embedVar.add_field(name="/time hours=1,minutes=30", value="Relative to current time")
            embedVar.add_field(name="optional arg: raw/full/raw+full",value="raw= Copy pasteable timestamp\nfull= Written out date instead of relative time")
            embedVar.add_field(name="optional message:", value="Brb {}; Meeting starts at {} be there!")
            await ctx.send(embed=embedVar)
            return
        if arg and arg == "raw":
            timestr = "`<t:" + str(int(timestr.timestamp())) + ":R>`"
        elif arg and arg == "raw+full":
            timestr = "`<t:" + str(int(timestr.timestamp())) + ":F>`"
        elif arg and arg == "full":
            timestr = "<t:" + str(int(timestr.timestamp())) + ":F>"
        else:
            timestr = ("<t:" + str(int(timestr.timestamp())) + ":R>")

        await ctx.send(
            message.format(timestr) if message and "{}" in message else f"{message} {timestr}" if message else timestr)
    except Exception as e:
        await ctx.send(e)

#@client.slash_command(name="muv", description="semi", guild_ids=[860527626100015154, 601381789096738863])
#async def movebogi(ctx, chanel: discord.abc.GuildChannel):
#    await ctx.user.move_to(chanel)

# @client.slash_command(name="muvraw", description="semi", guild_ids=[860527626100015154, 601381789096738863])
# async def movebogi2(ctx, chanel):
#     chanel = ctx.guild.get_channel(int(chanel))
#     await ctx.user.move_to(chanel)

@client.message_command(name="Unemojize")
async def unemojize(interaction, message):
    await interaction.response.send_message(f"`{emoji.demojize(message.content)}`",ephemeral=True)

@client.message_command(name="Spongebob mocking")  # pelda jobbklikk uzenetre commandra
async def randomcase(interaction, message):
    assert message.content
    await interaction.send("".join(random.choice([betu.casefold(), betu.upper()]) for betu in message.content) + " <:pepeclown:803763139006693416>")

class ReactSelect(discord.ui.Select):
    def __init__(self, message):
        self.optionen = []
        self.message = message
        for k in ["same", "mood", "true", "kekw", "kekno", "kekfu", "kekwait", "kekcry", "kekdoubt", "tiny","peepoheart", "tired", "jerrypanik", "hny", "minor_inconvenience", "doggo", "funkyjam", "business","business2", "tavozz", "concern", "amusing", "ofuk","ohgod"]:  # populating the select component with options
            self.optionen.append(discord.SelectOption(label=k,value=discord_emotes[k],emoji=discord_emotes[k]))
        super().__init__(placeholder="Select an emote", options=self.optionen)

    async def callback(self, interaction):
        def check(reaction, user):
            return not user.bot

        await self.message.add_reaction(self.values[0])
        reaction, user = await client.wait_for('reaction_add', timeout=6.0, check=check)
        await self.message.remove_reaction(self.values[0], client.user)

@client.message_command(name="Add reaction")
async def react(interaction, message):
    viewObj = discord.ui.View()
    viewObj.add_item(ReactSelect(message))
    await interaction.send("Dont forget to click the react yourself too! Also spamming emotes might trip up the anti-spam filter.",ephemeral=True, view=viewObj)

@client.command()
async def initiatespeh(ctx):
    global spehmode
    spehmode = not spehmode
    print("speh initiated")

@client.slash_command(name="run", description="For running python code")
async def run(ctx, command):
    if "@" in command and ctx.user.id != 617840759466360842:
        await ctx.send("oi oi oi we pinging or what?")
        return
    if any((word in command for word in ("open(","os.","eval(","exec("))) and ctx.user.id != 617840759466360842:
        await ctx.send("oi oi oi we hackin or what?")
        return
    elif "redditapi" in command and ctx.user.id != 617840759466360842:
        await ctx.send("Lol no sorry not risking anyone else doing stuff with MY reddit account xDDD")
        return
    try:
        async with ctx.channel.typing():
            a = eval(command)
        await ctx.send(a)
    except Exception as a:
        await ctx.send(a)

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
                 "Too long, didn't read xd")

discord_emotes = {}
good_emojis = (':smiling_face_with_hearts:', ':smiling_face_with_heart-eyes:', ':face_blowing_a_kiss:', ':kissing_face:',':kissing_face_with_closed_eyes:')
bad_emojis = (':rolling_on_the_floor_laughing:', ':cross_mark:', ':squinting_face_with_tongue:', ':thumbs_down:')
good_words = {"affectionate", "admirable", "charm", "creative", "friend", "funny", "generous", "kind", "likable","loyal", "polite", "sincere", "pretty", "please", "love", "goodnight", "nite", "prett", "kind", "sugar","clever", "beaut", "star", "heart", "my", "wonderful", "legend", "neat", "good", "great", "amazing","marvelous", "fabulous", "hot", "best", "birthday", "bday", "ador", "cute", " king", "queen", "master","daddy", "lil", "zlat", "bby", "angel", "god", "cool", "nice", "lil", "marvelous", "magnificent", "cutie","handsome"}
bad_words = {"adopt", "dirt", "die", "kill", "cring", "selfish", "ugly", "dick", "small", "devil", "drb", "ass","autis", "deranged", "idiot", "cock", "cut", "d1e", "fuck", "slut", "d13", "fake", "a55", "retard","r3tard", "tard", "bitch", "nigga", "nibba", "nazi", "jew", "fag", "f4g", "feg", "feck", "pussy", "pvssy","stink", "smell", "stupid"}
pills = [{"name": "\U0001F48A Size Up Forte", "effect": 5, "effectDur": timedelta(minutes=5), #TODO make custom emojis
          "badEffectDur": timedelta(seconds=0)},
         {"name": "\U0001F608 Clavin Extra", "effect": 10, "effectDur": timedelta(minutes=20), #TODO make into class
          "badEffectDur": timedelta(minutes=20)},
         {"name": "\U0001F535 Viagra XXL", "effect": 15, "effectDur": timedelta(minutes=60),
          "badEffectDur": timedelta(hours=2, minutes=30)}]

default_achievements = (
("morning", emoji.emojize(':sunrise_over_mountains:'), "Morning wood", "Measure your pp in the morning"),
("one_pump", emoji.emojize(':raised_fist:'), "One pump champ", "Relapse after just one pump"),
("micropp", emoji.emojize(':pinching_hand:'), "MicroPP", "Get a measurement of <0.5cm"),
("megapp", emoji.emojize(":hugging_face:", language="alias", variant="emoji_type"), "MegaPP","Get a measurement of >300cm"),
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
("contributor", emoji.emojize(':star:'), "Contributor","Aid development with ideas, offering help with gramatical errors, translations or reporting bugs and errors"))

class Achievement(object):
    """achievement object
icon = emoji
shorthand = id string to save
name = displayname in profile
desc = description in DMs
"""
    def __init__(self, achi):
        if type(achi) == tuple:
            for k, v in zip(("achiid", "icon", "name", "desc"), achi):
                setattr(self, k, v)

    def __str__(self):
        return f"{emoji.emojize(self.icon, language='alias')} {self.name}"

@client.event
async def on_ready(): #TODO move shit out of on_ready to pipikbot __init__
    global pipikbot
    pipikbot: discord.ext.commands.cog = client.get_cog("PipikBot")  # todo deprecate the global?
    game = discord.Game(f"{linecount} lines of code; V3.0! use /help")
    await client.change_presence(status=discord.Status.online, activity=game)
    print(f"Signed in {datetime.now()}")
    pipikLogger.debug(f"{time_module.perf_counter() - start} Bootup time")

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
        self.fap = 0
        self.achi = []
        self.items = []
        self.pb = 0
        self.pw = 0
        self.cd = None
        self.methods = 0
        self.pill = None
        self.pillPopTime = timedelta()
        self.dailyStreak = 0

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, PipikUser):
            return self.id == other.id
        else:
            raise NotImplemented(f"Comparsion between {type(self)} and {type(other)}")

    def __str__(self):
        return f"[{str(self.id)} with {str(len(self.achi))} achis; {str(self.dailyStreak)} streak; {str(self.pb)} pb and {str(self.methods)} methods]"

    async def takePill(self, which):
        self.pill = self.items[which][0]
        self.pillPopTime = datetime.now()
        self.items[which][1] -= 1
        if self.items[which][1] == 0:
            del (self.items[which])
        pipikbot.saveFile()

    async def updateUserAchi(self, ctx, achi,name=None):  # TODO: look into this? overengineered? Im sure theres some reason for this but idk what. Yes but im way too lazy to do that
        self.achi.append(achi)
        user = name or ctx.user.display_name
        achi = pipikbot.achievements[achi]
        await ctx.channel.send(embed=discord.Embed(title=f"{user} just got the achievement:", description=str(achi),color=discord.Colour.gold()))
        pipikbot.saveFile()

class PipikBot(commands.Cog): #TODO: move this into a separate cog file
    def __init__(self, member):
        self.usedcompliments = {"placeholder",}
        self.client = member
        self.temperature = 0
        self.holding = {}
        self.weatherUpdatedTime = datetime.now()
        self.leaderboards = {}
        self.loserboards = {}
        self.sunrise_date = datetime.now() #just a placeholder, it gets actually rewritten
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
                    pipikLogger.debug(f"found and ignored duplicate entry with id: {newUser.id}")
            pipikLogger.debug(self.users)

        self.readEmotes()

    def updateLeaderBoard(self, ldb, name, value):
        try:
            self.leaderboards[str(ldb)]
        except KeyError:
            self.leaderboards[str(ldb)] = []
        self.leaderboards[ldb].append((name, value))
        self.leaderboards[ldb].sort(key=lambda a: a[1], reverse=True)
        self.leaderboards[ldb] = self.leaderboards[ldb][:5]
        with open(root+"/data/pipikv3top.txt", "w") as file:
            json.dump(self.leaderboards, file, indent=4)

    def updateLoserBoard(self, ldb, name, value):
        try:
            self.loserboards[str(ldb)]
        except KeyError:
            self.loserboards[str(ldb)] = []
        self.loserboards[ldb] = self.loserboards[ldb][:5]  # needed because on_ready runs more times per login and loads the items more than once
        self.loserboards[ldb].append((name, value))
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
            except:
                pass
            tempusers.append(tempuser.__dict__)
        with open(root+"/data/pipikusersv3.txt", "w") as file:
            json.dump(tempusers, file, indent=4)
        pipikLogger.info("saved users")

    def saveSettings(self):
        settings = {"prefix": client.command_prefix, "temperature": self.temperature,"weatherUpdTime": self.weatherUpdatedTime.isoformat(), "sunrise": self.sunrise_date.isoformat()}
        with open(root+"/data/pipisettings.txt", "w") as file:
            json.dump(settings, file)
        pipikLogger.info("saved settings")

    def readSettings(self):
        with open(root+"/data/pipisettings.txt", "r") as file:
            settings = json.load(file)
        client.command_prefix = settings["prefix"]
        self.weatherUpdatedTime = datetime.fromisoformat(settings["weatherUpdTime"])
        if datetime.now() - self.weatherUpdatedTime > timedelta(hours=1):
            pipikLogger.debug("updating temp")
            self.getTemp()
        else:
            pipikLogger.debug("temp up to date")
            self.temperature = settings["temperature"]
            self.sunrise_date = datetime.fromisoformat(settings["sunrise"])

    def saveEmotes(self):
        with open(root+"/data/pipikemotes.txt", "w") as file:
            json.dump(discord_emotes, file, indent=4)
        pipikLogger.info("saved emotes")

    def readEmotes(self):
        global discord_emotes
        with open(root+"/data/pipikemotes.txt", "r") as file:
            discord_emotes = json.load(file)
        pipikLogger.info("loaded emotes")

    @commands.command()
    async def registerEmote(self, ctx, *attr):
        for emoji in attr:
            discord_emotes.update({emoji.split(":")[-2]: emoji})
        self.saveEmotes()

    @commands.command()
    async def registerAnimatedEmotes(self, ctx, howmany):
        howmany = int(howmany)
        for emoji in reversed(ctx.message.guild.emojis):
            if emoji.animated and howmany:
                howmany -= 1
                discord_emotes.update({emoji.name: f"<a:{emoji.name}:{emoji.id}>"})
        self.saveEmotes()

    @commands.command()
    async def reloadEmotes(self, ctx):
        self.readEmotes()

    def getUserFromDC(self, dcUser):
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

    async def getMsgFromLink(self, link):  #TODO: simplify, message can be get from only the channel
        link = link.split('/')
        server_id = int(link[4])
        channel_id = int(link[5])
        msg_id = int(link[6])
        server = client.get_guild(server_id)
        channel = server.get_channel(channel_id)
        message = await channel.fetch_message(msg_id)
        return message

    @client.slash_command(name="emote", description="For using special emotes")
    async def emote(self, ctx,emote=discord.SlashOption(name="emoji",description="An emoji name, leave blank if you want to list them all out.",required=False, default=None),
                    msg:str =discord.SlashOption(name="message_link",description="Use 'copy message link' to specify a message to react to.",required=False),
                    text:str = discord.SlashOption(name="text",description="The text message to send along with any emotes, use {emotename} as placeholder.",required=False, default=None)):
        def check(reaction, user):
            return not user.bot and (str(reaction.emoji) in list(discord_emotes.values()))

        pipikLogger.debug(f"{ctx.user}, {emote}, {datetime.now()}")
        if msg and emote:
            mess = await self.getMsgFromLink(msg)
            await mess.add_reaction(discord_emotes[emote])
            await ctx.send("Now go react on the message", ephemeral=True)
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=6.0, check=check)
            except asyncio.TimeoutError:
                pipikLogger.debug("emote timed out")
            finally:
                await mess.remove_reaction(discord_emotes[emote], client.user)
        elif text:
            try:
                text = text.replace("{", "{discord_emotes['")
                text = text.replace("}", "']}")
                text = eval(f'f"{text}"')
                await ctx.send(f"{text}")
            except Exception as e:
                pipikLogger.warning(e)
                await ctx.send(e,ephemeral=True)

        elif not emote:
            emotestr = ";".join([f"{v} {k}" for k, v in discord_emotes.items()])
            splitat = emotestr[4096::-1].index(";") #hehe this is a funny way to do it
            print(splitat)
            embedVar = discord.Embed(title="Emotes", description=emotestr[:4096-splitat], color=ctx.user.color)
            for i in range(4096-splitat, len(emotestr), 1024):
                embedVar.add_field(name=i, value=emotestr[i:min(i + 1024, len(emotestr))])
            embedVar.set_footer(text=f"{len(emotestr)} / 6000 chars in one message")
            await ctx.send(embed=embedVar, ephemeral=True)
            return
        else:
            await ctx.send(discord_emotes[emote])

    @emote.on_autocomplete("emote")
    async def emote_autocomplete(self, interaction, emote: str):
        if not emote:
            # send the full autocomplete list
            randomemotes = list(discord_emotes.keys())
            random.shuffle(randomemotes)
            await interaction.response.send_autocomplete(randomemotes[:25])
            return
        # send a list of nearest matches from the list of emotes
        get_near_emote = [i for i in discord_emotes.keys() if i.casefold().startswith(emote.casefold())]
        get_near_emote = get_near_emote[:25]
        await interaction.response.send_autocomplete(get_near_emote)

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
            embedVar = discord.Embed(title="You´ve got pills!", description="try /pills for inventory", color=colorEm)
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

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not ctx.author.bot:
            #if spehmode:
                #print("message at:",str(datetime.now()),"content:",ctx.content,"by:",ctx.author,"in:",ctx.channel.name)
            if "free nitro" in antimakkcen(ctx.content).casefold():
                await ctx.channel.send("bitch what the fok **/ban**")

    @client.user_command(name="Hold pp",dm_permission=False)
    async def holding(self,interaction,member):
        if interaction.user.id != member.id:
            await interaction.send(f"You are now holding {member.display_name}'s pp. This will be in effect until the next measurement done by anyone on this server.",ephemeral=True)
            self.holding.update({interaction.guild.id: interaction.user})
            pipikLogger.debug(f"{interaction.user} is holding")
        else:
            await interaction.send(f"You are now holding your own pp. Umm... I don't know what for but to be honest i don't even wanna know. \nNo effect is in place.",ephemeral=True)
            pipikLogger.debug(f"{interaction.user} is holding self lolololol")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user):
        global already_checked

        if str(reaction.emoji) in ("<:kekcry:871410695953059870>", "<:kekw:800726027290148884>"):
            if reaction.message.author.id == 569937005463601152:
                if user.id == 569937005463601152:
                    boci: discord.Member = reaction.message.author
                    already_checked.append(reaction.message.id)
                    await boci.timeout(timedelta(minutes=3), reason="Saját magára rakta a keket")
                    uzenet = "Imagine saját vicceiden nevetni. " + random.choice("<:cringe:644026740242645023> <:OhNoCringe:945225281172553760> <:cassiecringe:859589366870573106> <:SCCRINGE:664519482416300053> <:Catastrophe_CringeBro:645327316540456998> <:AntonCringe:690691883500044409> <a:cringesmiley:774412323662069770> <a:cringepepepet:773106637774913586> <:notcringebutwtf:600071034229751848> <:flushcringe:644026697880043570> <:pepe_cringe:774411918081261578>".split(" "))
                    await reaction.message.reply(uzenet)


        if reaction.emoji == emoji.emojize(":thumbs_down:"):
            if reaction.message.author.id == 569937005463601152:
                boci = reaction.message.author
                if reaction.count >= 3:
                    if reaction.message.id not in already_checked:
                        already_checked.append(reaction.message.id)
                        await boci.timeout(timedelta(minutes=2), reason="Nem volt vicces")
                        uzenet = "Nem volt vicces, Boti. " + random.choice("<:cringe:644026740242645023> <:OhNoCringe:945225281172553760> <:cassiecringe:859589366870573106> <:SCCRINGE:664519482416300053> <:Catastrophe_CringeBro:645327316540456998> <:AntonCringe:690691883500044409> <a:cringesmiley:774412323662069770> <a:cringepepepet:773106637774913586> <:notcringebutwtf:600071034229751848> <:flushcringe:644026697880043570> <:pepe_cringe:774411918081261578>".split(" "))
                        await reaction.message.reply(uzenet)

        if str(reaction.emoji) in ("<:kekcry:871410695953059870>", "<:kekw:800726027290148884>"):
            if reaction.message.author.id == 569937005463601152:
                if reaction.count >= 3:
                    if reaction.message.id not in already_checked:
                        already_checked.append(reaction.message.id)
                        uzenet = f"Gratulálunk, ez vicces volt, Boti. {emoji.emojize(':clap:')} {emoji.emojize(':partying_face:')}"
                        await reaction.message.reply(uzenet)

        if spehmode:
            print("react at:", str(datetime.now()),(emoji.demojize(reaction.emoji) if isinstance(reaction.emoji, str) else reaction.emoji.name), "by:",user, "on message:", reaction.message.content)

    @client.slash_command(name="help", description="Lists what all the commands do.")
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

    @client.slash_command(name="daily", description="Collect your daily pills")
    async def daily(self, ctx:discord.Interaction):
        user = self.getUserFromDC(ctx.user)
        try:
            pipikLogger.debug(f"user daily date {user.dailyDate}")
            if type(user.dailyDate) == datetime:
                user.dailyDate = user.dailyDate.date()
        except AttributeError:
            user.dailyDate = (datetime.now() - timedelta(days=1)).date()
            user.dailyStreak = 0  # kind of redundant? nvm
        finally:
            if user.dailyDate == date.today():  # if today already taken
                tomorrow = datetime.now() + timedelta(1)
                midnight = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=0, minute=0,second=0)
                embedVar = discord.Embed(title="Daily pills", description="You already collected your pills today.",color=ctx.user.color)
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
                        await user.updateUserAchi(ctx, "dedicated")
                embedVar = discord.Embed(title="Daily pills", color=ctx.user.color)
                embedVar.add_field(name="Current streak", value=user.dailyStreak)
            else:
                pipikLogger.warning(f"something is wrong {user.dailyDate}, {date.today()}, {user.dailyDate - date.today()}")
                return
            await ctx.send(embed=embedVar)
            user.dailyDate = datetime.now().date()
            await self.addPill(ctx, ctx.user.color, user, 0, random.randint(1, 3))  # yellow pill
            if user.dailyStreak >= random.randint(0, 99):
                await self.addPill(ctx, ctx.user.color, user, 1, random.randint(1, 2))  # red pill
            if user.dailyStreak / 10 >= random.randint(0, 99):
                if "lucky_draw" not in user.achi:
                    await user.updateUserAchi(ctx, "lucky_draw")
                    await self.addPill(ctx, ctx.user.color, user, 2, 1)  # blue pill
            self.saveFile()

    @commands.command(aliases=("angy", "angry"))
    async def upset(self, ctx):
        embedVar = discord.Embed(title="There´s no need to be upset!", color=ctx.author.color)
        await ctx.channel.send(embed=embedVar)
        await ctx.channel.send("https://cdn.discordapp.com/attachments/800207393539620864/814231682307719198/matkospin.mp4")

    @commands.command(aliases=("spin", "spinme"))
    async def matkospin(self, ctx):
        embedVar = discord.Embed(title="There´s no need to be upset!", color=ctx.author.color)
        await ctx.channel.send(embed=embedVar)
        await ctx.channel.send("https://cdn.discordapp.com/attachments/618082756584407041/814240245889105920/matkospinme_1.mp4")

    @commands.command(aliases=("party",))
    async def poolparty(self, ctx):
        embedVar = discord.Embed(title="There´s no need to be upset!", color=ctx.author.color)
        await ctx.channel.send(embed=embedVar)
        await ctx.channel.send("https://cdn.discordapp.com/attachments/800207393539620864/814260748074614794/matkopoolparty.mp4")

    @client.slash_command(name="max", description="Leaderboard of biggest pps",dm_permission=False)
    async def max(self, ctx, server: str = discord.SlashOption("leaderboard",description="User leaderboard or server leaderboards",required=False,choices=("This server","Between servers"),default="This server")):
        try:
            if server == "This server":
                ldb = self.leaderboards[str(ctx.guild_id)]
            elif server == "Between servers":
                ldb = sorted([(client.get_guild(int(id)),round(sum(map(lambda user: user[1],users)),3)) for id,users in self.leaderboards.items()],key=lambda x:x[1],reverse=True)[:5]
        except KeyError:
            await ctx.send(embed=discord.Embed(title="Leaderboard empty",description="Use the /pp command to measure your pp first"))
        else:
            embedVar = discord.Embed(title="Leaderboard of biggest pps", description=25 * "-")
            for i in ldb:
                embedVar.add_field(name=i[0], value=f"{i[1]} cm {'total' if server == 'Between servers' else ''}", inline=False)
            await ctx.send(embed=embedVar)

    @client.slash_command(name="min", description="Leaderboard of smallest pps",dm_permission=False)
    async def min(self, ctx,server: str = discord.SlashOption("leaderboard",description="User leaderboard or server leaderboards",required=False,choices=("This server","Between servers"),default="This server")):
        try:
            if server == "This server":
                ldb = self.loserboards[str(ctx.guild_id)]
            elif server == "Between servers":
                ldb = sorted([(client.get_guild(int(id)), round(sum(map(lambda user: user[1], users)),5)) for id, users in self.loserboards.items()], key=lambda x: x[1], reverse=False)[:5]
        except KeyError:
            await ctx.send(embed=discord.Embed(title="Loserboard empty",description="Use the /pp command to measure your pp first"))
        else:
            embedVar = discord.Embed(title="Leaderboard of smallest pps", description=25 * "-")
            for i in ldb:
                embedVar.add_field(name=i[0], value=f"{i[1]} cm {'total' if server == 'Between servers' else ''}", inline=False)
            await ctx.send(embed=embedVar)

    @client.slash_command(name="weather",description="Current weather at location, or simply see how your pp is affected at the moment.")
    async def weather(self, ctx, location:str =discord.SlashOption(name="city",description="City name, for extra precision add a comma and a country code e.g. London,UK",required=False)):
        await ctx.response.defer()
        if not location:
            self.getTemp()
            offset = ((7 - abs(7 - datetime.now().month)) - 1) * 3  # average temperature okolo ktorej bude pocitat <zcvrk alebo rast>
            embedVar = discord.Embed(title=f"It´s {self.temperature} degrees in Bratislava.",description="You can expect {} {} pps".format(("quite", "slightly")[int(abs(self.temperature - offset) < 5)],("shorter", "longer")[int(self.temperature - offset > 0)]), color=(0x17dcff if self.temperature < offset - 5 else 0xbff5ff if self.temperature <= offset else 0xff3a1c if self.temperature > offset + 5 else 0xffa496 if self.temperature > offset else ctx.user.color))
            offsettime = self.sunrise_date.astimezone(pytz.timezone("Europe/Vienna"))
            embedVar.add_field(name="And the sun is coming up at",value="{}:{:0>2}.".format(offsettime.hour, offsettime.minute))
        else:
            if location == "me":
                try:
                    location = {617840759466360842: "Bardoňovo", 756092460265898054: "Plechotice",677496112860626975: "Giraltovce", 735473733753634827: "Veľký Šariš"}[ctx.user.id]
                except KeyError:
                    pass
            else:
                try:
                    location = {"ds":"Dunajská Streda","ba":"Bratislava","temeraf": "Piešťany", "piscany": "Piešťany", "pistany": "Piešťany", "mesto snov": "Piešťany","terebes": "Trebišov", "eperjes": "Prešov", "blava": "Bratislava", "diera": "Stropkov","saris": "Veľký Šariš", "ziar": "Žiar nad Hronom", "pelejte": "Plechotice","bardonovo": "Bardoňovo", "rybnik": "Rybník,SK"}[antimakkcen(location.casefold())]
                except KeyError:
                    if "better than" in location.casefold():
                        description = "Yeah babe, you are the best!"
                    elif any(word in location.casefold() for word in ("dick", "pp", "penis", "cock", "schlong", "pussy", "humanity", "faith", "tits", "titty")):
                        description = "Very funny."
                    elif "to live" in location.casefold():
                        description = "Please seek help, do not suffer alone!"
                    elif "someone like you" == location:
                        description = "Keep searching Adele, maybe go deeper!"
                    elif "asked" in location:
                        description = "Oof what a burn! Your kindergarten friends must be impressed."
                    elif "someone" in location:
                        description = "Keep searching, babe."
                    elif any(word in location.casefold() for word in ("gf","bf","girlfriend","boyfriend","girl friend","boy friend")):
                        description = "I'm not a cupid, yo!"
                    else:
                        description = "Please check your spelling or specify the countrycode e.g. London,uk"
            # a = (mgr.weather_at_places(location, 'like', limit=1)[0]).weather some items are missing :(
            try:
                b = mgr.weather_at_place(location)
                a = b.weather
            except pyowm.commons.exceptions.NotFoundError:
                await ctx.send(embed=discord.Embed(title=location + " not found.", description=description))
                return
            else:
                embedVar = discord.Embed(title=f"Current weather at ** {b.location.name},{b.location.country}**",description="{:-^40}".format("Local time: " + str(datetime.utcnow() + timedelta(seconds=a.utc_offset))[11:19]), color=ctx.user.color)
                for k, v in {"Weather": a.detailed_status, "Temperature": str(a.temperature("celsius")["temp"]) + "°C","Feels like": str(a.temperature("celsius")["feels_like"]) + "°C","Clouds": str(a.clouds) + "%", "Wind": str(a.wind()["speed"] * 3.6)[:6] + "km/h","Humidity": str(a.humidity) + "%", "Visibility": str(a.visibility_distance) + "m","Sunrise": str(a.sunrise_time(timeformat="date") + timedelta(seconds=a.utc_offset))[11:19],"Sunset": str(a.sunset_time(timeformat="date") + timedelta(seconds=a.utc_offset))[11:19],"UV Index": a.uvi, "Atm. Pressure": str(a.pressure["press"]) + " hPa","Precip.": str(a.rain["1h"] if "1h" in a.rain else 0) + " mm/h"}.items():
                    embedVar.add_field(name=k, value=v)
                embedVar.set_thumbnail(url="http://openweathermap.org/img/wn/{}@2x.png".format(a.weather_icon_name))
        await ctx.send(embed=embedVar)

    @client.slash_command(name="tips", description="Read some tips on how to increase your pp size")
    async def tips(self, ctx):
        await ctx.send("""```diff
Disclaimer: EVERYTHING IS RANDOM, NOTHING GUARANTEES BIGGER PPS, ONLY BETTER CHANCES FOR A BIG PP!

A lot of things can influence your pp's size.
For your convenience i'll share some tips and tricks
for you here:
--------------------------------------------------
+I´ve heard your pp looks bigger in other people´s hands, so try asking others to hold it for you. (keyword: holding)

+The bot likes compliments, try some sweet words on it.

-The bot however dislikes insults.

-Lower temperatures may cause your pp to shrink, consider measuring it when it´s warmer outside.

+Morning woods are a normal healthy occurrence each morning, try to use them to your advantage.

+If you overslept this wakeup routine, don't worry, you can try to excite your pp with the fap command, but be wary of your endurance, relapsing causes you to go into a recharge state when your pp becomes more shy than usual.

If nothing else helps, you can turn to pills for help. But beware as overusing them might bring unforeseen side effects, like impotency.
You can get free pills each day with the /daily command
```""")

    @commands.command()
    async def rename(self, ctx, name):
        await ctx.message.guild.me.edit(nick=name)

    class PillTakeDropdown(discord.ui.Select):
        def __init__(self, user):
            self.user = user
            pillselect = [discord.SelectOption(label=pills[pill[0]]["name"],value=str(pill[0]),description=f"in inventory: {pill[1]}") for pill in self.user.items if pill[1] > 0] + [discord.SelectOption(label="Cancel",value="-1",emoji=emoji.emojize(":cross_mark:"))]

            super().__init__(placeholder="Select a pill to consume", options=pillselect)  # TODO: embedize

        async def callback(self, interaction):
            if interaction.user.id == self.user.id:
                if self.values[0] == "-1":
                    await interaction.response.edit_message(content="Cancelled.", view=None)
                else:
                    await interaction.response.edit_message(content=f"You took a {pills[int(self.values[0])]['name']}\nNow go measure your pp before it wears out!",view=None)  # TODO: embedize
                    await self.user.takePill(int(self.values[0]))
                    if "pill_popper" not in self.user.achi:
                        await self.user.updateUserAchi(interaction, "pill_popper")
            else:
                await interaction.send("This is not your prompt, use /pills to use your pills.",ephemeral=True)

    class PillCraftDropdown(discord.ui.Select):
        def __init__(self, user):
            self.user = user
            pillselect = [discord.SelectOption(label="Cancel",value="-1",emoji=emoji.emojize(":cross_mark:"))]
            for pill in [item for item in self.user.items if item[0] != len(pills) - 1 and item[1] >= 10]:  # populating the select component with options
                pillselect.append(discord.SelectOption(label=pills[pill[0]]["name"],value=str(pill[0]),description=f"in inventory: {pill[1]}"))
            super().__init__(placeholder="Select pills to crush up", options=pillselect)

        async def callback(self, interaction):
            if interaction.user.id == self.user.id:
                if self.values[0] == "-1":
                    await interaction.response.edit_message(content="Cancelled.", view=None)
                else:
                    which = int(self.values[0])
                    # amount = int(attr[2] or 1) #TODO: do multiselect again or just add it as options
                    amount = 1
                    self.user.items[which][1] -= amount * 10
                    await pipikbot.addPill(interaction, interaction.user.color, self.user,(self.user.items[which][0]) + 1, amount)
                    await interaction.response.edit_message(content=f"You crushed up 10 {pills[int(self.values[0])]['name']}",view=None)  # TODO emedize these
                    if self.user.items[which][1] == 0:
                        del (self.user.items[which])
                    if "breaking_bad" not in self.user.achi:
                        await self.user.updateUserAchi(interaction, "breaking_bad")
            else:
                await interaction.send("This is not your prompt, use /pills to use your pills.", ephemeral=True)

    class PillsButtonsConsume(discord.ui.Button):
        def __init__(self, user):
            self.user = user
            canConsume = len(user.items) != 0 and self.user.pill not in range(0, len(pills))
            super().__init__(label="Consume", disabled=not canConsume, style=discord.ButtonStyle.gray,emoji=emoji.emojize(":face_with_hand_over_mouth:"))

        async def callback(self, interaction):
            if interaction.user.id != self.user.id:
                await interaction.send("This is not your inventory, use /item to see your pills.",ephemeral=True)
                return
            self.style = discord.ButtonStyle.green
            for child in self.view.children:
                child.disabled = True
            await interaction.response.edit_message(view=self.view)
            viewObj = discord.ui.View()
            viewObj.add_item(pipikbot.PillTakeDropdown(pipikbot.getUserFromDC(interaction.user)))
            await interaction.send("Pill consumption", view=viewObj)  # TODO: embedize

    class PillsButtonsCraft(discord.ui.Button):
        def __init__(self, user):
            self.user = user
            canCraft = any([i[1] >= 10 for i in user.items])
            super().__init__(label="Craft", disabled=not canCraft, style=discord.ButtonStyle.gray,emoji=emoji.emojize(":hammer:"))

        async def callback(self, interaction):
            if interaction.user.id != self.user.id:
                await interaction.send("This is not your inventory, use /pills to see your pills.", ephemeral=True)
                return
            self.style = discord.ButtonStyle.green
            for child in self.view.children:
                child.disabled = True
            await interaction.response.edit_message(view=self.view)

            viewObj = discord.ui.View()
            viewObj.add_item(pipikbot.PillCraftDropdown(self.user))
            await interaction.send("Pill crafting", view=viewObj)  # TODO: embedize

    @client.slash_command(description="See, manage and use your pill inventory.")
    async def pills(self, ctx):
        user = self.getUserFromDC(ctx.user)
        user.items = sorted(user.items, key=lambda a: a[0])
        text = "```py\n"
        text += "Pills".center(25) + "\nCrafting takes 10 pills and crafts a better quality one\nBetter pills equals bigger pps\nExcessive use might result in impotency!\n{:-^25}\n".format("-")
        text += "\n".join(["{:<15} ({:<2} min)| amount: {}".format(pills[i[0]]["name"],(pills[i[0]]["effectDur"].seconds) // 60, i[1]) for i in list(user.items)])
        if len(user.items) == 0:
            text += "You have no pills. Use /daily to get some!"
        text += "\n```"

        if user.pill in range(0, len(pills)):
            pipikLogger.debug("uh oh pill already in you")
            takenAgo = datetime.now() - user.pillPopTime
            if takenAgo < pills[user.pill]["effectDur"] + pills[user.pill]["badEffectDur"]:
                pipikLogger.debug("nem jart le")
            else:
                user.pill = None

        viewObj = discord.ui.View()
        viewObj.add_item(self.PillsButtonsConsume(user))
        viewObj.add_item(self.PillsButtonsCraft(user))
        await ctx.send(content=text, view=viewObj)

    class FapButton(discord.ui.Button):
        def __init__(self, user):
            self.user = user
            if user.cd == None:
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
                await interaction.send("This is not your button, use your own by typing /fap",ephemeral=True)
                return
            if random.randint(0, 10 + (self.user.fap * 2)) < 10:
                self.user.fap += 1
                self.label = f"Combo: {self.user.fap}"
            else:
                self.style = discord.ButtonStyle.red
                self.emoji = emoji.emojize(':sweat_droplets:')
                self.disabled = True
                self.label = "Oops!"
                if self.user.fap == 0:
                    if "one_pump" not in self.user.achi:
                        await self.user.updateUserAchi(interaction, "one_pump")
                self.user.cd = datetime.now() + timedelta(minutes=5)
                self.user.fap = 0
            await interaction.response.edit_message(view=self.view)

    @client.slash_command(name="fap", description="Increase your pp length by repeatedly mashing a button.")
    async def fap(self, ctx):
        user = self.getUserFromDC(ctx.user)
        if user.cd != None:
            if user.cd == 0 or user.cd - datetime.now() < timedelta(seconds=0):
                user.cd = None
        if user.cd == None:
            text = "Use repeatedly to increase length."
        else:
            timestr = "<t:" + str(int(user.cd.timestamp())) + ":R>"
            text = f"Come back {timestr}"
        viewObj = discord.ui.View()
        viewObj.add_item(self.FapButton(user))
        await ctx.send(content=text, view=viewObj)  # TODO: embedize

    @client.slash_command(name="profile", description="See your, or someone else's pp profile") #oh my god this is ugly
    async def profile(self, ctx: discord.Interaction, user: discord.User = discord.SlashOption(name="user", description="User to display", required=False)):
        usertocheck = user or ctx.user
        user = self.getUserFromDC(usertocheck)

        temppill = False
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

        achievements = self.achievements
        temphorniness = user.fap + (pills[user.pill]["effect"] if user.pill not in (None, "None", "none") else 0)
        user.items = sorted(user.items, key=lambda a: a[0])

        text = usertocheck.name.center(25,"=")
        text += f"\nPersonal best: {user.pb}\nPersonal worst: {user.pw}\n"
        text += f"Horniness: {temphorniness}\n" if user.cd == None else ""
        text += "Pill: {} | {} minutes left.\n".format(pills[user.pill]["name"], ((pills[user.pill]["effectDur"] - takenAgo).seconds // 60) + 1) if temppill else ""
        text += "Erectyle disfunction: {} hours {} minutes\n".format(dysf_left.seconds // 3600, (dysf_left.seconds // 60 % 60) + 1) if user.cd is not None else ""
        text += "{:-^25}".format("Items") + "\n"
        text += "\n".join(["{:<20} | amount: {}".format(pills[i[0]]["name"], i[1]) for i in list(user.items)])
        text += "\n{:-^25}\n".format("Achievements")
        if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author != client.user:
            text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) + (("= " + achi.desc) if achi.achiid in user.achi else "= ???") for achi in achievements.values())
        else:
            text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) for achi in achievements.values())
            text += "\n\nfor more info, try /achi"
        text += "\n" + "{:-^25}".format("-")
        await ctx.send("```\n" + text + "\n```") #lord forgive me for what ive done

    @client.slash_command(name="achi", description="See your achievements")
    async def achi(self, ctx):
        user = self.getUserFromDC(ctx.user)
        achievements = self.achievements
        text = "Your achievements".center(60,"=")+"\n"
        text += "\n".join((emoji.emojize(":check_mark_button:") if achi.achiid in user.achi else emoji.emojize(":locked:")) + " " + achi.icon + " " + "{:23}".format(achi.name) + (("= " + achi.desc) if achi.achiid in user.achi else "= ???") for achi in achievements.values())
        await ctx.send("```\n" + text + "\n```", ephemeral=True)

    @discord.slash_command(name="pp", description="For measuring your pp.",dm_permission=False)
    async def pp(self,ctx,message:str =discord.SlashOption(name="message", description="Would you like to tell me something?",required=False, default=None)):
        await ctx.response.defer()
        msg = None
        embedMsg = discord.Embed(description=".", color=ctx.user.color)  # placeholders
        user = self.getUserFromDC(ctx.user)
        currmethods = 0  # this is for keeping track of what pp enlargement methods were used. Im gonna perform bitwise operations on this
        pipikLogger.debug(f"{datetime.now() - self.weatherUpdatedTime}, weatherupdatetimer, how long ago was updated")
        if datetime.now() - self.weatherUpdatedTime > timedelta(hours=1):
            pipikLogger.debug("updating temp")
            self.getTemp()
        else:
            pipikLogger.debug("temp up to date")

        curve = 1.85
        multiplier = 90

        # pill checker
        if user.pill in range(0, len(pills)) and user.pill not in (None, "none", "None"):  # fucking inconsistent
            currmethods = currmethods | 32
            takenAgo = datetime.now() - user.pillPopTime
            if takenAgo < pills[user.pill]["effectDur"]:
                curve -= pills[user.pill]["effect"] / 15
                multiplier += pills[user.pill]["effect"]
            elif takenAgo < pills[user.pill]["effectDur"] + pills[user.pill]["badEffectDur"]:
                badEffectStart = user.pillPopTime + pills[user.pill]["effectDur"]
                user.cd = datetime.now() + (pills[user.pill]["badEffectDur"] - (datetime.now() - badEffectStart))
            else:
                user.cd = None
                user.pill = None

        # fap checker
        if user.cd != None:
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
        pipikLogger.debug(f"morning wood check, {self.sunrise_date}, sunrise date (gmt) # {sunrise}, until sunrise {datetime.now(tz_info)}, current time (gmt)")
        if sunrise < timedelta(hours=1) and sunrise > timedelta(hours=-1):
            multiplier += 10
            curve -= 0.5
            currmethods = currmethods | 8
            if "morning" not in user.achi:
                await user.updateUserAchi(ctx, "morning")

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
            if len(self.usedcompliments) > 5:
                self.usedcompliments.pop()
            self.usedcompliments.add(message)
            if message not in self.usedcompliments:
                message = [antimakkcen(word.casefold()) for word in message.split(" ")]
                compliments = len(good_words.intersection(message)) - len(bad_words.intersection(message))

                multiplier += 2.2 * min(5, compliments)
                curve -= min(5, compliments) * 0.12

                if compliments < 1:
                    embedMsg.add_field(name=random.choice(bad_responses), value=emoji.emojize(random.choice(bad_emojis)),inline=False)
                else:
                    embedMsg.add_field(name=random.choice(good_responses), value=emoji.emojize(random.choice(good_emojis)),inline=False)
                    currmethods = currmethods | 2

                # compliment achi checker
                if compliments > 4 and "flirty" not in user.achi:
                    await user.updateUserAchi(ctx, "flirty")
                elif compliments < -4 and "playa" not in user.achi:
                    await user.updateUserAchi(ctx, "playa")

        # temperature adjustment
        pocasieOffset = ((7 - abs(7 - datetime.now().month)) - 1) * 3  # average temperature okolo ktorej bude pocitat <zcvrk alebo rast>
        if self.temperature > pocasieOffset + 5:
            currmethods = currmethods | 4
        curve -= (self.temperature - pocasieOffset) / 20
        multiplier += self.temperature - pocasieOffset

        # holding checker
        try:
            pipikLogger.debug(f"holdings table {self.holding} curr chanel {ctx.channel_id}, author {ctx.user}")
            if self.holding[ctx.guild.id] not in ("", " ", None) and self.holding[ctx.guild.id] != ctx.user:
                currmethods = currmethods | 1
                curve -= 0.4
                multiplier += 11
                holder = self.holding[ctx.guild.id]
                held = self.getUserFromDC(ctx.user)
                embedMsg.add_field(name="With helping hands from:", value=holder.display_name)
                if msg:
                    await msg.edit(embed=embedMsg)
                if "helping_hands" not in held.achi:  # helpout
                    await held.updateUserAchi(ctx, "helping_hands", name=ctx.user.display_name)  # holding achis
                if "friend_need" not in holder.achi:
                    await holder.updateUserAchi(ctx, "friend_need")
            self.holding.update({ctx.guild.id: None})
            if not any(self.holding.values()):
                self.holding = {}
        except KeyError as e:
            pipikLogger.error(e)

        # final calculation
        if curve < 0:
            pipikLogger.warning(25 * "#" + "uh oh stinky")
            curve = -curve * 0.01
        pipik = round((random.expovariate(curve) * multiplier), 3)
        pipikLogger.debug(f"{ctx.user.display_name}, pipik, {pipik}, curve, {curve}, mult, {multiplier}, compl, {compliments}, temp,{self.temperature}, fap, {user.fap}, cd, {user.cd}")

        # personal record checker
        if pipik > user.pb:
            await self.updateUserStats(user, "pb", pipik)
        if not user.pw or pipik < user.pw:
            await self.updateUserStats(user, "pw", pipik)

        # rekord checker
        try:
            pipikLogger.debug(f"this server´s leaderboard {self.leaderboards[str(ctx.guild_id)]}")
        except KeyError:
            self.leaderboards[str(ctx.guild_id)] = []
        if len(self.leaderboards[str(ctx.guild_id)]) > 4 and len(self.loserboards[str(ctx.guild_id)]) > 4:  # if leaderboard fully populated go check if the new measurement is better,
            if pipik > self.leaderboards[str(ctx.guild_id)][0][1] or pipik < self.loserboards[str(ctx.guild_id)][0][1]:  # otherwise just automatically populate it on the leaderboard without announing a record
                star = emoji.emojize(':glowing_star:')
                await ctx.channel.send(embed=discord.Embed(title=(str(3 * star) + "Wow! {} has made a new record!" + str(3 * star)).format(ctx.user.name),description="Drumroll please... " + emoji.emojize(":drum:"), color=discord.Colour.gold()))
                await asyncio.sleep(2)
            if pipik > self.leaderboards[str(ctx.guild_id)][4][1]:  # if bigger than the smallest on the leaderboard
                self.updateLeaderBoard(str(ctx.guild_id), ctx.user.name, pipik)
            if pipik < self.loserboards[str(ctx.guild_id)][4][1]:  # if smaller than the biggest on the leaderboard
                self.updateLoserBoard(str(ctx.guild_id), ctx.user.name, pipik)
        else:
            self.updateLeaderBoard(str(ctx.guild_id), ctx.user.name, pipik)
            self.updateLoserBoard(str(ctx.guild_id), ctx.user.name, pipik)

        # size achi checker
        if pipik > 300:
            if "megapp" not in user.achi:
                await user.updateUserAchi(ctx, "megapp")
        elif pipik < 0.5:
            if "micropp" not in user.achi:
                await user.updateUserAchi(ctx, "micropp")
        elif 69 <= pipik < 70:
            if "nice" not in user.achi:
                await user.updateUserAchi(ctx, "nice")

        # pp enlargement methods achi checker
        try:
            user.methods
        except KeyError:
            user.methods = 0
        if currmethods == 63 and "desperate" not in user.achi:
            await user.updateUserAchi(ctx, "desperate")
        await self.updateUserStats(user, "methods", user.methods | currmethods)
        if user.methods == 63 and "tested" not in user.achi:
            await user.updateUserAchi(ctx, "tested")

        # final printer
        embedMsg.title = f"*{ctx.user.display_name}* has **{pipik}** cm long pp!"
        embedMsg.description = str("o" + (min(4094, (int(pipik) // 10)) * "=") + "3")
        if msg:
            await msg.edit(embed=embedMsg)
        else:
            msg = await ctx.send(embed=embedMsg)
        if sunrise and type(sunrise) != str:
            if timedelta(hours=1) > sunrise > timedelta(hours=-1):
                await msg.add_reaction(emoji.emojize(":sunrise:"))

os.chdir(root)
if not args.minimal and not args.no_maths:
    utils = os.listdir(r"./utils")
    files = utils + [r"../pipikNextcord.py"]
    linecount = 197  # matstatMn is added manually cuz i have a million commented lines after if __name__ == __main__
else:
    files = (r"../pipikNextcord.py",)
    linecount = 0
for file in files:
    if file.endswith(".py"):
        with open(root+r"/utils/"+file, "r", encoding="UTF-8") as f:
            linecount += len(f.readlines())

cogs = os.listdir("./cogs")
cogs.remove("sympycog.py") if args.no_maths or args.minimal else None
cogs.remove("pscog.py") if args.no_maths or args.minimal else None
cogs.remove("ascog.py") if args.no_maths or args.minimal else None
cogs.remove("zsskcog.py") if args.no_zssk or args.minimal else None
cogs.remove("radiocog.py") if args.no_radio or args.minimal else None
cogs.remove("gifsavercog.py") if args.no_gifsaver or args.minimal else None
cogs.remove("aiscog.py") if args.no_ais or args.minimal else None
cogs.remove("fujkincog.py") if args.no_fujkin or args.minimal else None
cogs.remove("wordlecog.py") if args.no_wordle or args.minimal else None
cogs.remove("rpgcog.py") if args.no_rpg or args.minimal else None
cogs.remove("cloveckocog.py") if args.no_clovece or args.minimal else None
cogs.remove("topiccog.py") if args.no_topic or args.minimal else None
cogs.remove("currencyCog.py") if args.no_currency or args.minimal else None
cogs.remove("testing.py") if args.no_testing else None

for n, file in enumerate(cogs, start=1):
    if file.endswith(".py"):
        with open("./cogs/"+file, "r", encoding="UTF-8") as f:
            linecount += len(f.readlines())
        client.load_extension("cogs." + file[:-3],extras={"baselogger":pipikLogger})
        sys.stdout.write(f"\rLoading... {round((n / len(cogs)) * 100,2)}% [{((int((n/len(cogs))*10)*'=')+'>').ljust(11, ' ')}]")
        sys.stdout.flush()
sys.stdout.write("\rAll cogs loaded.                    \n")
sys.stdout.flush()
os.chdir(root)

client.add_cog(PipikBot(client))
client.run(os.getenv("MAIN_DC_TOKEN"))  # bogibot

# 277129587776 reduced perms
# https://discord.com/api/oauth2/authorize?client_id=618079591965392896&permissions=543652576368&scope=bot%20applications.commands bogibot