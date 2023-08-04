import json
import sys
from collections import defaultdict
from io import BytesIO
from typing import Coroutine
import nextcord as discord
import random
import nextcord.ext.commands
from numpy import clip
from nextcord.ext import commands
from datetime import datetime, timedelta
from utils.antimakkcen import antimakkcen
import emoji
import os
import argparse
import time as time_module
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from sympy import Sum
from utils.mentionCommand import mentionCommand
from utils.getMsgFromLink import getMsgFromLink
from utils import mylogger


start = time_module.perf_counter()
version = 3.8
load_dotenv(r"./credentials/main.env")

parser = argparse.ArgumentParser(prog=f"PipikBot V{version}", description='A fancy discord bot.', epilog="Written by theonlypeti.")

for cog in os.listdir("./cogs"):
    if cog.endswith("cog.py"):
        parser.add_argument(f"--no_{cog.removesuffix('cog.py')}", action="store_true", help=f"Disable {cog} extension.")
        parser.add_argument(f"--only_{cog.removesuffix('cog.py')}", action="store_true", help=f"Enable only the {cog} extension.")

parser.add_argument("--minimal", action="store_true", help="Disable most of the extensions.")
parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
parser.add_argument("--no_testing", action="store_true", help="Disable testing module.")
parser.add_argument("--only_testing", action="store_true", help="Add testing module.")
parser.add_argument("--logfile", action="store_true", help="Turns on logging to a text file.")
parser.add_argument("--no_linecount", action="store_true", help="Turns off line counting.")
args = parser.parse_args()

mylogger.main(args) #initializing the logger
from utils.mylogger import baselogger as pipikLogger

if args.logfile:
    pipikLogger.setLevel(5)

if not args.minimal and not args.no_sympy:
    import utils.matstatMn
    prikazy = list(filter(lambda a: not a.startswith("_"), dir(utils.matstatMn)))
    [prikazy.remove(i) for i in ("lru_cache", "graf", "plt", "prod", "kocka", "minca", "napoveda")]

    from utils.matstatMn import *

root = os.getcwd()  # "F:\\Program Files\\Python39\\MyScripts\\discordocska\\pipik"

already_checked = []
discord_emotes = {}
timeouts = defaultdict(int)
us = set()

intents = discord.Intents.all() #TODO remember what do i use members intent for?!?!! update: members is used when checking if guild is premium for example
intents.presences = False
intents.typing = True

#bot = commands.Bot(intents=intents, chunk_guilds_at_startup=False, member_cache_flags=nextcord.MemberCacheFlags.none())
client = commands.Bot(command_prefix='&', intents=intents, chunk_guilds_at_startup=True, status=discord.Status.offline, activity=discord.Game(name="Booting up...")) #TODO chunk_guilds_at_startup=False might help me
client.remove_command('help')

# TODO play with this @commands.has_permissions(manage_server=True) only applicable to prefix commands, slash has smth else
# TODO colored ansi text
# TODO video.py
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
# TODO webhooks can send ephemeral messages
# TODO command maker for users, and like on message command maker
# TODO replace every list typehint with Sequence or MutableSequence or smth or Iterable
# TODO a database abstraction for myself
# TODO selectmenu for bp temy to open their desc and availability in a embed, then the pagi arrows would cycle through the bp temy one by one + button for english

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

@client.event
async def on_ready():
    global timeouts, us
    print(f"Signed in at {datetime.now()}")
    pipikLogger.info(f"{time_module.perf_counter() - start} Bootup time")
    game = discord.Game(f"{linecount} lines of code; V{version}! Use /help")  # dont even try to move this believe me ive tried
    await client.change_presence(activity=game)
    #print("\n".join(i.name for i in client.get_application_commands()))
    try:
        with open("timeouts.txt", "r") as file:
            timeouts = defaultdict(int)
            for k, v in json.load(file).items():
                timeouts.update({k: v})
    except IOError:
        with open("timeouts.txt", "w") as file:
            json.dump({}, file, indent=4)
    readus()
    pipikLogger.debug(timeouts)

def writeus(): #TODO move this to misc
    with open(r"data/us.txt", "w") as file:
        json.dump(list(us), file, indent=4)



def readus():
    global us
    try:
        with open(r"data/us.txt", "r") as file:
            us = set(json.load(file))
            pipikLogger.debug(f"Read {len(us)} us from file")
    except IOError as e:
        pipikLogger.error(e)
        with open(r"data/us.txt", "w") as file:
            json.dump([], file, indent=4)

@client.event
async def on_disconnect():
    global start
    start = time_module.perf_counter()

@client.event
async def on_message_delete(msg: nextcord.Message):
    if not msg.author.bot:
        # if ctx.guild.id == 601381789096738863:
        #     await ctx.add_reaction("<:kekw:800726027290148884>")
        if args.logfile:
            tolog = f"{msg.author} said ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} in {msg.channel.name} at {str(datetime.now())}"
            tolog = emoji.demojize(antimakkcen(tolog)).encode('ascii', "ignore").decode()
            pipikLogger.log(5, tolog)
        if msg.attachments:
            for att in msg.attachments:
                ...  # todo implement image saving? but only on prepinač


@client.event
async def on_message(msg: nextcord.Message):
    if "free nitro" in antimakkcen(msg.content).casefold():
        await msg.channel.send("bitch what the fok **/ban**")
    else:
        if msg.guild:
            # if msg.guild.id in (691647519771328552,):
            #     tolog = f"{msg.author} sent: ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} in {msg.channel} at {str(datetime.now())}"
            #     tolog = emoji.demojize(antimakkcen(tolog)).encode('ascii', "ignore").decode()
            #     pipikLogger.info(tolog)

            if msg.guild.id not in (800196118570205216,):
                words = msg.content.split(" ")
                for word in words:
                    if (word.lower().endswith("us") or word.lower().endswith("usz")) and len(word) > 4 and word.lower() not in us:
                        us.add(word.lower())
                        writeus()
                        img = Image.open(r"data/amogus.png") #TODO extract this writing thing to a func?
                        d = ImageDraw.Draw(img)
                        textsize = img.width * (1 / (len(word)))
                        textsize = int(clip(textsize, 25, 60))
                        fnt = ImageFont.truetype('impact.ttf', size=textsize)

                        newquestion = ""
                        for i in range(0, len(word), 38):
                            newquestion += word[i:i + 38] + "\n"

                        textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100,
                                      "fill": (255, 255, 255), "anchor": "mm"}
                        d.multiline_text((img.width / 2, textsize + (textsize * len(word) // 38)), newquestion,
                                         **textconfig)
                        with BytesIO() as image_binary:
                            img.save(image_binary, "png")
                            image_binary.seek(0)
                            await msg.reply(file=discord.File(fp=image_binary, filename=f'amogus.png'))
                        break
        else:
            tolog = f"{msg.author} sent dm: ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} in {msg.channel.recipient} at {str(datetime.now())}"
            tolog = emoji.demojize(antimakkcen(tolog)).encode('ascii', "ignore").decode()
            pipikLogger.info(tolog)

    await client.process_commands(msg)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.Member):
    if reaction.message.author.bot or user.bot:
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

    if str(reaction.emoji) in ("<:kekcry:871410695953059870>", "<:kekw:800726027290148884>", "<:hapi:889603218273878118>", ":joy:", "<:kekw:1101064898391314462>",":rofl:"):
        #if reaction.message.author.id in (569937005463601152, 422386822350635008):
        if reaction.message.guild.id in (601381789096738863, 691647519771328552):
        # if True:
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

    elif emoji.demojize(str(reaction.emoji)) in (":thumbs_down:", "<:2head:913874980033421332>", "<:bruh:913875008697286716>", "<:brainlet:766681101305118721>","<:whatchamp:913874952887873596>"):
        #if reaction.message.author.id in (569937005463601152, 422386822350635008): #csak bocira timeout
        # if True: #mindenkire timeout
        if reaction.message.guild.id in (601381789096738863, 691647519771328552):
            kapja = reaction.message.author
            timeout = timeouts.get(str(kapja.id), 0)
            if reaction.count >= 3:
                if reaction.message.id not in already_checked:
                    already_checked.append(reaction.message.id)
                    await kapja.timeout(timedelta(minutes=2 ** timeout), reason="Nem volt vicces")
                    uzenet = discord.Embed(description=random.choice((f"Nem volt vicces, {reaction.message.author.display_name} <:nothapi:1007757789629796422>.","Ki kérdezett")))
                    uzenet.set_footer(text=f"Current timeout is at {2 ** timeout} minutes.")
                    await reaction.message.reply(embed=uzenet)
                    timeouts[str(kapja.id)] += 1
                    pipikLogger.debug(timeouts)


    if emoji.demojize(str(reaction.emoji)) in ("<:kekcry:871410695953059870>", "<:kekw:800726027290148884>", "<:hapi:889603218273878118>", ":joy:", "<:kekw:1101064898391314462>",":rofl:"):
        #if reaction.message.author.id == 569937005463601152:
        # if True:
        if reaction.message.guild.id in (601381789096738863, 691647519771328552):
            if reaction.count >= 3:
                if reaction.message.id not in already_checked:
                    already_checked.append(reaction.message.id)
                    uzenet = random.choice(good_responses)
                    sent = reaction.message.created_at
                    tz_info = sent.tzinfo
                    now = datetime.now(tz_info)
                    if (now - sent) < timedelta(minutes=10):
                        await reaction.message.reply(uzenet, mention_author=True)
                    else:
                        await reaction.message.reply(uzenet, mention_author=False)
                    try:
                        timeouts[str(reaction.message.author.id)] -= 1
                        pipikLogger.debug(timeouts)
                    except KeyError as e:
                        pipikLogger.info(e)

    if args.logfile:
        tolog = f"{user} reacted [{(reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name)}] in {reaction.message.channel.name} at {str(datetime.now())}"
        tolog = emoji.demojize(antimakkcen(tolog)).encode('ascii', "ignore").decode()
        pipikLogger.log(5, tolog)
        print("react at:", str(datetime.now()), (emoji.demojize(reaction.emoji) if isinstance(reaction.emoji, str) else reaction.emoji.name), "by:", user, "on message:", reaction.message.content or reaction.message.jump_url, "in:", reaction.message.channel)

    with open(r"data/timeouts.txt", "w") as file:
        json.dump(timeouts, file, indent=4)
    return reaction, user


@client.slash_command(name="run", description="For running python code")
async def run(ctx: discord.Interaction, command: str):
    if "@" in command and ctx.user.id != 617840759466360842:
        await ctx.send("oi oi oi we pinging or what?")
        return
    if any((word in command for word in ("open(", "os.", "eval(", "exec("))) and ctx.user.id != 617840759466360842:
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

@client.slash_command(name="arun", description="For running async python code")
async def arun(ctx: discord.Interaction, command: str):
    if "@" in command and ctx.user.id != 617840759466360842:
        await ctx.send("oi oi oi we pinging or what?")
        return
    if any((word in command for word in
            ("open(", "os.", "eval(", "exec("))) and ctx.user.id != 617840759466360842:
        await ctx.send("oi oi oi we hackin or what?")
        return
    elif "redditapi" in command and ctx.user.id != 617840759466360842:
        await ctx.send("Lol no sorry not risking anyone else doing stuff with MY reddit account xDDD")
        return
    try:
        await ctx.response.defer()
        commands = command.split(";")
        for command in commands:
            if isinstance(command, str):
                if command.startswith("*"):
                    commands.extend(eval(command[1:]))
                    continue
                try:
                    a = await eval(command)
                except TypeError:
                    a = eval(command)
                except Exception as e:
                    await ctx.send(e)
                    continue
                await ctx.send(a)
            elif isinstance(command, Coroutine):
                a = await command
                await ctx.send(a)
    except Exception as a:
        await ctx.send(f"{a}")


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
if not args.minimal and not args.no_sympy: #TODO does not take into consideration the only_ keyword arguments
    utils = [file for file in os.listdir(r"./utils") if file.endswith(".py")]
    files = utils + [r"../pipikNextcord.py"]
    linecount = 197  # matstatMn is added manually cuz i have a million commented lines after if __name__ == __main__
else:
    files = (r"../pipikNextcord.py",) # TODO somehow make sure i can rename the file and it still works __file__ is not working
    linecount = 0
for file in files:
    if file.endswith(".py"):
        with open(root+r"/utils/"+file, "r", encoding="UTF-8") as f:
            linecount += len(f.readlines())

allcogs = [cog for cog in os.listdir("./cogs") if cog.endswith("cog.py")] + ["testing.py"]
cogcount = len(allcogs)
cogs = []
if not args.minimal:  # if not minimal
    if not [not cogs.append(cog) for cog in allcogs if args.__getattribute__(f"only_{cog.removesuffix('cog.py').removesuffix('.py')}")]: #load all the cogs that are marked to be included with only_*
        cogs = allcogs[:]  # if no cogs are marked to be exclusively included, load all of them
        for cog in reversed(cogs):  # remove the cogs that are marked to be excluded with no_*
            if args.__getattribute__(f"no_{cog.removesuffix('cog.py').removesuffix('.py')}"):  # if the cog is marked to be excluded
                cogs.remove(cog)  # remove it from the list of cogs to be loaded
cogs.remove("testing.py") if args.no_testing else None  # remove testing.py from the list of cogs to be loaded if testing is disabled

for n, file in enumerate(cogs, start=1): #its in two only because i wouldnt know how many cogs to load and so dont know how to format loading bar
    if not args.no_linecount:
        with open("./cogs/"+file, "r", encoding="UTF-8") as f:
            linecount += len(f.readlines())
    client.load_extension("cogs." + file[:-3], extras={"baselogger": pipikLogger})
    if not args.debug:
        sys.stdout.write(f"\rLoading... {(n / len(cogs)) * 100:.02f}% [{(int((n/len(cogs))*10)*'=')+'>':<10}]")
        sys.stdout.flush()
sys.stdout.write(f"\r{len(cogs)}/{cogcount} cogs loaded.".ljust(50)+"\n")
sys.stdout.flush()
os.chdir(root)

client.run(os.getenv("MAIN_DC_TOKEN"))

# 277129587776 reduced perms
# https://discord.com/api/oauth2/authorize?client_id=618079591965392896&permissions=543652576368&scope=bot%20applications.commands bogibot