import os
from typing import Optional
import nextcord as discord
from nextcord.ext import commands
import asyncio
import json 
from datetime import datetime, date, timedelta
import emoji
from random import randint, choice, choices, shuffle
from copy import deepcopy

from utils.mentionCommand import mentionCommand

sleepTimeMult = 1

white_sq = "\u25FB"
black_sq = "\u2B1B"
large_white_sq = "\u2B1C"
white_sq_black_border = "\U0001F532"
black_sq_white_border = "\U0001F533"
green_sq = "\U0001F7E9"

spinTokenIcon = "<:spin:957469682917572728>"
premSpinTokenIcon = "<:epicspin:957470557002141696>"
spinShardIcon = "<:shard:957469681474744340>"

root = os.getcwd()

os.makedirs(root + r"/data", exist_ok=True)
with open(root + r"/data/emojis.txt", "r") as file:
    allemojis_dict = json.load(file)
allemojis = sum([v for v in allemojis_dict.values()],[])
unlockable_emojis_dict = {k:v for k,v in allemojis_dict.items() if k not in ("pipikachis","cloveceachis")}
unlockable_emojis = sum([v for v in unlockable_emojis_dict.values()],[])
achi_emojis_dict = {k:v for k,v in allemojis_dict.items() if k in ("pipikachis","cloveceachis")}

class LobbyCog(commands.Cog):
    def __init__(self, client, baselogger):
        global cloveceLogger
        cloveceLogger = baselogger.getChild("CloveceLogger")
        self.users = []

        try:
            with open(root + r"/data/cloveceUsers.txt","r") as f:
                temp = json.load(f)
            for user in temp:
                try:
                    user["dailyDate"] = datetime.fromisoformat(user["dailyDate"])
                except:
                    pass
                self.users.append(self.User(user))
            cloveceLogger.debug(self.users)
        except OSError as e:
            cloveceLogger.error(e)
            with open(root + r"/data/cloveceUsers.txt", "w") as f:
                pass
        except json.decoder.JSONDecodeError as e:
            cloveceLogger.error(e)
            pass
        self.client = client
        self.lobbies = []
        self.serveremojis = []

    @discord.slash_command(description="Commands for the clovece game")
    async def clovece(self, interaction):
        pass

    @clovece.subcommand(name="spin", description="See your inventory of spin tokens and try your luck!")
    async def spincommand(self, interaction):
        user = self.getUserFromDC(interaction.user)
        await user.spin(interaction, self)

    class SpinButton(discord.ui.View):
        def __init__(self, cog):
            self.cog = cog
            super().__init__(timeout=None)

        @discord.ui.button(label="Test your luck?", emoji=spinTokenIcon)
        async def callback(self, button, interaction):
            button.disabled = True
            await interaction.edit(view=self)
            user=self.cog.getUserFromDC(interaction.user)
            await user.spin(interaction,self.cog)
    
    @clovece.subcommand(name="daily",description="Claim your daily spin today!")
    async def claimdaily(self,ctx):
        user = self.getUserFromDC(ctx.user)
        try:
            cloveceLogger.debug(f"user daily date, {user.dailyDate}, {type(user.dailyDate)}")
            if type(user.dailyDate) == datetime: #what is this line and the one below?!?!
                user.dailyDate = user.dailyDate.date()
            elif type(user.dailyDate) == str:
                cloveceLogger.warning("str?!?!?!! while claiming daily")
                user.dailyDate = (datetime.now() - timedelta(days=1)).date()
        except KeyError or ValueError:
            user.dailyDate = (datetime.now() - timedelta(days=1)).date()
        finally:
            if user.dailyDate == date.today(): #if today already taken
                tomorrow = datetime.now() + timedelta(1)
                midnight = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=0, minute=0, second=0)
                embedVar = discord.Embed(title="Daily spin token", description="You already collected your spin token today.", color=ctx.user.color)
                timestr = "<t:"+str(int(midnight.timestamp()))+":R>"
                embedVar.add_field(name="Come back", value=timestr)
                await ctx.send(embed=embedVar)
                return
            elif (user.dailyDate - date.today()) <= timedelta(days=-1): #if picking up daily
                embedVar = discord.Embed(title="Daily spin token", color=ctx.user.color)
                embedVar.add_field(name="You've got:", value=f"{spinTokenIcon} **1** x **Spin token**")
                await ctx.send(embed=embedVar,view=self.SpinButton(self))
            else:
                cloveceLogger.error(f"something is wrong,{user.dailyDate},{date.today()},{user.dailyDate - date.today()}")
                return
            user.dailyDate = datetime.now().date() 
            user.addItem("spinToken",1)
            self.savePlayers()

    @clovece.subcommand(name="stats",description="Shows your stats across all the games you´ve played.")
    async def showstats(self,ctx,user:discord.User=discord.SlashOption(name="user",description="See someone else´s profile.",required=False,default=None)):
        if user is None:
            user = ctx.user
        player = self.getUserFromDC(user)
        embedVar = discord.Embed(title=f"__{user.name}'s stats__",color=user.color)
        for k,v in player.stats.items():
            embedVar.add_field(name=k,value=v)
        await ctx.send(embed=embedVar)

    @clovece.subcommand(name="icons", description="Shows your or an user's collected icons.")
    async def showicons(self, ctx,
                        user: discord.User = discord.SlashOption(name="user", description="See someone else´s icons.",required=False, default=None)):
        if user is None:
            user = ctx.user
        player = self.getUserFromDC(user)
        embedVar = await self.printdefaults(player)
        embedVar.title = f"__{user.name}'s icons__"
        await ctx.send(embed=embedVar,ephemeral=True)

    @clovece.subcommand(name="help",description="Shows the help manual to this game and the bot.")
    async def helpclovece(self,ctx):
        helptext = {
            "commands": """**play** (*public*/*private*) = Makes a lobby for 4 players max. Private lobbies can be joined only via room code.
            
**join** [*code*] = joins an existing lobby using the room code. Alternatively just click the green join button.

**leave** = Leave the lobby you are currently in. Alternatively just click the red leave button.

**spin** = Acquire a random emoji icon for use in a človeče game.

**icons** = Shows your collected icons.
 
**daily** = Come back every day for your daily icon spin token.

**stats** (*pick a user*) = Shows your stats across all the games you´ve played.""",

            "lobbies": f"""To create a lobby, use the {mentionCommand(self.client,'clovece play')} command. You can choose whether to create a public or private lobby. Public lobbies can be joined by anyone using the {emoji.emojize(":inbox_tray:")} green button below the lobby. Private lobbies can only be joined using {mentionCommand(self.client,'clovece join')} with the 
            **room code** given to the lobby leader. The lobby leader can add bots, kick players and start the game once everyone confirmed their readiness using the {emoji.emojize(":check_mark_button:")} checkmark button.
            Players in the lobby may customize their icon with the {emoji.emojize(":artist_palette:")} palette button.""",

            "icons": f"""Player icons are used in človeče games to represent players and their pawns on the game board.
                        You can use the {emoji.emojize(":artist_palette:")} palette button while in a lobby to change your icon.
                        You can get icons by using the spin tokens you receive either from winning človeče games 
                        or claiming your daily rewards using {mentionCommand(self.client,'clovece daily')}.
                        You can see all your collected icons using the {mentionCommand(self.client,'clovece icons')} command.
                     """,

            "spin tokens": f"""Spin tokens are used to acquire icons in človeče games. You can get spin tokens by winning človeče games or claiming your daily rewards using {mentionCommand(self.client,'clovece daily')}.
            {spinTokenIcon} **Spin token**s grant you a random icon from any category, while {premSpinTokenIcon} **Premium spin token**s let you pick the category of your choice. 
            Getting an icon you already own breaks your spin token. Collecting {spinShardIcon} **10 shards** either from games or broken spin tokens will grant you a Premium spin token.""",

            "rules": """The point of the game is to get all your pawns from the spawn to the house. The first player to get all their pawns to the house wins the game.
            Players take turn throwing a dice. Throwing a 6 allows them to put a new pawn on the board. Pawns are moved in a clockwise direction as many steps as they rolled with the dice.
            Pawns are required to complete a full roundtrip around the board to enter the house. Stepping on another player's pawn will cause them to be removed from the board back to their spawn.""",

            "house rules": """Every household has different rules by which they play človeče. Some rules are arbitrary, and some are purely limitations of the discord bot implementation. Here are some of them:
            
            There are no safe spaces on the board. Not even the starting square. (Apart from inside the house.)
            
            Two pawns can not occupy the same square. Opponents are kicked out, your own pawns are pushed back by one tile. (Use this to your advantage if someone is behind you.)
            
            Throwing a 6 with a dice does not grant you another turn/throw. The game feels unfair already as it is.
            
            There is no penalty for throwing too many consecutive 6's."""}

        class HelpTopicSelector(discord.ui.Select):
            def __init__(self):
                opts = [discord.SelectOption(label="Commands",description="Gives help about človeče commands.",value="commands",emoji=emoji.emojize(":paperclip:")),
                        discord.SelectOption(label="Lobbies",description="How do i operate lobbies?",value="lobbies",emoji=emoji.emojize(":inbox_tray:")),
                        discord.SelectOption(label="Icons",description="What are icons and what do i use them for?",value="icons",emoji=emoji.emojize(":chess_pawn:")),
                        discord.SelectOption(label="Spin tokens",description="What are spin tokens and what do i use them for?",value="spin tokens",emoji=spinTokenIcon),
                        discord.SelectOption(label="Rules",description="What are the rules of človeče?",value="rules",emoji=emoji.emojize(":ledger:")),
                        discord.SelectOption(label="House rules",description="Because not everything is standard.",value="house rules",emoji=emoji.emojize(":straight_ruler:",language="alias")),
                        discord.SelectOption(label="Close",value="0",emoji=emoji.emojize(":cross_mark:"))]
                super().__init__(options=opts)

            async def callback(self, interaction: discord.Interaction):
                if self.values[0] == "0":
                    await interaction.response.edit_message(content="Cancelled", view=None, embed=None,delete_after=5.0)
                else:
                    await interaction.edit(embed=discord.Embed(title=f"About {self.values[0]}",description=helptext[self.values[0]],color=interaction.user.color))

        embedVar = discord.Embed(title="What do you wish to learn about?", description="Pick a topic below:",color=ctx.user.color)
        viewObj = discord.ui.View()
        viewObj.add_item(HelpTopicSelector())
        await ctx.send(embed=embedVar, view=viewObj)

    def readEmojis(self, file) -> dict:
        with open(file, "r") as file:
            return json.load(file)

    @commands.command()
    async def addEmojis(self, ctx, *attr): #TODO look at this #why? oh wait i get it now
        if len(attr) < 2:
            await ctx.send(embed=discord.Embed(title="Custom Emojis", description="""Allows to add emojis to the public or private emoji roster.
        Privately submitting the emojis will only make them usable on your own server,
        while public submitting allows players who are on your server to use them in games on other servers too.
        Submitted emojis might take some time to verify, as emojis should not contain any explicit content.
        if you are interested in adding server-wide public emotes for everyone to use, contact me at @Boothiepro#9144

        If you wish to add emotes, use &addEmojis public/private <emotes separated by space>

        !removing emotes is unfair against players who unlocked them so pick emotes that are likely to be permanent on your server!"""),ephemeral=True)
        else:
            with open(root + r"/data/private_serveremojis.txt","r") as file:
                privates = json.load(file)
            with open(root + r"/data/public_serveremojis.txt","r") as file:
                public = json.load(file)
            with open(root + r"/data/awaiting_review.txt","r") as file:
                pending = json.load(file)
            if str(ctx.guild.id) in privates.keys() or str(ctx.guild.id) in public.keys() or str(ctx.guild.id) in pending.keys():
                cloveceLogger.error(f"{ctx.guild.id} alredy has emotes in")
                await ctx.channel.send(embed=discord.Embed(title="You already have custom emotes in.", color=discord.Color.red()))
                return
            if attr[0].lower() == "private":
                    #for emoji in ctx.guild.emotes
                privates.update({ctx.guild.id:attr[1:]}) #TODO emoji check if they are actually part of this guild and are custom emojis
                with open(root + r"/data/private_serveremojis.txt","w") as file:
                    json.dump(privates,file,indent=4)
                
            elif attr[0].lower() == "public":
                print("registered public")
                #for emoji in ctx.guild.emotes
                reviewemojis = {ctx.channel.id:attr[1:]} #TODO emoji check if they are actually part of this guild and are custom emojis
                with open(root + r"/data/awaiting_review.txt","w") as file:
                    json.dump(reviewemojis,file,indent=4)
        #TODO

    @discord.slash_command( #deprecate these two #maybe not yet
        name="unlock",
        description="test",
        guild_ids=(860527626100015154,)
        )
    async def unlockEmoji(self, ctx,
        player: discord.User = discord.SlashOption(name="player", description="player to give an icon"),
        cat: str = discord.SlashOption(name="category", description="category"),
        emote: str = discord.SlashOption(name="emote", description="emote", required=False, default=None)
        ):
        
        user = self.getUserFromDC(player)
        user.addEmoji("defaults", cat, emote or choice(cat))
        await ctx.send(f"{emote} unlocked")

    @discord.slash_command( 
        name="unlockitem",
        description="test",
        guild_ids=(860527626100015154,)
        )
    async def useradditem(self, ctx,
        player: discord.User = discord.SlashOption(name="player",description="player to give an item"),
        item:str = discord.SlashOption(name="item", description="premSpinToken/spinToken/spinShards", required=True, choices=["premSpinToken", "spinToken", "spinShards"]),
        amount: int = discord.SlashOption(name="amount", description="number", required=False, default=1)
        ):
        
        user = self.getUserFromDC(player)
        user.addItem(item,amount)
        await ctx.send("item added")

    class DefaultsCategorySelectDropdown(discord.ui.Select): #now that i know how to make paginators i could try making them here too
        def __init__(self, user, cog):
            self.categories = user.inv["defaults"]
            self.user = user
            self.cog = cog
            options = sum([[discord.SelectOption(label=k + (f" ({str(i+1)})" if len(v)>24 else ""),emoji=emoji.emojize(":checkered_flag:" if k=="flags" else v[0],language="alias"),description=("Flag names are broken here but show up ingame perfectly fine" if k=="flags" else None),value=f"{k};{i}") for i in range((len(v)//24)+1)] for k,v in self.categories.items() if v] + [[discord.SelectOption(label="Back",emoji=emoji.emojize(":left_arrow:"),value="0")]],[])
            #options = sum([[discord.SelectOption(label=k + (f"({str(i+1)})" if len(v)>24 else ""),emoji=emoji.emojize(v[0]),value=k) for i in range((len(v)//24)+1)] for k,v in categories.items()] + [[discord.SelectOption(label="Back",emoji=emoji.emojize(":left_arrow:"),value="0")]],[])
            #print(*options,sep="\n")
            super().__init__(options=options,placeholder="Select an emoji category")

        async def callback(self, interaction):
            cloveceLogger.debug(self.values[0])
            if self.values[0] == "0":
                await interaction.response.edit_message(content="Cancelled",view=None,embed=None,delete_after=5.0) #TODO make it go back to cutsom emoji select #what do you mean?
                return
            cat,myslice = self.values[0].split(";")
            viewObj = discord.ui.View()
            viewObj.add_item(self.IconSelectDropdown(self.user, cat, myslice, self))
            await interaction.response.edit_message(view=viewObj)
    
        class IconSelectDropdown(discord.ui.Select):
            def __init__(self, user, category, myslice, parentView):
                myslice = int(myslice)
                self.pw = parentView
                self.user = user
                #print(*user.inv["defaults"][category][myslice*24: min((myslice+1)*24,len(user.inv["defaults"][category]))],sep="\n")
                if category != "flags":
                    icons = [discord.SelectOption(emoji=emoji.emojize(i,language="alias"),label=i) for i in user.inv["defaults"][category][myslice*24: min((myslice+1)*24,len(user.inv["defaults"][category]))]] + [discord.SelectOption(label="Back",emoji=emoji.emojize(":left_arrow:"),value="0")]
                else:
                    icons = [discord.SelectOption(label=i) for i in user.inv["defaults"][category][myslice*24: min((myslice+1)*24,len(user.inv["defaults"][category]))]] + [discord.SelectOption(label="Back",emoji=emoji.emojize(":left_arrow:"),value="0")]
                    
                super().__init__(options=icons, placeholder=f"Pick an emoji from {category}")

            async def callback(self, interaction):
                if self.values[0] != "0":
                    self.user.icon = self.values[0]
                    lobby = await self.pw.cog.findLobby(self.user.inLobby)
                    await lobby.messageid.edit(embed=lobby.show())
                    await interaction.edit(content=f"Chosen emoji: {self.values[0]}", view=None, embed=None)
                else:
                    viewObj = discord.ui.View()
                    viewObj.add_item(self.pw)
                    await interaction.response.edit_message(view=viewObj)

    async def printdefaults(self, user):
        if user is None:
            defaultemojis = allemojis_dict
        else:
            player = self.getUserFromDC(user)
            defaultemojis = player.inv["defaults"]
        embedVar = discord.Embed(title="Choose an icon", description="**Default emojis**")
        for k,v in defaultemojis.items():
            if k in unlockable_emojis_dict.keys() and v:
                embedVar.add_field(name=k, value="".join([emoji.emojize(i) for i in v]))
        embedVar.add_field(name="**Unlocked from achievements**", value="--------------- ", inline=False)
        for k,v in defaultemojis.items():
            if k in achi_emojis_dict.keys() and v:
                embedVar.add_field(name=k, value="".join([emoji.emojize(i) for i in v]))
            
        return embedVar

    async def customization(self, interaction):
        player = self.getUserFromDC(interaction.user)
        viewObj = discord.ui.View()
        player.syncpipikachis(self.client)
##        with open("emojis.txt","r") as file:
##            emojis = json.load(file)
        viewObj.add_item(self.DefaultsCategorySelectDropdown(player, self))
        await interaction.send(embed=await self.printdefaults(interaction.user), view=viewObj, ephemeral=True)
        #await self.printcustoms(user,channel) #TODO
        
    async def printcustoms(self, user, channel):
        player = self.getUserFromDC(user)
        public = self.readEmojis("public_serveremojis.txt")
        private = self.readEmojis("private_serveremojis.txt")
        globalemojis = self.readEmojis("global_serveremojis.txt")
        print(len(public),len(private),len(globalemojis))
        user_specific_emojis = {}
        if len(private)>0:
            print(channel.guild.id,private.keys())
            print(channel.guild.id in private.keys())
            print(str(channel.guild.id) in private.keys())
            if str(channel.guild.id) in private.keys():#ak current guild je v privates, print this current guilds emotes
                user_specific_emojis.update({channel.guild.name:private[str(channel.guild.id)]})
        if len(public) > 0:
            for guild in public:
                guildobj = self.client.get_guild(int(guild))
                if guildobj.get_member(user.id):  #ak user je na serveri, show those emotes #TODO maybe do this better? im like 90% sure this is pretty bad implementation
                #if ctx.message.author in guildobj.members:
                    user_specific_emojis.update({guildobj.name:public[guild]})
        if len(globalemojis)>0:
            for guild in globalemojis:
                print(guild)
                guildobj = self.client.get_guild(int(guild))
                print(user_specific_emojis)
                user_specific_emojis.update({guildobj.name:globalemojis[guild]})
                print(user_specific_emojis)

        if len(user_specific_emojis)>0:
            keylist = list(user_specific_emojis.keys())
            string="Custom Emojis:\n-----------------"
            for i in range(len(keylist)):
                string += "\n"+keylist[i]+": "
                for i in user_specific_emojis[(keylist[i])]:
                    string += i#emoji.emojize(i)
                    if len(string) > 1980:
                        await user.send(string)
                        string = ""
            await user.send(string)
        else:
            print("no custom emotes") #TODO pretty print

    @commands.command()
    async def verifyawaiting(self,ctx): #TODO REDO THIS WITH BUTTONS
        if ctx.author.id != 617840759466360842:
            return
        accepted = {}
        public = self.readEmojis("awaiting_review.txt")
        print(type(public))
        if len(public)>0:                
            keylist = list(public.keys())
            string = ""
            for i in range(len(keylist)):
                channel = self.client.get_channel(int(keylist[i])) #where the request was sent from, there we gonna reply with acceptance letter or denial letter
                string += "\n"+channel.guild.name+": "
                for j in public[(keylist[i])]:
                    string += emoji.emojize(j)
                    if len(string) > 1980:
                        await ctx.channel.send(string)
                        string = ""
                to_react = await ctx.channel.send(string)
                string = ""
                await to_react.add_reaction(emoji.emojize(":cross_mark:"))
                await to_react.add_reaction(emoji.emojize(":check_mark_button:"))
                
                
                def check(reaction, user):
                    print(not user.bot,reaction in (green_check,crossmark))
                    return not user.bot and reaction.emoji in (green_check,crossmark) #TODO PLAYER CHECK

                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=360.0, check=check)
                    print("yes?")
                except asyncio.TimeoutError:
                    print("L")
                    return
                else:
                    if reaction.emoji == emoji.emojize(":check_mark_button:"):
                        print("passed")
                        await channel.send("Congratulations, your custom emojis have been accepted!")
                        #TODO actually put them into public
                        accepted.update({channel.guild.id:public[keylist[i]]})
                    elif reaction.emoji == emoji.emojize(":cross_mark:"):
                        await channel.send("Unfortunatelly, your custom emoji suggestions don´t meet the criteria to be public.")

            ctx.channel.send("all done")
            with open(root + r"/data/awaiting_review.txt", "w") as file:
                file.truncate(0)
                file.write("{}")
                print("cleared")
            if len(accepted) > 0:
                with open(root + r"/data/public_serveremojis.txt", "r+") as file:
                    accepted.update(json.load(file))
                    file.truncate(0) # oh my god, what are you doing here
                    file.seek(0)
                    json.dump(accepted, file, indent=4)
                    print("dumped")
        else:
            await ctx.channel.send("no custom emotes") #TODO pretty print

    class LobbyView(discord.ui.View):
        def __init__(self, cog, lobby):
            self.cog = cog
            self.lobby = lobby
            super().__init__(timeout=600)

        @discord.ui.button(style=discord.ButtonStyle.green,emoji=emoji.emojize(":inbox_tray:"))
        async def joinbutton(self, button, ctx):
            player = self.cog.getUserFromDC(ctx.user)
            await self.lobby.addPlayer(player, ctx)
            cloveceLogger.debug(f"{ctx.user.name} joined")

        @discord.ui.button(style=discord.ButtonStyle.red,emoji=emoji.emojize(":outbox_tray:"))
        async def leavebutton(self, button, ctx):
            player = self.cog.getUserFromDC(ctx.user)
            await self.lobby.removePlayer(ctx, player)
            cloveceLogger.debug(f"{ctx.user.name} left")

        @discord.ui.button(style=discord.ButtonStyle.grey, emoji=emoji.emojize(":artist_palette:"), disabled=False)
        async def customizebutton(self, button, ctx):
            player = self.cog.getUserFromDC(ctx.user)
            if player.ready:
                await ctx.send("You cannot change your icon while you are marked ready!", ephemeral=True)
                return
            if not player.inLobby:
                await ctx.send("You are not in a lobby!", ephemeral=True)
                return
            await self.cog.customization(ctx)
            cloveceLogger.debug(f"{ctx.user.name} clicked customize")

        @discord.ui.button(style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def readybutton(self, button, ctx):
            player = self.cog.getUserFromDC(ctx.user)
            if player.inLobby:
                if [i.icon for i in self.lobby.players].count(player.icon) > 1:
                    await ctx.send(embed=discord.Embed(title="Cannot ready up, someone else has the same icon as you!", color=discord.Color.red()),ephemeral=True)
                    player.ready = False
                    self.lobby.readyCheck()
                    return
                player.ready = not player.ready
                await self.lobby.readyCheck()
                cloveceLogger.debug(f"{ctx.user.name} requested ready/unready")
            else:
                await ctx.send(embed=discord.Embed(title="You are not in this lobby.", color=discord.Color.red()), ephemeral=True)
                cloveceLogger.debug(f"{ctx.user.name} clicked ready on not joined lobby")

        @discord.ui.button(style=discord.ButtonStyle.blurple,emoji=emoji.emojize(":right_arrow:"),disabled=True)
        async def startbutton(self, button, ctx):
            await ctx.response.defer()
            if self.lobby.lobbyleader == ctx.user:
                await self.lobby.managemsg.edit(embed=None, view=None, content="Game started.", delete_after=5.0)
                await self.lobby.start(ctx)
            else:
                await ctx.send(embed=discord.Embed(title="You are not the leader of this lobby.", color=discord.Color.red()), ephemeral=True)
                cloveceLogger.info(f"{ctx.user.name} wanted to start game when not lobbyleader")

    class DiffcultyDropdown(discord.ui.Select):
        def __init__(self, lobby, cog):
            self.lobby = lobby
            self.cog = cog
            optionslist=[
                discord.SelectOption(label="Easy", emoji=emoji.emojize(":green_circle:"), description="Weighted dice, reduced game end rewards."),
                discord.SelectOption(label="Normal", emoji=emoji.emojize(":yellow_circle:"), description="Normal dice, standard opponent."),
                discord.SelectOption(label="Hard", emoji=emoji.emojize(":red_circle:"), description="Unfair dice, opponent actually thinks before moving."),
                discord.SelectOption(label="Cancel", value="0", emoji=emoji.emojize(":cross_mark:"))
                ]
            super().__init__(options=optionslist, placeholder="Select a diffculty")

        async def callback(self, inter):
            diff = self.values[0]
            if diff != "0":
                await self.lobby.addPlayer(self.cog.Bot(self.lobby, diff), inter)
                await self.lobby.messageid.edit(embed=self.lobby.show())
            await inter.edit(view=self.cog.MngmntView(self.lobby, self.cog))

    class KickPlayerDropdown(discord.ui.Select):
        def __init__(self, lobby, cog):
            self.lobby = lobby
            self.cog = cog
            optionslist=list([discord.SelectOption(label=i.name, value=str(n), emoji=emoji.emojize(i.icon, language="alias")) for n, i in enumerate(self.lobby.players[1:],start=1)])
            optionslist.append(discord.SelectOption(label="Cancel", value="-1", emoji=emoji.emojize(":cross_mark:")))
            super().__init__(options=optionslist, placeholder="Pick a player to kick")

        async def callback(self, inter):
            result = self.values[0]
            if result != "-1":
                cloveceLogger.debug(f"kicking player number {result}")
                tokick = self.lobby.players[int(result)]
                if isinstance(tokick, LobbyCog.Bot):
                    self.lobby.bot_icons.append(tokick.icon)
                    self.lobby.bot_names.append(tokick.name)
                    del self.lobby.players[int(result)]
                else:
                    await self.lobby.removePlayer(inter, self.cog.getUserFromDC(self.lobby.players[int(result)]))
                await self.lobby.messageid.edit(embed=self.lobby.show())
            await inter.edit(view=self.cog.MngmntView(self.lobby, self.cog))

    class MngmntView(discord.ui.View):
        def __init__(self, lobby, cog):
            self.lobby = lobby
            self.cog = cog
            super().__init__(timeout=None)

        @discord.ui.button(label="Add Bot", style=discord.ButtonStyle.grey, emoji=emoji.emojize(":robot:"))
        async def addbotbutton(self, button, inter):
            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.DiffcultyDropdown(self.lobby, self.cog))
            await inter.edit(view=viewObj)
            
        @discord.ui.button(label="Kick Player", style=discord.ButtonStyle.red, emoji=emoji.emojize(":boot:", language="alias"))
        async def kickbutton(self, button, inter):
            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.KickPlayerDropdown(self.lobby,self.cog))
            await inter.edit(view=viewObj)

        @discord.ui.button(label="Resend lobbymsg", style=discord.ButtonStyle.grey,emoji=emoji.emojize(":right_arrow_curving_left:"))
        async def resendbutton(self, button, inter):
            await self.lobby.messageid.edit(embed=discord.Embed(title="The lobby you are looking for has moved", description="see below"),view=None,delete_after=30.0)
            lobbymessage = await inter.channel.send(embed=discord.Embed(title="Generating lobby..."))
            self.lobby.messageid = lobbymessage
            await self.lobby.messageid.edit(embed=self.lobby.show(), view=self.cog.LobbyView(self.cog, self.lobby))
                
    @clovece.subcommand(name="play", description="Makes a lobby for a človeče game.")
    async def makeLobby(self, ctx: discord.Interaction, private=discord.SlashOption(name="private", description="Do you wish to create a public lobby or a private one",required=False,default="Public",choices=("Public","Private"))):
        user = self.getUserFromDC(ctx.user)
        if user.inLobby:
            await ctx.send(embed=discord.Embed(title=f"You are already in a lobby. Try {mentionCommand(self.client,'clovece leave')}", color=discord.Color.red()),ephemeral=True)
            return
        else:
            lobbymessage = await ctx.channel.send(embed=discord.Embed(title="Generating lobby..."))
            newLobby = self.Lobby(ctx, lobbymessage, self, private=(private == "Private"))
            newLobby.players.append(user)
            
            self.lobbies.append(newLobby)
            user.inLobby = newLobby.code

            await ctx.send(embed=discord.Embed(title=f"You are now the lobby leader of ||{newLobby.code}||",
                description="You can add bots with the **Add bot** button\n\nYou can remove players/bots from the lobby with the **Kick player** button\n\nIf the channel is spammed over, you can resend the lobby message with the **Resend lobbymsg** button\n\nWhen everybody is ready, a start game ({}) button will appear under the lobby message.".format(emoji.emojize(":right_arrow:"))),ephemeral=True,view=self.MngmntView(newLobby,self))
            newLobby.managemsg = await ctx.original_message()
            
            viewObj = self.LobbyView(self, newLobby)
            if private == "Private":
                viewObj.children[0].disabled = True
            
            await lobbymessage.edit(embed=newLobby.show(), view=viewObj)
        
    class Lobby(object):
        def __init__(self, ctx, messageid, cog, private=False):
            self.cog = cog
            self.players = []
            self.private = private
            while (code := "".join([chr(randint(65, 90)) for _ in range(4)])) in [lobby.code for lobby in self.cog.lobbies]:
                cloveceLogger.info(f"generating lobbycode {code}")
                continue
            self.code = code
            self.ongoing = False
            self.managemsg = None
            self.messageid = messageid
            self.lobbyleader = ctx.user
            self.bot_names = ['Bot Abraham', 'Bot Albert', 'Bot Alfred', 'Bot Archibald', 'Bot Arthur', 'Bot Benedict', 'Bot Charles', 'Bot Edward', 'Bot Eric', 'Bot Ernest', 'Bot Frank', 'Bot Frederick', 'Bot George', 'Bot Henry', 'Bot Jack', 'Bot Oliver', 'Bot Reginald', 'Bot Stanley', 'Bot Ted', 'Bot Winston']
            self.bot_icons = [":computer:", ":desktop_computer:", ":space_invader:", ":robot:"]
            shuffle(self.bot_names) #zoznam mien z ktorych si BOTi random vyberaju
            shuffle(self.bot_icons)

        def __str__(self):
            return self.code+"+".join(map(str, self.players))

        def show(self):
            name = self.lobbyleader.name
            EmbedVar = discord.Embed(
                title=name+"'s "+("Public" if not self.private else "Private")+" Lobby ("+str(len(self.players))+"/4)",
                description=("Game already running." if self.ongoing else f"use **{mentionCommand(self.cog.client, 'clovece join')} {self.code}** or click the join icon") if not self.private else f"ask the lobby leader for the code, \nthen use {mentionCommand(self.cog.client,'clovece join')} *CODE*, don't worry noone will see that.\n Make sure everyone has a unqiue icon!") #extra space deliberate, otherwise looks stupid
            EmbedVar.set_footer(text="{} join, {} leave, {} customize self, {} ready".format(emoji.emojize(":inbox_tray:"), emoji.emojize(":outbox_tray:"), emoji.emojize(":artist_palette:"),emoji.emojize(":check_mark_button:")))
            for i, player in enumerate(self.players, start=1):
                EmbedVar.add_field(name=f"{i}. {player}", value="Ready?"+(emoji.emojize(":cross_mark:"), emoji.emojize(":check_mark_button:"))[bool(player.ready)],inline=False)
            while i < 4:
                EmbedVar.add_field(name="[Empty]", value="Ready? "+emoji.emojize(":check_mark_button:"), inline=False)
                i += 1
            return EmbedVar

        async def readyCheck(self):
            readys = [i.ready for i in self.players]
            uniqueIcons = len({i.icon for i in self.players}) == len(self.players)
            viewObj = self.cog.LobbyView(self.cog, self)
            viewObj.children[0].disabled = bool(self.private)
            if not self.ongoing:
                if all(readys) and len(readys) > 1 and uniqueIcons:
                    viewObj.children[-1].disabled = False
                    cloveceLogger.debug("all players ready to go")
                    await self.messageid.edit(embed=self.show(), view=viewObj) #KEEP THIS HERE!!! NOT DUPLICATE
                    return True
                else:
                    viewObj.children[-1].disabled = True
                    cloveceLogger.debug("not all players ready to go")
            else:
                for child in viewObj.children:
                    child.disabled = True
            await self.messageid.edit(embed=self.show(), view=viewObj)
            return False

        async def start(self, ctx) -> None:
            #if await self.readyCheck(): #hold on why is it like this #looks like this is working as intended
            if True:
                if not self.ongoing:
                    self.ongoing = True
                    await self.readyCheck() #this is needed to update the view
                    game = CloveceGame(self) #create game
                    for player in self.players: #add players to game
                        game.playerList.append(Player(player.name, isCPU=True if type(player) == self.cog.Bot else False, diffculty="Normal" if type(player) == self.cog.User else player.diffculty ,ikonky=player.icon,houseIcon=game.houseIcon,profile=player))
                    await game.cloveceStart(ctx.channel) #start game #if i do ctx.send it breaks after 15mins cuz interactions.
                    self.cog.savePlayers()
                else:  #should not be achievable as the start button should be disabled when game is ongoing, maybe delete
                    await ctx.send(embed=discord.Embed(title="A game is already running.", color=discord.Color.red()), ephemeral=True)
                    cloveceLogger.warning("ongoing game")
        
        async def addPlayer(self, player, ctx) -> None:
            if len(self.players) < 4:
                if not self.ongoing:
                    if not isinstance(player, self.cog.Bot):
                        if not player.inLobby:
                            player.inLobby = self.code
                            await ctx.send(embed=discord.Embed(title="Joined", color=discord.Color.green()), ephemeral=True)
                        else:
                            await ctx.send(embed=discord.Embed(title=f"You are already in a lobby. Try {mentionCommand(self.cog.client,'clovece leave')}",color=discord.Color.red()),ephemeral=True)
                            cloveceLogger.debug("already in lobby")
                            return
                    #await self.messageid.edit(embed=self.show()) #redundant: gets updated in readyCheck again too so
                    self.players.append(player)
                    await self.readyCheck()
                else:
                    cloveceLogger.error("ongoing game") #shouldnt be a possibility, remove buttons from lobbymsg after start
            else:
                await ctx.send(embed=discord.Embed(title="Lobby is already full!", color=discord.Color.red()), ephemeral=True)

        async def removePlayer(self, ctx, player) -> None:
            if not self.ongoing:
                if player in self.players:
                    self.players.remove(player)
                    player.inLobby = False
                    player.ready = False
                    leader = self.cog.getUserFromDC(self.lobbyleader)
                    if player == leader:
                        await self.disband()
                        return
                    else:
                        self.messageid.edit(embed=self.show())
                        await self.readyCheck()
                else:
                    await ctx.send(embed=discord.Embed(title="You are not in this lobby.", color=discord.Color.red()), ephemeral=True)
            else:
                print("game ongoing") #TODO make the player a bot?; ~~actually should not be possible to achieve this so~~ actually it is possible by using slash leave

        async def disband(self):
            for player in self.players:
                if not isinstance(player,LobbyCog.Bot):
                    player.inLobby = False
                    player.ready = False
            try:
                await self.managemsg.delete()
            except Exception:
                try:
                    await self.managemsg.edit(embed=discord.Embed(title="Lobby disbanded."), view=None, delete_after=5.0)
                except Exception:
                    pass
            try:
                await self.messageid.edit(embed=discord.Embed(title="Lobby disbanded.", description=f"Make a new one with {mentionCommand(self.cog.client,'clovece play')}"), view=None, delete_after=30.0)
            except AttributeError: #disbanding after a game cannot edit message as it doesnt exist anymore
                pass
            self.cog.lobbies.remove(self)
            del self

    async def findLobby(self, lobbyid) -> Optional[Lobby]:
        if not lobbyid:
            return None
        else:
            for lobby in self.lobbies:
                if lobby.code == lobbyid:
                    break
            else:
                cloveceLogger.info("lobby not found inside findlobby") #NO need to print. it is done a few lines lower, line 678 if nothing moved
                return None
        return lobby

    @clovece.subcommand(name="join", description="Join an existing človeče lobby.")
    async def joinlobby(self, ctx, lobbyid: str = discord.SlashOption(name="lobbyid", description="A lobby´s identification e.g. ABCD", required=True)):
        user = self.getUserFromDC(ctx.user)
        lobby = await self.findLobby(lobbyid.upper())
        if lobby:
            await lobby.addPlayer(user, ctx)
        else:
            await ctx.send(embed=discord.Embed(title=f"Lobby \"**{lobbyid}**\" not found", color=ctx.user.color), ephemeral=True)

    @clovece.subcommand(name="leave", description="Leave the človeče lobby you are currently in.")
    async def leavelobby(self, ctx):
        user = self.getUserFromDC(ctx.user)
        lobby = await self.findLobby(user.inLobby)
        if lobby:
            await ctx.send(embed=discord.Embed(title=f"Left {lobby.lobbyleader.name}'s lobby.", color=ctx.user.color), ephemeral=True)
            await lobby.removePlayer(ctx.channel, user)
        else:
            await ctx.send(embed=discord.Embed(title="You are not currently in a lobby.",color=ctx.user.color), ephemeral=True)
            
    def getUserFromDC(self, dcUser):
        if isinstance(dcUser, int):
            lookingfor = dcUser
        elif isinstance(dcUser, self.User):
            lookingfor = dcUser.userid
        elif isinstance(dcUser, discord.member.Member):
            lookingfor = dcUser.id
        else:
            raise NotImplementedError(type(dcUser))
        for i in self.users:
            if i.userid == lookingfor:
                return i
        else:
            user = self.User(dcUser)
            self.users.append(user)
            self.savePlayers()
            return user

    def savePlayers(self):
        tempusers = []
        for user in self.users:
            tempuser = deepcopy(user)
            tempuser = tempuser.toDict()
            tempuser["inLobby"] = None
            tempuser["ready"] = False
            try:
                tempuser["dailyDate"] = tempuser["dailyDate"].isoformat()
            except Exception as s:
                cloveceLogger.error(s)
            tempusers.append(tempuser)
        with open(root + r"/data/cloveceUsers.txt","w") as file:
            json.dump(tempusers,file,indent=4)
        cloveceLogger.info("saved")

    class Bot:
        def __init__(self,lobby,diff):
            self.name = lobby.bot_names.pop()
            self.icon = lobby.bot_icons.pop()
            self.ready = True
            self.diffculty = diff
            
        def __str__(self):
            return f"{self.name} ({self.diffculty}) | icon: {self.icon}"
        
    class User(object):
        def __init__(self, discorduser):
            if type(discorduser) == dict:
                for k, v in discorduser.items():
                    setattr(self, k, v)
            else:
                self.userid = discorduser.id
                self.name = discorduser.name
                self.inv = {"items":{"spinToken":0,"premSpinToken":0,"spinShards":0},"defaults":{"defaults": [
                                                    ":white_circle:",
                                                    ":black_circle:",
                                                    ":red_circle:",
                                                    ":blue_circle:",
                                                    ":brown_circle:",
                                                    ":purple_circle:",
                                                    ":green_circle:",
                                                    ":yellow_circle:",
                                                    ":orange_circle:"],
                    "smileys":[],"hands":[],"plants":[],"animals":[],"foods":[],"items":[],"symbols":[],"hearts":[],"horoscope":[],"flags":[],"meme":[],"professions":[]},
                                                    "customs":{}}
                self.stats = {"Steps taken":0,"Players kicked out":0,"Times kicked out":0,"First places":0,"Second places":0,"Third places":0,"Dice thrown":0,"Spins":0,"Default icons owned":9,"Custom server icons owned":"Coming Soon"}
                self.icon = choice(self.inv["defaults"]["defaults"])
                self.ready = False
                self.dailyDate = (datetime.now() - timedelta(days=1)).date()
                cloveceLogger.debug(f"{self.dailyDate},{type(self.dailyDate)}")
                self.inLobby = False

        def __str__(self):
            return self.name+" | icon: "+self.icon

        def syncpipikachis(self,client):
            pipikcog = client.cogs["PipikBot"]
            pipikuser = pipikcog.getUserFromDC(self.userid)
            for achi in pipikuser.achi:
                achiobj = pipikcog.achievements[achi]
                achiemojisdict = {"nice": ":eggplant:", "breaking_bad": ":yum:", "dedicated": ":spiral_calendar_pad:", "megapp": ":hugging_face:"}
                if emoji.demojize(achiobj.icon) in allemojis_dict["pipikachis"]:
                    self.addEmoji("defaults", "pipikachis", emoji.demojize(achiobj.icon))
                elif achiobj.achiid in achiemojisdict:
                    self.addEmoji("defaults","pipikachis", achiemojisdict[achiobj.achiid])
            if pipikuser.methods & 4:
                self.addEmoji("defaults", "pipikachis", ":thermometer:")
                    
        def addItem(self, item, amount):
            if item in self.inv["items"].keys():
                self.inv["items"][item] = max(0, self.inv["items"][item] + amount)
            else: #should not happen but lets be safe #added choices, should not be reachable now #what
                self.inv["items"][item] = amount
           
        def addEmoji(self, emojitype, category, emoji): #emojitype is default or custom or global maybe, category is server in that case
            if emojitype in self.inv:
                if category in self.inv[emojitype]:
                    if emoji not in self.inv[emojitype][category]:
                        self.inv[emojitype][category].append(emoji)
                        return 0
                    else:
                        return 1
                else:
                    self.inv[emojitype][category] = []
            else:
                self.inv[emojitype] = {}
            self.addEmoji(emojitype,category,emoji)

        async def checkShards(self,cog=None,ctx=None):
            if self.inv["items"]["spinShards"] >= 10:
                self.addItem("spinShards",-10)
                self.addItem("premSpinToken",1)
                if ctx and cog:
                    viewObj = cog.SpinButton(cog)
                    await ctx.channel.send(embed=discord.Embed(title=f"You collected {spinShardIcon} 10 token shards!",description=f"They have been combined into a {premSpinTokenIcon} **Premium Spin Token** for you!",color=ctx.user.color),view=viewObj)

        class SpinTypeSelect(discord.ui.Select):
            def __init__(self,user,cog):
                self.user = user
                self.cog = cog
                self.choices = [discord.SelectOption(label="Cancel",emoji=emoji.emojize(":cross_mark:"),value="-1")]
                cloveceLogger.debug(f'{user.inv["items"]["spinToken"]},{type(user.inv["items"]["spinToken"])}')
                if user.inv["items"]["spinToken"]:
                    self.choices.append(discord.SelectOption(label="Spin Token",emoji=spinTokenIcon,description="Get any random emoji",value="basic"))
                if user.inv["items"]["premSpinToken"]:
                    self.choices.append(discord.SelectOption(label="Premium Spin Token",emoji=premSpinTokenIcon,description="Get an emoji from any category you'd like!",value="prem"))
                super().__init__(options=self.choices,placeholder="Select a spin type")

            async def callback(self, interaction):
                if self.cog.getUserFromDC(interaction.user) != self.user:
                    await interaction.send(embed=discord.Embed(title=f"This is not your inventory! Use {mentionCommand(self.cog.client,'clovece spin')}", color=discord.Colour.red()),ephemeral=True)
                    return
                chosen = self.values[0]
                if chosen == "-1":
                    try:
                        await interaction.response.delete_original_message()
                    except Exception:
                        await interaction.edit(content="Cancelled",view=None,embed=None,delete_after=2.0)
                elif chosen=="basic" and self.user.inv["items"]["spinToken"] >= 1:
                    self.user.stats["Spins"] += 1
                    self.user.addItem("spinToken",-1)
                    got = choice(unlockable_emojis)
                    for key,v in unlockable_emojis_dict.items():
                        if got in v:
                            break
                    err = self.user.addEmoji("defaults", key, got)
                    if not err:
                        await interaction.edit(embed=discord.Embed(title=f"You recieved  {got} !", description=f"You can now use this emoji as an icon in a clovece game. Try it in {mentionCommand(self.cog.client,'clovece play')}", color=interaction.user.color),view=None)
                        self.user.stats["Default icons owned"] += 1
                    elif err:
                        amount = randint(1,3)
                        await interaction.edit(embed=discord.Embed(title=f"You rolled {got}", description=f"...but you already own it. Heres {spinShardIcon} **{amount}** spin token shards", color=interaction.user.color), view=None)
                        self.user.addItem("spinShards",amount)
                        await self.user.checkShards(self.cog,interaction)
                    self.cog.savePlayers()
                elif chosen == "prem" and self.user.inv["items"]["premSpinToken"] >= 1:
                    viewObj = discord.ui.View()
                    viewObj.add_item(self.SpinDefaultsCategorySelectDropdown(self.user,self.cog))
                    await interaction.edit(view=viewObj)

            class SpinDefaultsCategorySelectDropdown(discord.ui.Select):
                def __init__(self,user,cog):
                    self.user = user
                    self.cog = cog #cursed line below
                    options = [discord.SelectOption(label=k,emoji=emoji.emojize(":checkered_flag:" if k=="flags" else v[0],language="alias"),description="({}/{})".format((len(self.user.inv["defaults"][k]) if k in self.user.inv["defaults"] else 0),len(v)),value=k) for k,v in allemojis_dict.items() if k not in ("pipikachis","cloveceachis")] + [discord.SelectOption(label="Cancel",emoji=emoji.emojize(":cross_mark:"),value="0")]
                    super().__init__(options=options,placeholder="Select an emoji category")

                async def callback(self,interaction):
                    if self.cog.getUserFromDC(interaction.user) != self.user:
                        await interaction.send(embed=discord.Embed(title=f"This is not your inventory! Use {mentionCommand(self.cog.client,'clovece spin')}", color=discord.Colour.red()),ephemeral=True)
                        return
                    if self.values[0] == "0":
                        await interaction.edit(content="Cancelled", view=None, embed=None, delete_after=1.0)
                        return
                    if self.user.inv["items"]["premSpinToken"] >= 1:
                        self.user.stats["Spins"] += 1
                        self.user.addItem("premSpinToken", -1)
                        cat = self.values[0]
                        got = choice(allemojis_dict[cat])
                        err = self.user.addEmoji("defaults", cat, got)
                        cloveceLogger.info(f"{err},emoji adding outcome")
                        if not err:
                            await interaction.edit(embed=discord.Embed(title=f"You recieved {got}", description=f"You can now use this emoji as an icon in a clovece game. Try it in {mentionCommand(self.cog.client,'clovece play')}", color=interaction.user.color), view=None)
                            self.user.stats["Default icons owned"] += 1
                        elif err:
                            amount = randint(1,3)
                            await interaction.edit(embed=discord.Embed(title=f"You rolled {got}", description=f"...but you already own it. Heres {spinShardIcon} **{amount}** spin token shards", color=interaction.user.color), view=None)
                            self.user.addItem("spinShards", amount)
                            await self.user.checkShards(self.cog, interaction)
                        self.cog.savePlayers()

        async def spin(self,ctx,cog):
            user = cog.getUserFromDC(ctx.user) 
            viewObj = discord.ui.View()
            viewObj.add_item(self.SpinTypeSelect(user,cog))
            await ctx.send(embed=discord.Embed(
                title="Spin tokens",description=f"""Your inventory:
{spinTokenIcon} **Spin Token** x **{user.inv["items"]["spinToken"]}**
Allows you to get *any* emoji from *any* default category.

{premSpinTokenIcon} **Premium Spin Token** x **{user.inv["items"]["premSpinToken"]}**
Allows you to get *any* emoji from *your choice* of a category.

{spinShardIcon} **Spin Token Shards** x **{user.inv["items"]["spinShards"]}**
When you get a duplicate emoji, the spin token is broken.
Collecting 10 of these grants you a *Premium spin token*""", color=ctx.user.color), view=viewObj)

        def toDict(self):
            return self.__dict__

class Empty(object): #prazdne policko
        """prazdne policko, jediny attribute je jeho ikonka na zobrazenie na poli"""
        def __init__(self, icon): #pre konzistenciu
            self.icon = icon

        def __str__(self):
            return self.icon

        def __bool__(self):
            return False

class CloveceGame(object):
    def __init__(self, lobby):
        self.velkost = 11 #len taky placeholder aby nebol NameError, btw 105 je max sirka mojho terminalu
        self.winPoradie = [] #do tohto zoznamu sa budu pridavat hraci ktori dokoncili hru, a tento zoznam bude aj na konci vyprintovany ako leaderboard
        self.playerList = [] #cely zoznam aktivnych aj neaktivnych hracov
        self.diffculties = {"Easy":(0.25,0.25,0.2,0.2,0.15,0.15), 
                        "Normal":(0.2,0.2,0.2,0.2,0.2,0.2),
                        "Hard":(0.15,0.15,0.2,0.2,0.25,0.25)} #pouzite ako pravdepodobnosti hodenia kockou BOTmi(napr Hard ma vacsiu sancu hodit 6ku)

        self.houseIcon = black_sq_white_border #default ikonka pre domceky, da sa zmenit v menu vzhladu
        self.emptyIcon = black_sq #default ikonka pre policka, da sa zmenit v menu vzhladu
        self.spawnIcon = black_sq_white_border #default ikonka pre spawny, da sa zmenit bla bla atd
        #self.sleepTimeMult = 1 #multiplier na cas pre pauzy medzi printami a inymi akciami. Da sa zmenit v nastaveniach
        self.vegetationIcon = None #TODO future
        self.voidIcon = large_white_sq
        self.lobby = lobby

    #class PowerUpPolicko(object):
        #TODO one day... ;)

    async def posToPole(self,pocet_poli,panakAmount):
        """takes every active panacik´s poziciu a polozi ich na hracie polia"""
        #polia je 1D reprezentacia vsetkych poli na ktore panaky mozu stupit. Nulte pole je pravo hore (start hráca A)
        polia = [Empty(self.emptyIcon) if i % (self.velkost-1) != 0 else Empty(self.spawnIcon) for i in range(pocet_poli)] #naplni hracie pole prazdnymi polickami, start pozicie maju inu ikonku
        for player in self.playerList:
            await player.fillHouses(panakAmount) #reset domcekovych policok 
            for panak in player.panaky:
                if not panak.inSpawn: #ak je none tak je v spawn/stajni tak ho mozme nechat v pokoji
                    if panak.homePos is not None:
                        player.domceky[panak.homePos] = panak
                    else:
                        polia[panak.currPos] = panak #dam na currPos-té policka cely panak objekt
        return polia

    async def diceThrow(self, player): #this is a mess yo
        availablePanaciky = [i for i in player.panaky if not i.inSpawn] #panaciky na vybranie
        if not availablePanaciky:
            throw = choices(range(1, 7), weights=(0.1, 0.1, 0.1, 0.15, 0.15, 0.4))[0]
            if not player.isCPU:
                player.player.stats["Dice thrown"] += 1
        else:
            if player.isCPU:
                throw = choices(range(1, 7), weights=self.diffculties[player.diffculty])[0]
            else:
                player.player.stats["Dice thrown"] += 1
                throw = choice(range(1, 7))
                #throw = 6
        await asyncio.sleep(sleepTimeMult*0.5)
        return throw

    class VyberPanacikButton(discord.ui.Button):
        def __init__(self, num, throw, player, availablePanaciky, disabled=False):
            self.player = player
            self.num = num
            self.throw = throw
            self.availablePanaciky = availablePanaciky
            nums = {1: "one", 2: "two", 3: "three", 4: "four"}
            icon = emoji.emojize(":{}:".format(nums[self.num]), language="alias")

            super().__init__(emoji=icon, disabled=disabled)
    
        async def callback(self, interaction):
            if interaction.user.id != self.player.player.userid:
                await interaction.send("It´s not your turn!", ephemeral=True)
                return
            
            await interaction.response.edit_message(view=None)
            await self.availablePanaciky[self.num-1].move(self.throw)
            self.view.stop()

    class ExtraPanacikButton(discord.ui.Button):
        def __init__(self, player, panak, disabled=False):
            self.player=player
            self.panak = panak
            icon = emoji.emojize(":plus:")
            super().__init__(emoji=icon, disabled=disabled)
    
        async def callback(self, interaction):
            if interaction.user.id != self.player.player.userid:
                await interaction.send("It´s not your turn!", ephemeral=True)
                return
            await interaction.response.edit_message(view=None)
            await self.panak.move(6)
            self.view.stop()

    async def processTurn(self, player, throw):
        #self.emojis = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(num) for num in range(1,5)]
        panakyInSpawn = [i for i in player.panaky if (i.inSpawn and await i.canMove(throw))] #kolko panakov je este na spawne
        availablePanaciky = [i for i in player.panaky if (await i.canMove(throw) and not i.inSpawn)] #panaciky na vybranie
        possibleMoves = len(availablePanaciky)+bool(panakyInSpawn)
        message = f"<i> {player.name} ({player.ikonky}) rolled {throw}" #STATUS MESSAGE
        
        if possibleMoves == 0:
            await asyncio.sleep(0.5*sleepTimeMult)
            await self.infomsg.edit(content=message+"\n<i> No possible move.") #STATUS MESSAGE
            return
        
        elif possibleMoves == 1:
            if len(availablePanaciky) == 0:
                chosen = panakyInSpawn[0]
            else:
                chosen = availablePanaciky[0]
            await asyncio.sleep(0.5*sleepTimeMult)
            await chosen.move(throw)
            
        else:
            chosen = availablePanaciky[0] #preemptívne vybereme panacika
            if not player.isCPU: #a ak hraca kontroluje clovek
                emojis = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(num) for num in range(5)]
                        
                for num,panak in enumerate(availablePanaciky,start=1):
                    panak.icon = emojis[num] #zmeni ikonu panacika na jeho korespondujuce cislo
                    
                self.polia = await self.posToPole(self.pocet_poli,self.panakAmount) #vykresli novu plochu na vyber panacika,aby hrac videl ktore si vybera
                await self.polemsg.edit(content=await self.pole(self.velkost,self.polia)) #POLE MESSAGE
                for panak in availablePanaciky:
                    panak.icon = panak.owner.ikonky

                viewObj = discord.ui.View(timeout=30)
                for i in range(1,len(availablePanaciky)+1):
                    viewObj.add_item(self.VyberPanacikButton(i,throw,player,availablePanaciky))
                    
                viewObj.add_item(self.ExtraPanacikButton(player,panakyInSpawn[0])) if bool(panakyInSpawn) else None
                await self.infomsg.edit(content=message+"\n<i> {} pawns can move..".format(len(availablePanaciky)+len(panakyInSpawn)),view=viewObj) #STATUS MESSAGE
                if await viewObj.wait():  #waits 30s and if it times out>
                    player.isCPU = True
                    await chosen.move(throw)
                    await self.infomsg.channel.send(embed=discord.Embed(title=f"{player.name} has gone AFK. A bot is taking their place.",description="Stats and rewards disabled.",color=discord.Color.red()),delete_after=60.0)
                    await self.infomsg.edit(view=None)
                    cloveceLogger.info("player is cpu now")
            else:
                if player.diffculty == "Hard":
                    chosen = await self.pickPanakBot(player, throw)
                await chosen.move(throw) 

    async def pickPanakBot(self,player,throw):
        availablePanaciky = sorted([i for i in player.panaky if (await i.canMove(throw))], reverse=True)
        for panak in availablePanaciky:
            if panak.inSpawn and type(self.polia[panak.startpos]) != Empty:
                cloveceLogger.debug("picking startpos kicker")
                return panak
            if not panak.inSpawn and not panak.homePos and panak.currPos:
                if type(self.polia[(panak.currPos + throw)%self.pocet_poli]) == Panak:
                    if self.polia[(panak.currPos + throw)%self.pocet_poli].team != panak.team:
                        cloveceLogger.debug("picking one that will be kicked from walking into")
                        return panak
            if throw == 6 and not panak.inSpawn and not panak.homePos and panak.stepsTaken > self.pocet_poli *0.6: #favour new panaky if nearing home
                for i in reversed(availablePanaciky):
                    cloveceLogger.debug("picking new cuz almost finishd")
                    if i.inSpawn:
                        return i
        else:
            return availablePanaciky[0]
                        
    async def pole(self, rozmer, polia): #enter at your own risk, here be dragons, the flying spaghetti mosnter and potentially some long lost treasure too. jk just some stupid string formatting
        """ocakava neparne cislo vacsie ako 5
        vlozi stavy (occupied/empty) vsetkych hracich policok do stringu
        a vracia string celej hracej plochy"""
        if rozmer < 5 or rozmer %2 == 0:
            return "This should never ever ever ever have happened. I already put up a safeguard against it but i´m keeping it here anyway."
        #i,hracie_pole = 0,str(" "+" |".join([str(i%10) for i in range(rozmer)])+"\n") #suradnice x, ergo tie cisla na vrchu
        #self.voidIcon = str(choice(lobbycog.serveremojis))
        hracie_pole = str((rozmer-3)//2*self.voidIcon)+(polia[-2].icon+polia[-1].icon+polia[0].icon)+str((rozmer-3)//2*self.voidIcon)+"\n" #vrchne tri polia (velkost-3)/2
        for i in range(1, rozmer//2-1): #ičkom naznacujem cislo riadku potom aj nadalej v tejto celej funkcii
            hracie_pole += str((rozmer-3)//2*self.voidIcon)+(polia[-i-2].icon+self.playerList[0].domceky[i-1].icon+polia[i].icon)+str((rozmer-3)//2*self.voidIcon)+"\n" #zvisle horne polia
        hracie_pole += "".join(polia[j].icon for j in list(range(-i-rozmer//2-2,-i-2)))+self.playerList[0].domceky[-1].icon+"".join(polia[j].icon for j in list(range(i+1,i+1+rozmer//2)))+"\n" #vodorovne horne polia
        hracie_pole += polia[-i-rozmer//2-3].icon+"".join(j.icon for j in self.playerList[3].domceky)+"\u274E"+"".join(j.icon for j in self.playerList[1].domceky[::-1])+polia[i+rozmer//2+1].icon+"\n" #domceky a bocne policka
        hracie_pole += "".join(polia[j].icon for j in list(range(-i-rozmer+rozmer//2-3,-i-rozmer-3,-1)))+self.playerList[2].domceky[-1].icon+"".join(polia[j].icon for j in list(range(i+rozmer,i+rozmer//2+1,-1)))+"\n" #vodorovne dolne polia
        i = rozmer//2+1 #toto musim jedine jenom iba ak rozmer = 5, v inom pripade sa to ajtak prepise v dalsom for
        for i in range(rozmer//2+2,rozmer-1): #rozmer//2 je akurat stredny riadok s domcekmi takze zacinam o 2 riadky nizsie
            hracie_pole += str((rozmer-3)//2*self.voidIcon)+(polia[-i-rozmer+1].icon+self.playerList[2].domceky[rozmer//2-i].icon+polia[rozmer+i-3].icon)+str((rozmer-3)//2*self.voidIcon)+"\n" #zvisle dolne polia
        hracie_pole += str((rozmer-3)//2*self.voidIcon)+(polia[rozmer+i].icon+polia[rozmer+i-1].icon+polia[rozmer+i-2].icon)+str((rozmer-3)//2*self.voidIcon)+"\n" #spodne tri
##        hracie_pole = list(hracie_pole)
##        for i in range(10):
##            a = randrange(0,len(hracie_pole))
##            if hracie_pole[a] == self.voidIcon:
##                hracie_pole[a] = "\U0001F383"
##        hracie_pole = "".join(hracie_pole)
        #return "```py\n"+hracie_pole+"\n```"
        return hracie_pole

    async def gamesetup(self, playerList, velkost=11):
        activePlayers = [player for player in playerList if player.isActive]
        pocet_poli = velkost*4-4 #pocet poli ktore panaciky musia prejst pred tym ako sa mohli dostat do domceka
        panakAmount = velkost//2-1   #kolko panacikov bude mat kazdy hrac, tiez determines the amount of domčekov
        for teamNum,player in enumerate(playerList):
            for panak in range(panakAmount):
                player.panaky.append(Panak(player, teamNum, player.ikonky, self))
       
        polia = await self.posToPole(pocet_poli, panakAmount) #vytvori prazdnu sachovnicu
        return polia, activePlayers, pocet_poli, panakAmount

    async def gameLoop(self):
        global polia #uz ma nesmierne sere furt passovat vsetko ako argumenty 
        while True: ###Main GameLoop ###
        #if True:
            if len(self.activePlayers) > 1:
                for player in self.activePlayers:
                    throw = await self.diceThrow(player)
                    await self.processTurn(player, throw)

                    self.polia = await self.posToPole(self.pocet_poli, self.panakAmount)

                    if any([not player.isCPU for player in self.activePlayers]):
                    #IF all players bots, skip this part
                        await self.polemsg.edit(content=await self.pole(self.velkost, self.polia)) #vykresli uz panacikmi populovanu sachovnicu  #CLOVECE MESSAGE
                    
                    if await player.checkWinCondition():
                        self.activePlayers.remove(player) #odoberieme hraca z aktivnych, aby sa ho uz nepytala hra na hodenie kocky
                        self.winPoradie.append(player) #zoznam pouzivany ako leaderboard na konci hry.
                        await self.infomsg.edit(content=f"<i> {player.name} finished the game.\n<i> {len(self.activePlayers)} players remaining.") #STATUS MESSAGE
                    
            else:
                self.winPoradie.append(self.activePlayers[-1]) #nesmieme vynechat posledného hraca ktory este nevosiel do domceku.
                embedVar = discord.Embed(title="Game finished. Thanks for playing!", description="-----------------------")
                
                dificulties = [player.diffculty for player in self.winPoradie]
                babygame = dificulties.count("Normal") == 1 and "Hard" not in dificulties #if only one player is higher than easy diff (the player who started against all easy bots)
                rewards = {"premSpinToken": f"{premSpinTokenIcon} 1x Premium Spin Token", "spinToken": f"{spinTokenIcon} 1x Spin Token", "spinShards":f"{spinShardIcon} 1x Spin Token Shard","nothing":None}
                rewardsindex = list(rewards.keys()) + ["nothing"]
                
                for n, j in enumerate(self.winPoradie, start=1):    #this is also so ugly
                    if n < 4 and not j.isCPU:
                        itemtogive = rewardsindex[n - bool(not babygame)]
                        embedVar.add_field(name=f"__{n}.place__ = **{str(j)}**", value=f"Reward: {rewards[itemtogive]}", inline=False)
                        key = "{} places".format(("First", "Second", "Third")[n-1])
                        j.player.stats[key] += 1
                        j.player.addItem(itemtogive, 1) if itemtogive else None
                        await j.player.checkShards()
                    else:
                        embedVar.add_field(name=f"__{n}.place__ = {str(j)}",value="\u200b",inline=False)
                embedVar.set_footer(text="Easy game, rewards reduced.") if babygame else None
                await self.infomsg.edit(embed=embedVar)#STATUS MESSAGE
                await self.lobby.disband()
                break

    async def cloveceStart(self, channel):
        while len(self.playerList) < 4:
            self.playerList.append(Player("Dummy",False,None,False,ikonky="",houseIcon=self.houseIcon))
        self.polia,self.activePlayers,self.pocet_poli,self.panakAmount = await self.gamesetup(self.playerList)
        self.polemsg = await channel.send("Rendering...")
        self.infomsg = await channel.send("Get ready!")
        await self.gameLoop()

class Player(object):
    """ulozi meno hraca, či je clovek alebo hrá zaň pocitac, či je este v hre, ak je pocitac aku obtiaznost ma
    a contains policka domcekov a zoznam panacikov"""
    def __init__(self,name,isCPU,diffculty=None,isActive=True,ikonky="?",houseIcon="?",profile=None):
        self.name = name #meno na zobrazenie
        self.isCPU = isCPU #za isCPU==True playerov rozhoduje program namiesto ludskeho hraca
        self.isActive = isActive #isActive==False playerov preskoci gameLoop, teda ak uz dokoncili hru napr. (and for internal use)
        self.diffculty = diffculty #ak human player,bude None inac zadam hned pri volaní
        self.panaky = [] #zoznam panacikov hraca
        self.domceky = [] #pouzite v fillHouses, na reset neokkupovanych policok
        self.ikonky = ikonky #ake znaky pouzivat na vykreslovanie panacikov
        self.houseIcon = houseIcon
        self.player = profile

    def __str__(self):
        return self.name

    async def checkWinCondition(self):
        """ak hrac ma vsetky panaciky v domceku, vrati True"""
        return all(self.domceky)

    async def fillHouses(self,panakAmount):
        """pouzite na reset neokkupovanych policok"""
        self.domceky = [Empty(self.houseIcon) for i in range(panakAmount)] #zoznam policok domceku hraca

class Panak(): #probably dont dediť this class
    """Obsahuje hraca kto panacika kontroluje, tím, ikonku na zobrazenie, akutalnu poziciu
ci je v spawne/na poli/alebo uz v domceku"""
    def __init__(self, owner, team, icon, game):
        self.owner = owner #nieco ako team len s player objectom, (#kebyze to nenecham na poslednu chvilu by som to spravil aj lepsie)
        self.team = team #koho hraca panacik, kebyze mam farby tak by bola farba ale nemam tak jednoducho int (alebo "a","b","c"..?? uvidim)
        self.icon = icon #akou ikonkou reprezentovat panacika na hracom poli
        self.startpos = self.team*(game.velkost-1) #poradie timu * velkost boardu - 1
        self.currPos = None #aktualna pozicia panacika na boarde, int alebo None
        self.inSpawn = True #panacik este neni vylozeny na board, na wikipedii to volajú ze stajna :D
        self.homePos = None #poloha panaciku v dome. None alebo int
        self.stepsTaken = 0 #aby som mohol KONZISTENTNE presuvat panaciky do domceka, lebo sposoby čekovania pozicie na sachovnici mali par edge caseov ktore som nemohol ignorovat
        self.game = game

    def __str__(self):
        return self.icon

    def __gt__(self, other):
        otherpos = other.stepsTaken or 0
        mypos = self.stepsTaken or 0
        return mypos > otherpos

    def __le__(self, other):
        otherpos = other.stepsTaken or 0
        mypos = self.stepsTaken or 0
        return mypos <= otherpos

    def __bool__(self):
        return True

    async def canMove(self, steps): #toto by som mal zjednodusit ale bojim sa ho dotknut
        """vrati True alebo False podla toho ci panacik moze stupit na policko [steps] krokov vpred. Berie do uvahy
obsadene policka svojmi panakmi, prekrocenie dlzky domceku a obsadene policka v domceku."""
        if self.inSpawn:
            if steps == 6: #ak je panacik este na spawne a hodime 6ku
                if type(self.game.polia[self.startpos]) == Empty: #ak je spawn policko prazdne
                    return True
                elif self.game.polia[self.startpos].team != self.team: #alebo je na nom enemy panacik
                    return True
                else: #ale ak uz na nej stoji svoj panacik tak nenechame spawnnut
                    return False

        elif self.homePos != None: #ak v domceku; homePos je pozicia v domceku, panakAmount je mnozstvo policok v domceku
            if self.homePos + steps >= self.game.panakAmount: #ak prekroci dlzku domceku
                return False
            else:
                if type(self.owner.domceky[self.homePos + steps]) != Empty: #ak uz v domceku na tom mieste stoji panacik
                    return False
                return True
        elif self.currPos != None: #ak na sachovnici
            tempPotentialMove = (self.stepsTaken + steps) % self.game.pocet_poli
            if self.stepsTaken+steps >= self.game.pocet_poli:
                if tempPotentialMove >= self.game.panakAmount: #ak prekroci dlzku domceku, ale teraz check z mimo domceku
                    return False
                elif type(self.owner.domceky[tempPotentialMove]) != Empty:#ak uz v domceku na tom mieste stoji panacik
                    return False
            return True
        else:
            return True

    async def move(self, amount):
        """posunie panacik na ktorom bola tato funkcia volana o (+ alebo aj -)amount polcika vopred
    ak ruleset povoli posun panacikov na uz occupied policko tak handles aj posunutie panacikov pozad
    Tiez sa stara o vyhadzovanie oponentov, o vchádzanie do domceka ba dokonca aj vychadzanie zo stajne."""
        if amount == -1:
            content = f"<i> {self.owner.name} (\"{self.owner.ikonky}\") bumped into themselves." # STATUS MESSAGE
        else:
            content = f"<i> {self.owner.name} (\"{self.owner.ikonky}\") rolled {str(amount)}"
        if self.inSpawn: #----vylozi na sachovnicu----#
            self.currPos = self.startpos
            self.inSpawn = False
            content+="\n<i> "+str(self)+" has been placed on the board." #STATUS MESSAGE
            if type(self.game.polia[self.currPos]) != Empty and self.game.polia[self.currPos].team != self.team: #kicking out
                self.game.polia[self.currPos].currPos = None
                self.game.polia[self.currPos].stepsTaken = 0
                self.game.polia[self.currPos].inSpawn = True
                content+="\n<i> "+str(self.game.polia[self.currPos])+" was kicked out!" #STATUS MESSAGE
            
        else:           #----pohyb na sachovnici----#
            content+=f"\n<i> Moving \"{str(self)}\" {amount} spaces" #STATUS MESSAGE
            self.stepsTaken += amount                                     #this is why english is fvcking better
            user = self.owner
            if not user.isCPU:
                user.player.stats["Steps taken"] += amount
            
            if self.stepsTaken >= self.game.pocet_poli: #ak ideme do domceku
                self.homePos = self.stepsTaken%self.game.pocet_poli
                self.currPos = None
            else:                           #ak este na sachovnici
                targetPole = (self.currPos + amount)%self.game.pocet_poli #wrap back na zaciatok ak dosiahol koniec hraciehpo pola
                
                if type(self.game.polia[targetPole]) != Empty: #ak pole na ktore chceme stupit neni prazdne
                    if self.game.polia[targetPole].team == self.team: #ak na target policku stoji teammate, posunieme ho naspat o 1 policko.
                        self.game.polia[self.currPos] = Empty(self.game.emptyIcon) #docasne vymazem panacika z hracieho pola lebo mi robil komplikacie ked som posuval panaka o jedno dopredu
                        await self.game.polia[targetPole].move(-1) #posunme panacika na destination policku o jedno dozadu
                        
                            #----------vyhadzovanie tuto dole---------#
                    else: #ak na target policku stoji oponent,
                        self.game.polia[targetPole].currPos = None
                        self.game.polia[targetPole].stepsTaken = 0
                        self.game.polia[targetPole].inSpawn = True
                        
                        user = self.game.polia[targetPole].owner
                        if user.isCPU != True:
                            user.player.stats["Times kicked out"] += 1
                        user = self.owner
                        if user.isCPU != True:
                            user.player.stats["Players kicked out"] += 1
                        content += "\n<i> "+str(self.game.polia[targetPole])+" was kicked out!"
                self.currPos = targetPole
        await self.game.infomsg.edit(content=content) #STATUS MESSAGE
        await asyncio.sleep(sleepTimeMult)


def setup(client, baselogger):
    client.add_cog(LobbyCog(client, baselogger))
