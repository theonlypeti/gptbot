import sys
import nextcord as discord
import nextcord.ext.commands
from nextcord.ext import commands
from datetime import datetime
import emoji
import os
import argparse
import time as time_module
from dotenv import load_dotenv
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

logger = mylogger.init(args) #initializing the logger

if args.logfile:
    logger.setLevel(5)

intents = discord.Intents.all() #TODO remember what do i use members intent for?!?!! nor presences
intents.presences = True

#bot = commands.Bot(intents=intents, chunk_guilds_at_startup=False, member_cache_flags=nextcord.MemberCacheFlags.none())
client = commands.Bot(command_prefix='&', intents=intents, chunk_guilds_at_startup=True, status=discord.Status.offline, activity=discord.Game(name="Booting up...")) #TODO chunk_guilds_at_startup=False might help me
client.remove_command('help')
client.logger = logger
client.root = root

#-------------------------------------------------#

@client.event
async def on_ready():
    print(f"Signed in at {datetime.now()}")
    logger.info(f"{time_module.perf_counter() - start} Bootup time")
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
async def on_message(msg: nextcord.Message):
    if True:
        if msg.guild:
            ...
        else:
            tolog = f"{msg.author} sent dm: ['{msg.content}']{(' +' + ','.join([i.proxy_url for i in msg.attachments])) if msg.attachments else ''} "
            tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
            logger.warning(tolog)

    await client.process_commands(msg)

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

    tolog = f"[{inter.user}] called [{cmd} with {opts}]  in: [{inter.guild}/{inter.channel}]"
    tolog = emoji.demojize(antimakkcen(tolog)).encode('utf-8', "ignore").decode()
    logger.log(25, tolog)


#-------------------------------------------------#
client.logger.debug(__name__)
if __name__ == "__main__":
    os.chdir(root)
    linecount = 0
    if not args.minimal: #TODO does not take into consideration the only_ keyword arguments
        utils = [file for file in os.listdir(r"./utils") if file.endswith(".py")]
        files = utils + [__file__]
    else:
        files = (__file__,)
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
