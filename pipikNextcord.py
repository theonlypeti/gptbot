import sys
import nextcord as discord
import random
from nextcord.ext import commands
from datetime import datetime, timedelta
from utils.antimakkcen import antimakkcen
import emoji
import os
import argparse
import time as time_module
import logging
from dotenv import load_dotenv
import coloredlogs

start = time_module.perf_counter()

load_dotenv(r"./credentials/main.env")

parser = argparse.ArgumentParser(prog="PipikBot V3.5",description='A fancy discord bot.',epilog="Written by theonlypeti.")

for cog in os.listdir("./cogs"):
    if cog.endswith("cog.py"):
        parser.add_argument(f"--no_{cog.removesuffix('cog.py')}", action="store_true", help=f"Disable {cog} extension.")

parser.add_argument("--minimal", action="store_true", help="Disable most of the extensions.")
parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
parser.add_argument("--no_testing", action="store_true", help="Disable testing module.")
args = parser.parse_args()

pipikLogger = logging.getLogger("Base")

#FORMAT = "[{asctime}][{filename}][{lineno:4}][{funcName}][{levelname}] {message}"
#formatter = logging.Formatter(FORMAT, style="{")  #this is for default logger

fmt = "[ %(asctime)s %(filename)s %(lineno)d %(funcName)s %(levelname)s ] %(message)s"
coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'}, 'lineno': {'color': 'magenta'}, 'levelname': {'bold': True, 'color': 'black'}, 'filename': {'color': 'blue'},'funcname': {'color': 'cyan'}}
coloredlogs.DEFAULT_LEVEL_STYLES = {'critical': {'bold': True, 'color': 'red'}, 'debug': {'bold': True, 'color': 'black'}, 'error': {'color': 'red'}, 'info': {'color': 'green'}, 'notice': {'color': 'magenta'}, 'spam': {'color': 'green', 'faint': True}, 'success': {'bold': True, 'color': 'green'}, 'verbose': {'color': 'blue'}, 'warning': {'color': 'yellow'}}

#std = logging.StreamHandler()
#std.setFormatter(formatter)
#fl = logging.FileHandler("pipikLog.txt")
#fl.setFormatter(formatter)
if args.debug:
    pipikLogger.setLevel(logging.DEBUG)
    #std.setLevel(logging.DEBUG)
    #fl.setLevel(logging.INFO)
    coloredlogs.install(level='DEBUG', logger=pipikLogger,fmt=fmt)
else:
    pipikLogger.setLevel(logging.INFO)
    #std.setLevel(logging.INFO)
    #fl.setLevel(logging.INFO)
    coloredlogs.install(level='INFO', logger=pipikLogger,fmt=fmt)
#pipikLogger.addHandler(std)
#pipikLogger.addHandler(fl)

if not args.minimal and not args.no_sympy:
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
# TODO properly integrate matstat stuff, maybe put all subcommands into slashotpion with autocomplete
# TODO make emojis for pills
# TODO make a better help command
# TODO make pipikbot users a dict of id:user instead of a list of users, also redo the getUserFromDC func then
# TODO make an actual lobby extension
# TODO make pills buttons edit message not reply
# TODO In math when returning the latex, invert the black text in pillow? that takes time tho to upload
# TODO merge caesar, clownize, t9 ize into one context command
# TODO maybe make some mafia type game but rebrand it to some discord admins and mods vs spammers and use right click user commands

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

def getCommandId(command) -> dict:
    # every = client.get_application_commands()
    # for i in every:
    #     if i.name == command:
    #         ids = {}
    #         for guild, value in i.command_ids.items():
    #             if guild is not None:
    #                 ids.update({client.get_guild(guild).name: value})
    #             else:
    #                 ids.update({"Global": value})
    #         return {command: ids}

    return {command: {client.get_guild(i[0][0]) or "Global": i[0][1] for i in (tuple(comm.command_ids.items()) for comm in (comm for comm in client.get_application_commands() if comm.name == command))}}

def mentionCommand(command, guild: int = None) -> str:
    ids = getCommandId(command.split(" ")[0])
    iddict = list(ids.values())[0]
    if guild is not None:
        if int(guild) in iddict:
            return f"`</{command}:{iddict[int(guild)]}>`"
    return f"`</{command}:{iddict['Global']}>`"

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
               arg:str = discord.SlashOption(name="format", description="raw = copypasteable, full = not relative", required=False,choices=["raw", "full", "raw+full"],default=""),
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
        style = 'F' if "full" in arg else 'R'
        israw = "raw" in arg
        mention = f"{'`' if israw else ''}{discord.utils.format_dt(timestr,style=style)}{'`' if israw else ''}"
        await ctx.send(message.format(mention) if message and "{}" in message else f"{message} {mention}" if message else mention)
    except Exception as e:
        raise e
        #await ctx.send(e)

#@client.slash_command(name="muv", description="semi", guild_ids=[860527626100015154, 601381789096738863])
#async def movebogi(ctx, chanel: discord.abc.GuildChannel):
#    await ctx.user.move_to(chanel)

# @client.slash_command(name="muvraw", description="semi", guild_ids=[860527626100015154, 601381789096738863])
# async def movebogi2(ctx, chanel):
#     chanel = ctx.guild.get_channel(int(chanel))
#     await ctx.user.move_to(chanel)

@client.message_command(name="Unemojize")
async def unemojize(interaction, message):
    await interaction.response.send_message(f"`{emoji.demojize(message.content)}`", ephemeral=True)

@client.message_command(name="Spongebob mocking")  # pelda jobbklikk uzenetre commandra
async def randomcase(interaction, message):
    assert message.content
    await interaction.send("".join(random.choice([betu.casefold(), betu.upper()]) for betu in message.content) + " <:pepeclown:803763139006693416>")

@client.command()
async def initiatespeh(ctx):
    global spehmode
    spehmode = not spehmode
    print("speh initiated")

@client.slash_command(name="run", description="For running python code")
async def run(ctx: discord.Interaction, command):
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
        #async with ctx.channel.typing():
        await ctx.response.defer()
        a = eval(command)
        await ctx.send(a)
    except Exception as a:
        await ctx.send(a)

discord_emotes = {}

@client.event
async def on_ready():
    game = discord.Game(f"{linecount} lines of code; V3.5! use /help")
    await client.change_presence(status=discord.Status.online, activity=game)
    print(f"Signed in at {datetime.now()}")
    pipikLogger.info(f"{time_module.perf_counter() - start} Bootup time")

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
if not args.minimal and not args.no_sympy:
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

allcogs = [cog for cog in os.listdir("./cogs") if cog.endswith(".py")]
if args.minimal:
    cogs = ["testing.py"]
else:
    cogs = allcogs[:]
    for cog in reversed(cogs):
        if cog.endswith("cog.py"):
            if args.__getattribute__(f"no_{cog.removesuffix('cog.py')}") or args.minimal:
                cogs.remove(cog)
cogs.remove("testing.py") if args.no_testing else None

for n, file in enumerate(cogs, start=1): #its in two only because i wouldnt know how many cogs to load and so dont know how to format loading bar
    with open("./cogs/"+file, "r", encoding="UTF-8") as f:
        linecount += len(f.readlines())
    client.load_extension("cogs." + file[:-3],extras={"baselogger":pipikLogger})
    sys.stdout.write(f"\rLoading... {(n / len(cogs)) * 100:.2f}% [{(int((n/len(cogs))*10)*'=')+'>':<10}]")
    sys.stdout.flush()
sys.stdout.write(f"\r{len(cogs)}/{len(allcogs)} cogs loaded.                    \n")
sys.stdout.flush()
os.chdir(root)

client.run(os.getenv("MAIN_DC_TOKEN"))  # bogibot

# 277129587776 reduced perms
# https://discord.com/api/oauth2/authorize?client_id=618079591965392896&permissions=543652576368&scope=bot%20applications.commands bogibot