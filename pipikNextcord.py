import sys
from collections import defaultdict
from typing import Coroutine
import nextcord as discord
import nextcord.ext.commands
from nextcord.ext import commands
from datetime import datetime
# from tqdm import tqdm
from utils.antimakkcen import antimakkcen
import emoji
import os
import argparse
import time as time_module
from dotenv import load_dotenv
from utils.mentionCommand import mentionCommand #used in /run
from utils.getMsgFromLink import getMsgFromLink
from utils import mylogger

# root = os.getcwd()
# print(root) #wrong

root = (os.path.dirname(os.path.abspath(__file__)))
# print(root)
os.chdir(root)

start = time_module.perf_counter()
version = "3.12"
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
parser.add_argument("--profiling", action="store_true", help="Measures the bootup time and outputs it to profile.prof.")
args = parser.parse_args()

pipikLogger = mylogger.init(args) #initializing the logger

if args.logfile:
    pipikLogger.setLevel(5)

if not args.minimal and not args.no_sympy:
    import utils.matstatMn
    prikazy = list(filter(lambda a: not a.startswith("_"), dir(utils.matstatMn)))
    [prikazy.remove(i) for i in ("lru_cache", "graf", "plt", "prod", "kocka", "minca", "napoveda")]

    from utils.matstatMn import *

already_checked = []
discord_emotes = {}
timeouts = defaultdict(int)
us = set()

intents = discord.Intents.all() #TODO remember what do i use members intent for?!?!! update: members is used when checking if guild is premium for example
intents.presences = True
intents.typing = True

#bot = commands.Bot(intents=intents, chunk_guilds_at_startup=False, member_cache_flags=nextcord.MemberCacheFlags.none())
client = commands.Bot(command_prefix='&', intents=intents, chunk_guilds_at_startup=True, status=discord.Status.offline, activity=discord.Game(name="Booting up...")) #TODO chunk_guilds_at_startup=False might help me
client.remove_command('help')
client.logger = pipikLogger
client.root = root

# TODO play with this @commands.has_permissions(manage_server=True) only applicable to prefix commands, slash has smth else
# TODO orjson
# TODO add modal to pill taking and crafting asking how many to use
# TODO continue the gifsaver add a normal command without reply
# TODO properly integrate matstat stuff, maybe put all subcommands into slashotpion with autocomplete
# TODO make emojis for pills
# TODO make a better help command
# TODO make pipikbot users a dict of id:user instead of a list of users, also redo the getUserFromDC func then
# TODO make an actual lobby extension
# TODO maybe make some mafia type game but rebrand it to some discord admins and mods vs spammers and use right click user commands
# TODO play with this  if interaction.user.guild_permissions.administrator
# TODO play with ClientCog and its application_commands property
# TODO command maker for users, and like on message command maker
# TODO replace every list typehint with Sequence or MutableSequence or smth or Iterable
# TODO a database abstraction for myself
# TODO selectmenu for bp temy to open their desc and availability in a embed, then the pagi arrows would cycle through the bp temy one by one + button for english
# TODO zssk listok buyer
# TODO include license files for my projects

#-------------------------------------------------#

@client.event
async def on_ready():
    print(f"Signed in at {datetime.now()}")
    pipikLogger.info(f"{time_module.perf_counter() - start} Bootup time")
    if args.profiling:
        os.system("snakeviz profile.prof")
        exit(0)
    game = discord.CustomActivity(
        name="Custom Status",
        state=f"{linecount} lines of code; V{version}!"
    )
    # game = discord.Game(f"{linecount} lines of code; V{version}! Use /help")  # dont even try to move this believe me ive tried
    await client.change_presence(activity=game)

@client.event
async def on_disconnect():
    global start
    start = time_module.perf_counter()

@client.event
async def on_message_delete(msg: nextcord.Message):
    if not msg.author.bot:
        if args.logfile:
            tolog = f"[{msg.author}] deleted ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} in {msg.channel.name}"
            tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
            pipikLogger.log(25, tolog)
        if msg.attachments:
            for att in msg.attachments:
                ...  # todo implement image saving? but only on prepinač


@client.event
async def on_message(msg: nextcord.Message):
    if True:
        if msg.guild:
            if msg.guild.id in []:
                tolog = f"{msg.author} sent: ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} in {msg.channel}"
                tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
                pipikLogger.log(25, tolog)
        else:
            tolog = f"{msg.author} sent dm: ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} "
            tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
            pipikLogger.warning(tolog)

    await client.process_commands(msg)


@client.listen("on_reaction_add")
async def reaction_add(reaction: discord.Reaction, user: discord.User):
    if reaction.message.author.bot or user.bot:
        return
    tolog = f"[{user}] reacted [{(reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name)}] on message: [{reaction.message.content or reaction.message.jump_url}], in: [{reaction.message.guild.name}/{reaction.message.channel}]"
    tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
    pipikLogger.log(25, tolog)


@client.listen("on_reaction_remove")
async def react_remove(reaction: discord.Reaction, user: discord.Member):
    if reaction.message.author.bot or user.bot:
        return
    tolog = f"[{user}] removed react [{(reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name)}] on message: [{reaction.message.content or reaction.message.jump_url}], in: [{reaction.message.guild.name}/{reaction.message.channel}]"
    tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
    pipikLogger.log(25, tolog)


@client.listen("on_interaction")
async def oninter(inter: discord.Interaction):
    cmd = inter.application_command
    if isinstance(cmd, discord.SlashApplicationSubcommand):
        cmd = cmd.parent_cmd.name + "/" + cmd.name
        opts = [f'{a["name"]} = {a["value"]}' for a in inter.data.get("options", [])[0]["options"]]
    elif isinstance(cmd, discord.SlashApplicationCommand):
        cmd = cmd.name
        opts = [f'{a["name"]} = {a["value"]}' for a in inter.data.get("options", [])]
    else:
        ...  #probably buttons
        return

    # pipikLogger.debug(inter.data.get("options", []))
    tolog = f"[{inter.user}] called [{cmd} with {opts}]  in: [{inter.guild}/{inter.channel}]"
    tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
    pipikLogger.log(25, tolog)

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
                    await ctx.send(f"{e}")
                    continue
            elif isinstance(command, Coroutine):
                a = await command
            await ctx.send(str(a)[:2000])
    except Exception as e:
        await ctx.send(f"{e}")


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
client.logger.debug(__name__)
if __name__ == "__main__":
    os.chdir(root)
    if not args.minimal and not args.no_sympy: #TODO does not take into consideration the only_ keyword arguments
        utils = [file for file in os.listdir(r"./utils") if file.endswith(".py")]
        files = utils + [__file__]
        linecount = 197  # matstatMn is added manually cuz i have a million commented lines after if __name__ == __main__
    else:
        files = (__file__,)
        linecount = 0
    for file in files:
        if file.endswith(".py"):
            try:
                with open(root+r"/utils/"+file, "r", encoding="UTF-8") as f:
                    linecount += len(f.readlines())
            except OSError:
                with open(file, "r", encoding="UTF-8") as f:
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
    # cogs.remove("testing.py") if args.no_testing else None  # remove testing.py from the list of cogs to be loaded if testing is disabled

    for n, file in enumerate(cogs, start=1): #its in two only because i wouldnt know how many cogs to load and so dont know how to format loading bar
        if not args.no_linecount:
            with open("./cogs/"+file, "r", encoding="UTF-8") as f:
                linecount += len(f.readlines())
        client.load_extension("cogs." + file[:-3])
        if not args.debug:
            sys.stdout.write(f"\rLoading... {(n / len(cogs)) * 100:.02f}% [{(int((n/len(cogs))*10)*'=')+'>':<10}]")
            sys.stdout.flush()

    sys.stdout.write(f"\r{len(cogs)}/{cogcount} cogs loaded.".ljust(50)+"\n")
    sys.stdout.flush()
    os.chdir(root)

# for file in tqdm(cogs):
#     if not args.no_linecount:
#         with open("./cogs/"+file, "r", encoding="UTF-8") as f:
#             linecount += len(f.readlines())
#     client.load_extension("cogs." + file[:-3])  #breaks

    if args.profiling:
        import cProfile
        import pstats
        with cProfile.Profile() as pr:
            client.run(os.getenv("MAIN_DC_TOKEN"))
        stats = pstats.Stats(pr)
        # stats.sort_stats(pstats.SortKey.TIME)
        # stats.print_stats()
        stats.dump_stats(filename="profile.prof")
    else:
        client.run(os.getenv("MAIN_DC_TOKEN"))

# 277129587776 reduced perms
# https://discord.com/api/oauth2/authorize?client_id=618079591965392896&permissions=543652576368&scope=bot%20applications.commands bogibot