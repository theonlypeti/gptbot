import sys
import nextcord as discord
import random
from nextcord.ext import commands
import asyncio
from datetime import datetime, timedelta
import json
from utils.antimakkcen import antimakkcen
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
parser.add_argument("--no_pipik",action="store_true",help="Disable pipikbot module.")
args = parser.parse_args()

pipikLogger = logging.getLogger("Base")
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
# TODO make pipikbot users a dict of id:user instead of a list of users, also redo the getUserFromDC func then
# TODO make an actual lobby extension
# TODO make pills buttons edit message not reply

intents = discord.Intents.all() #TODO remember what do i use members intent for?!?!! update: members is used when checking if guild is premium for example
intents.presences = False

client = commands.Bot(command_prefix='&', intents=intents,chunk_guilds_at_startup=True) #TODO chunk_guilds_at_startup=False might help me
client.remove_command('help')


#T9 = ({key * i: letter for i, key, letter in zip([(num % 3) + 1 for num in range(0, 26)], [str(q // 3) for q in range(6, 30)],sorted({chr(a) for a in range(ord("A"), ord("Z") + 1)} - {"S", "Z"}))} | {"7777": "S", "9999": "Z","0": " "})
#T9rev = {v: k for k, v in T9.items()}

##@client.message_command(name="T9ize",guild_ids=[860527626100015154])
##async def t9(interaction, text):
##    await interaction.send(" ".join([T9rev[letter.upper()] for letter in text.content]))
##
##@client.message_command(name="T9rev",guild_ids=[860527626100015154])
##async def t9r(interaction, text):
##    await interaction.send("".join([T9[letters] for letters in text.content.split(" ")]))


#-------------------------------------------------#

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
        embedVar = discord.Embed(title="Brainfuck code output", type="rich", description=output)
        embedVar.set_author(name=ctx.user.display_name, icon_url=ctx.user.avatar.url)
        await ctx.send(embed=embedVar)

@client.slash_command(description="Brainfuck interpreter",name="brainfuck")
async def bf_modal(ctx):
    modal = BfModal(title="Brainfuck")
    await ctx.response.send_modal(modal)

#@commands.has_permissions(manage_server=True)
@client.slash_command(name="pfp", description="chooses a random emote for the servers profile pic.",guild_ids=[860527626100015154,552498097528242197],dm_permission=False)
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
        if arg and arg == "raw": #TODO consider https://docs.nextcord.dev/en/latest/api.html#nextcord.utils.format_dt
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

discord_emotes = {}

@client.event
async def on_ready():
    game = discord.Game(f"{linecount} lines of code; V3.0! use /help")
    await client.change_presence(status=discord.Status.online, activity=game)
    print(f"Signed in {datetime.now()}")
    pipikLogger.debug(f"{time_module.perf_counter() - start} Bootup time")
    readEmotes()

def saveEmotes():
    with open(root+"/data/pipikemotes.txt", "w") as file:
        json.dump(discord_emotes, file, indent=4)
    pipikLogger.info("saved emotes")

def readEmotes():
    global discord_emotes
    with open(root+"/data/pipikemotes.txt", "r") as file:
        discord_emotes = json.load(file)
    pipikLogger.info("loaded emotes")

@client.command()
async def registerEmote(ctx, *attr):
    for emoji in attr:
        discord_emotes.update({emoji.split(":")[-2]: emoji})
    saveEmotes()

@client.command()
async def registerAnimatedEmotes(ctx, howmany):
    howmany = int(howmany)
    for emoji in reversed(ctx.message.guild.emojis):
        if emoji.animated and howmany:
            howmany -= 1
            discord_emotes.update({emoji.name: f"<a:{emoji.name}:{emoji.id}>"})
    saveEmotes()

@client.command()
async def reloadEmotes(ctx):
    readEmotes()

async def getMsgFromLink(link):
    link = link.split('/')
    #server_id = int(link[4])
    channel_id = int(link[5])
    msg_id = int(link[6])
    #server = client.get_guild(server_id)
    channel = client.get_channel(channel_id)
    message = await channel.fetch_message(msg_id)
    return message

@client.slash_command(name="emote", description="For using special emotes")
async def emote(ctx,
                emote=discord.SlashOption(name="emoji",description="An emoji name, leave blank if you want to list them all out.",required=False, default=None),
                msg:str =discord.SlashOption(name="message_link",description="Use 'copy message link' to specify a message to react to.",required=False),
                text:str = discord.SlashOption(name="text",description="The text message to send along with any emotes, use {emotename} as placeholder.",required=False, default=None)):
    def check(reaction, user):
        return not user.bot and (str(reaction.emoji) in list(discord_emotes.values()))

    pipikLogger.debug(f"{ctx.user}, {emote}, {datetime.now()}")
    if msg and emote:
        mess = await getMsgFromLink(msg)
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
async def emote_autocomplete(interaction, emote: str):
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

@client.event
async def on_message(ctx):
    if not ctx.author.bot:
        #if spehmode:
            #print("message at:",str(datetime.now()),"content:",ctx.content,"by:",ctx.author,"in:",ctx.channel.name)
        if "free nitro" in antimakkcen(ctx.content).casefold():
            await ctx.channel.send("bitch what the fok **/ban**")
    await client.process_commands(ctx)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user):
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

@client.command(aliases=("angy", "angry"))
async def upset(ctx):
    embedVar = discord.Embed(title="There´s no need to be upset!", color=ctx.author.color)
    await ctx.channel.send(embed=embedVar)
    await ctx.channel.send("https://cdn.discordapp.com/attachments/800207393539620864/814231682307719198/matkospin.mp4")

@client.command(aliases=("spin", "spinme"))
async def matkospin(ctx):
    embedVar = discord.Embed(title="There´s no need to be upset!", color=ctx.author.color)
    await ctx.channel.send(embed=embedVar)
    await ctx.channel.send("https://cdn.discordapp.com/attachments/618082756584407041/814240245889105920/matkospinme_1.mp4")

@client.command(aliases=("party",))
async def poolparty(ctx):
    embedVar = discord.Embed(title="There´s no need to be upset!", color=ctx.author.color)
    await ctx.channel.send(embed=embedVar)
    await ctx.channel.send("https://cdn.discordapp.com/attachments/800207393539620864/814260748074614794/matkopoolparty.mp4")

@client.command()
async def rename(ctx, name):
    await ctx.message.guild.me.edit(nick=name)

#-------------------------------------------------#

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
cogs.remove("pipikcog.py") if args.no_pipik else None

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

client.run(os.getenv("MAIN_DC_TOKEN"))  # bogibot

# 277129587776 reduced perms
# https://discord.com/api/oauth2/authorize?client_id=618079591965392896&permissions=543652576368&scope=bot%20applications.commands bogibot