import json
import sys
from collections import defaultdict
from io import BytesIO
from typing import Optional
import nextcord as discord
import random
import nextcord.ext.commands
import numpy as np
from nextcord.ext import commands
from datetime import datetime, timedelta
from pycaw.utils import AudioUtilities
from utils.antimakkcen import antimakkcen
import emoji
import os
import argparse
import time as time_module
import logging
from dotenv import load_dotenv
import coloredlogs
from sympy import Sum
from PIL import Image, ImageDraw, ImageFont
from utils.mentionCommand import mentionCommand

start = time_module.perf_counter()
version = 3.7
load_dotenv(r"./credentials/main.env")

parser = argparse.ArgumentParser(prog=f"PipikBot V{version}", description='A fancy discord bot.', epilog="Written by theonlypeti.")

for cog in os.listdir("./cogs"):
    if cog.endswith("cog.py"):
        parser.add_argument(f"--no_{cog.removesuffix('cog.py')}", action="store_true", help=f"Disable {cog} extension.")

parser.add_argument("--minimal", action="store_true", help="Disable most of the extensions.")
parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
parser.add_argument("--no_testing", action="store_true", help="Disable testing module.")
parser.add_argument("--logfile", action="store_true", help="Turns on logging to a text file.")
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
if args.logfile:
    pipikLogger.setLevel(5)
if args.debug:
    # pipikLogger.setLevel(logging.DEBUG)
    #std.setLevel(logging.DEBUG)
    #fl.setLevel(logging.INFO)
    coloredlogs.install(level='DEBUG', logger=pipikLogger, fmt=fmt)
else:
    # pipikLogger.setLevel(logging.INFO)
    #std.setLevel(logging.INFO)
    #fl.setLevel(logging.INFO)
    coloredlogs.install(level='INFO', logger=pipikLogger, fmt=fmt)
    # coloredlogs.install(level=5, logger=pipikLogger, fmt=fmt)
#pipikLogger.addHandler(std)
#pipikLogger.addHandler(fl)

if args.logfile: #if you need a text file
    FORMAT = "[{asctime}][{filename}][{lineno:4}][{funcName}][{levelname}] {message}"
    formatter = logging.Formatter(FORMAT, style="{")  #this is for default logger
    filename = f"./logs/bot_log_{datetime.now().strftime('%m-%d-%H-%M-%S')}.txt"
    os.makedirs(r"./logs", exist_ok=True)
    with open(filename, "w") as f:
        pass
    fl = logging.FileHandler(filename)
    fl.setFormatter(formatter)
    fl.setLevel(5)
    logging.addLevelName(5, "Message")
    fl.addFilter(lambda rec: rec.levelno < 10)
    pipikLogger.addHandler(fl)


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
discord_emotes = {}
timeouts = defaultdict(int)
stunlocked = None

intents = discord.Intents.all() #TODO remember what do i use members intent for?!?!! update: members is used when checking if guild is premium for example
intents.presences = False
intents.typing = True

client = commands.Bot(command_prefix='&', intents=intents, chunk_guilds_at_startup=True, status=discord.Status.online, activity=discord.Game(name="Booting up...")) #TODO chunk_guilds_at_startup=False might help me
client.remove_command('help')

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
# TODO merge caesar, clownize, t9 ize into one context command
# TODO maybe make some mafia type game but rebrand it to some discord admins and mods vs spammers and use right click user commands
# TODO play with this  if interaction.user.guild_permissions.administrator:
# TODO play with ClientCog and its application_commands property

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

# @client.message_command(name="En-/Decrypt")
# async def caesar(interaction, text):
#     if text.type == discord.MessageType.chat_input_command and text.embeds[0].title == "Message":
#         text = text.embeds[0].description
#     else:
#         text = text.content
#     await interaction.send("".join([chr(((ord(letter) - 97 + 13) % 26) + 97) if letter.isalpha() and letter.islower() else chr(((ord(letter) - 65 + 13) % 26) + 65) if letter.isalpha() and letter.isupper() else letter for letter in text]))

class CaesarModal(discord.ui.Modal):
    def __init__(self, title):
        super().__init__(title=title)
        self.inputtext = discord.ui.TextInput(label="Input the text", style=discord.TextInputStyle.paragraph)
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

@client.slash_command(description="Yes or no", name="yesorno")
async def yesorno(ctx: discord.Interaction, question: Optional[str]):
    if not question:
        await ctx.send("https://cdn.discordapp.com/attachments/607897146750140457/1040242560964251678/3d-yes-or-no-little-man-drawings_csp19386099.jpg")
    else:
        img = Image.open(r"data/yesorno.jpeg")
        d = ImageDraw.Draw(img)
        textsize = img.width * (1/(len(question)))
        textsize = int(np.clip(textsize, 25, 60))
        fnt = ImageFont.truetype('impact.ttf', size=textsize)

        newquestion = ""
        for i in range(0,len(question), 38):
            newquestion += question[i:i+38] + "\n"

        textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100, "fill": (255, 255, 255), "anchor": "mm"}
        d.multiline_text((img.width / 2, textsize + (textsize * len(question)//38)), newquestion, **textconfig)
        with BytesIO() as image_binary:
            img.save(image_binary, "jpeg")
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename=f'yesorno.jpeg'))
    mesage = await ctx.original_message()
    await mesage.add_reaction("<:yes:1040243872095281152>")
    await mesage.add_reaction("<:no:1040243824489943040>")


class BfModal(discord.ui.Modal):
    def __init__(self, title):
        super().__init__(title=title)
        self.codetext = discord.ui.TextInput(label="Input the code", style=discord.TextInputStyle.paragraph,default_value="+[-->-[>>+>-----<<]<--<---]>-.>>>+.>>..+++[.>]<<<<.+++.------.<<-.>>>>+.")
        self.add_item(self.codetext)

        self.inputtext = discord.ui.TextInput(label="input from user (if any)", required=False, style=discord.TextInputStyle.paragraph, placeholder="123")
        self.add_item(self.inputtext)

    async def callback(self, ctx):
        output = bf(self.codetext.value, self.inputtext.value)
        embedVar = discord.Embed(title="Brainfuck code output", type="rich", description=output)
        embedVar.set_author(name=ctx.user.display_name, icon_url=ctx.user.avatar.url)
        await ctx.send(embed=embedVar)

@client.slash_command(description="Brainfuck interpreter", name="brainfuck")
async def bf_modal(ctx):
    modal = BfModal(title="Brainfuck")
    await ctx.response.send_modal(modal)

#@commands.has_permissions(manage_server=True)
@client.slash_command(name="pfp", description="chooses a random emote for the servers profile pic.",guild_ids=[860527626100015154, 552498097528242197], dm_permission=False)
async def pfp(interaction: discord.Interaction):
    os.chdir("D:\\Users\\Peti.B\\Pictures\\microsoft\\emotes")
    emotes = [emote for emote in os.listdir() if not emote.endswith(".gif") or interaction.guild.premium_tier]
    await interaction.send(f"Picking from {len(emotes)} emotes...")
    img = random.choice(emotes)
    print(img)
    with open(img, "rb") as file:
        await interaction.guild.edit(icon=file.read())
    os.chdir(root)

@client.slash_command(name="ticho", description="Uber hlasitost", guild_ids= (860527626100015154,))
async def ticho(ctx: discord.Interaction, message: Optional[str]):
    ogname = ctx.guild.me.display_name
    await ctx.guild.me.edit(nick=ctx.user.name)
    for session in AudioUtilities.GetAllSessions():
        if session.Process and session.Process.name() in ("chrome.exe", "JetAudio.exe"):
            session.SimpleAudioVolume.SetMasterVolume(session.SimpleAudioVolume.GetMasterVolume()/3, None)
    await ctx.send(content=message or "Tíško si poprosím", tts=True)
    await ctx.guild.me.edit(nick=ogname)

@client.slash_command(name="time", description="/time help for more info")
async def time(ctx,
               time: str = discord.SlashOption(name="time", description="Y.m.d H:M or H:M or relative (minutes=30 etc...)"),
               arg: str = discord.SlashOption(name="format", description="raw = copypasteable, full = not relative", required=False, choices=["raw", "full", "raw+full"], default=""),
               message: str = discord.SlashOption(name="message", description="Your message to insert the timestamp into, use {} as a placeholder", required=False)):
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
            embedVar.add_field(name="optional arg: raw/full/raw+full", value="raw= Copy pasteable timestamp\nfull= Written out date instead of relative time")
            embedVar.add_field(name="optional message:", value="Brb {}; Meeting starts at {} be there!")
            await ctx.send(embed=embedVar)
            return
        style = 'F' if "full" in arg else 'R'
        israw = "raw" in arg
        mention = f"{'`' if israw else ''}{discord.utils.format_dt(timestr,style=style)}{'`' if israw else ''}"
        await ctx.send(message.format(mention) if message and "{}" in message else f"{message} {mention}" if message else mention)
    except Exception as e:
        await ctx.send(e)

#@client.slash_command(name="muv", description="semi", guild_ids=[860527626100015154, 601381789096738863])
#async def movebogi(ctx, chanel: discord.abc.GuildChannel):
#    await ctx.user.move_to(chanel)

# @client.slash_command(name="muvraw", description="semi", guild_ids=[860527626100015154, 601381789096738863])
# async def movebogi2(ctx, chanel):
#     chanel = ctx.guild.get_channel(int(chanel))
#     await ctx.user.move_to(chanel)

# @client.message_command(name="Unemojize")
# async def unemojize(interaction, message):
#     await interaction.response.send_message(f"`{emoji.demojize(message.content)}`", ephemeral=True)

@client.message_command(name="Mocking clown")
async def randomcase(interaction, message):
    assert message.content
    await interaction.send("".join(random.choice([betu.casefold(), betu.upper()]) for betu in message.content) + " <:pepeclown:803763139006693416>")

@client.user_command(name="FbAnna profilka")
async def flowersprofilka(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()
    with BytesIO() as image:
        await user.display_avatar.save(image)
        img = Image.open(image)
        for i in range(56):
            mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
            mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
            virag = mappa + "/" + random.choice(os.listdir(mappa))
            with open(virag, "rb") as file:
                virag = Image.open(file)
                size = img.width//8
                virag.thumbnail((size, size))
                img.paste(virag, (random.choice([i for i in range(-size//3, int(img.width-(size*1))) if i not in range(size*1, img.width-size*3)]), random.randint(0, img.height-size*2)), virag)

        for i in range(24):
            mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
            mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
            virag = mappa + "/" + random.choice(os.listdir(mappa))
            with open(virag, "rb") as file:
                virag = Image.open(file)
                size = img.width//8
                virag.thumbnail((size, size))
                img.paste(virag, (random.randint(0, img.width), random.randint(img.height-size*2, img.height-size)), virag)

        d = ImageDraw.Draw(img)
        fnt = ImageFont.truetype('FREESCPT.TTF', size=size)

        textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100, "fill": (255, 255, 255), "anchor": "mm"}

        #szoveg = random.choice(("Jó éjszakát mindenkinek", "Kellemes ünnepeket", "Áldott hétvégét kívánok", "Meghalt a Jóska xd"))
        szoveg = random.choice(("Dobrú noc vám prajem!","Pozehnaný víkend vám prajem!","Kávicka pohodicka","Príjemné popoludnie prajem!"))
        d.multiline_text((img.width / 2, img.height - size), szoveg, **textconfig)

    with BytesIO() as image_binary:
        img.save(image_binary, "PNG")
        image_binary.seek(0)
        await interaction.send(file=discord.File(image_binary, "flowers.PNG"))

@client.user_command(name="Stunlock",guild_ids=(601381789096738863,))
async def flowersprofilka(interaction: discord.Interaction, user: discord.User):
    global stunlocked
    if stunlocked == user:
        stunlocked = None
    else:
        stunlocked = user
    await interaction.send(f"Stunlokced {stunlocked}",ephemeral=True)

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
        await ctx.response.defer()
        a = eval(command)
        await ctx.send(a)
    except Exception as a:
        await ctx.send(f"{a}")

@client.event
async def on_ready():
    global timeouts
    print(f"Signed in at {datetime.now()}")
    pipikLogger.info(f"{time_module.perf_counter() - start} Bootup time")
    game = discord.Game(f"{linecount} lines of code; V{version}! Use /help")  # dont even try to move this believe me ive tried
    await client.change_presence(activity=game)
    #print("\n".join(i.name for i in client.get_application_commands()))
    try:
        with open("timeouts.txt", "r") as file:
            timeouts = defaultdict(int)
            for k,v in json.load(file).items():
                timeouts.update({k: v})
    except IOError:
        with open("timeouts.txt", "w") as file:
            json.dump({}, file, indent=4)
    pipikLogger.debug(timeouts)

@client.event
async def on_disconnect():
    global start
    start = time_module.perf_counter()

@client.event
async def on_message(msg: nextcord.Message):
    if not msg.author.bot:
        # if ctx.guild.id == 601381789096738863:
        #     await ctx.add_reaction("<:kekw:800726027290148884>")
        if args.logfile:
            tolog = f"{msg.author} said ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} in {emoji.demojize(msg.channel.name)} at {str(datetime.now())}"
            pipikLogger.log(5, tolog)
        if msg.attachments:
            for att in msg.attachments:
                ...  # todo implement image saving? but only on prepinač
        if "free nitro" in antimakkcen(msg.content).casefold():
            await msg.channel.send("bitch what the fok **/ban**")
    await client.process_commands(msg)

@client.event
async def on_typing(channel: discord.TextChannel, who: discord.Member, when: datetime):
    if stunlocked:
        if who.id == stunlocked.id:
            await who.timeout(timedelta(seconds=15), reason="Te csak ne írjál")
            await channel.send(f"Te csak ne írjál semmit, {who.display_name}.")

@client.event
async def on_reaction_add(reaction: discord.Reaction, user):
    if reaction.message.author.bot:
        return

    good_responses = ("Azta de vicces valaki <:hapi:889603218273878118> 👌",
                      f"Gratulálunk, ez vicces volt, {reaction.message.author.display_name}. {emoji.emojize(':clap:')} {emoji.emojize(':partying_face:')}",
                      "Damn, you got the whole squad laughing <:hapi:889603218273878118>",
                      "Hát ez odabaszott xd",
                      "xddd",
                      "Kiégtem",
                      "Bruh miafasz xd",
                      "Hát ilyet még nem baszott a világ <:kekcry:956217725880000603> <:hapi:889603218273878118>",
                      "Azért ennyire ne <:kekcry:956217725880000603>",
                      "Jolvan nembirom xdddd",
                      "Hát ez a földhöz baszott <:kekcry:956217725880000603>",
                      "Sikítok xddd",
                      "Ez sok nekem <:kekcry:956217725880000603>",
                      "Sípolok xdd",
                      "Beszarok gec <:kekcry:956217725880000603> <:kekcry:956217725880000603>",
                      "Leköptem a laptopom xddd",
                      "Mekkora komedista <:hapi:889603218273878118>"
                      )
    global already_checked, timeouts

    if str(reaction.emoji) in ("<:kekcry:871410695953059870>", "<:kekw:800726027290148884>", "<:hapi:889603218273878118>", ":joy:"):
        #if reaction.message.author.id in (569937005463601152, 422386822350635008):
        if True:
            if user.id == reaction.message.author.id: # (569937005463601152, 422386822350635008):
                kapja: discord.Member = reaction.message.author
                already_checked.append(reaction.message.id)
                timeout = timeouts.get(str(kapja.id), 0)
                uzenet = discord.Embed(description="Imagine saját vicceiden nevetni. <:bonkdoge:950439465904644128> <a:catblushy:913875026606948393>")
                uzenet.set_footer(text=f"Current timeout is at {2 ** timeout} minutes.")
                await reaction.message.reply(embed=uzenet)
                await kapja.timeout(timedelta(minutes=2 ** timeout), reason="Saját magára rakta a keket")
                timeouts[str(kapja.id)] += 1
                pipikLogger.debug(timeouts)

    if str(reaction.emoji) in (":thumbs_down:","<:2head:913874980033421332>","<:bruh:913875008697286716>","<:brainlet:766681101305118721>","<:whatchamp:913874952887873596>"):
        #if reaction.message.author.id in (569937005463601152, 422386822350635008): #csak bocira timeout
        if True: #mindenkire timeout
            kapja = reaction.message.author
            timeout = timeouts.get(str(kapja.id), 0)
            if reaction.count >= 3:
                if reaction.message.id not in already_checked:
                    already_checked.append(reaction.message.id)
                    await kapja.timeout(timedelta(minutes=2 ** timeout), reason="Nem volt vicces")
                    uzenet = discord.Embed(description=f"Nem volt vicces, {reaction.message.author.display_name} <:nothapi:1007757789629796422>.")
                    uzenet.set_footer(text=f"Current timeout is at {2 ** timeout} minutes.")
                    await reaction.message.reply(embed=uzenet)
                    timeouts[str(kapja.id)] += 1
                    pipikLogger.debug(timeouts)


    if str(reaction.emoji) in ("<:kekcry:871410695953059870>", "<:kekw:800726027290148884>",  "<:hapi:889603218273878118>", ":joy:"):
        #if reaction.message.author.id == 569937005463601152:
        if True:
            if reaction.count >= 3:
                if reaction.message.id not in already_checked:
                    already_checked.append(reaction.message.id)
                    uzenet = random.choice(good_responses)
                    await reaction.message.reply(uzenet)
                    try:
                        timeouts[str(reaction.message.author.id)] -= 1
                        pipikLogger.debug(timeouts)
                    except KeyError as e:
                        pipikLogger.info(e)

    if args.logfile:
        tolog = f"{user} reacted {(emoji.demojize(reaction.emoji) if isinstance(reaction.emoji, str) else reaction.emoji.name)} in {reaction.channel.name} at {str(datetime.now())}"
        pipikLogger.log(5, tolog)
        print("react at:", str(datetime.now()), (emoji.demojize(reaction.emoji) if isinstance(reaction.emoji, str) else reaction.emoji.name), "by:", user, "on message:", reaction.message.content, "in:", reaction.message.channel)

    with open("timeouts.txt", "w") as file:
        json.dump(timeouts, file, indent=4)

# @client.slash_command(name="banboci", description="Timeout boci mindkét accját.",guild_ids=(601381789096738863,), dm_permission=False)
# async def banboci(interaction: discord.Interaction, minutes: float, reason: str):
#     boci1: discord.Member = interaction.guild.get_member(569937005463601152)
#     await boci1.timeout(timeout=timedelta(minutes=minutes), reason=reason)
#     boci2: discord.Member = interaction.guild.get_member(422386822350635008)
#     await boci2.timeout(timeout=timedelta(minutes=minutes), reason=reason)
#     await interaction.send(f"Timeouted both Boci accounts for {minutes} minutes, reason: {reason}")


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
            if args.__getattribute__(f"no_{cog.removesuffix('cog.py')}"):
                cogs.remove(cog)
cogs.remove("testing.py") if args.no_testing else None

for n, file in enumerate(cogs, start=1): #its in two only because i wouldnt know how many cogs to load and so dont know how to format loading bar
    with open("./cogs/"+file, "r", encoding="UTF-8") as f:
        linecount += len(f.readlines())
    client.load_extension("cogs." + file[:-3], extras={"baselogger": pipikLogger})
    if not args.debug:
        sys.stdout.write(f"\rLoading... {(n / len(cogs)) * 100:.2f}% [{(int((n/len(cogs))*10)*'=')+'>':<10}]")
        sys.stdout.flush()
sys.stdout.write(f"\r{len(cogs)}/{len(allcogs)} cogs loaded.                    \n")
sys.stdout.flush()
os.chdir(root)

client.run(os.getenv("MAIN_DC_TOKEN"))  # bogibot

# 277129587776 reduced perms
# https://discord.com/api/oauth2/authorize?client_id=618079591965392896&permissions=543652576368&scope=bot%20applications.commands bogibot