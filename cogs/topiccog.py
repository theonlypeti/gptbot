import os
from collections import namedtuple
from typing import Literal
import asyncprawcore.exceptions
from asyncpraw.models import ListingGenerator
from nextcord.ext import commands
import asyncpraw
import nextcord as discord
import json
import emoji
from dotenv import load_dotenv
from utils import embedutil

load_dotenv(r"./credentials/reddit.env")

#TODO AITA? maybe a multiselect for multiple subreddits

reddit = asyncpraw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID"),
                     client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                     user_agent=os.getenv("REDDIT_USER_AGENT"),
                     username=os.getenv("REDDIT_USERNAME"),
                     password=os.getenv("REDDIT_PWD"))

emoji_buttons = (emoji.emojize(":red_question_mark:"), emoji.emojize(":men’s_room:"), emoji.emojize(":men’s_room:"),
                 emoji.emojize(":women’s_room:"), emoji.emojize(":women’s_room:"),
                 emoji.emojize(":person_raising_hand:"), emoji.emojize(":person_raising_hand:"), emoji.emojize(":person_raising_hand:"),
                 emoji.emojize(":no_one_under_eighteen:")) #note, dont delete!
subs = ("AskReddit", "AskMen", "askteenboys", "AskWomen", "AskTeenGirls", "DAE+DoesAnybodyElse", "amitheonlyone", "AmItheAsshole", "AskRedditAfterDark")
subs_names = ("General questions", "Ask Men", "Ask Teen Boys", "Ask Women", "Ask Teen Girls", "Does Anybody Else..?", "Am I The Only One..?", "Am I The Asshole?", "After Dark")
Sub = namedtuple("Sub", ["id", "display_name", "emoji"])
subs = [Sub(id=i, display_name=n, emoji=e) for i, n, e in zip(subs, subs_names, emoji_buttons)]
emoji_buttons = list(dict.fromkeys(emoji_buttons)) #remove duplicates
root = os.getcwd()


class TopicCog(commands.Cog): #TODO make reddithandler not global, and have multiple handlers for multiple guilds, TODO check if it is good now
    def __init__(self, client):
        global reddithandler, logger
        self.client = client
        logger = client.logger.getChild('topicLogger')
        reddithandler = self.RedditHandler(self)
        reddithandler.openFilters()

    class TopicDropdown(discord.ui.Select):
        def __init__(self, cog):
            self.cog = cog
            opts = [discord.SelectOption(label=sub.display_name, value=sub.id, emoji=sub.emoji) for sub in subs]
            super().__init__(placeholder="Choose a subreddit", options=opts, min_values=1, max_values=len(opts))

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            await self.cog.nexttopic(interaction.channel, "+".join(self.values), interaction.user)

    class TopicThemeButtons(discord.ui.View):
        def __init__(self, cog):
            self.cog = cog
            super().__init__(timeout=180)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji_buttons[0])
        async def general(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            async with interaction.channel.typing():
                await self.cog.nexttopic(interaction.channel, "AskReddit", interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji_buttons[1])
        async def askmen(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            async with interaction.channel.typing():
                await self.cog.nexttopic(interaction.channel, "AskMen", interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji_buttons[2])
        async def askwomen(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            async with interaction.channel.typing():
                await self.cog.nexttopic(interaction.channel, "AskWomen", interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji_buttons[3])
        async def dae(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            async with interaction.channel.typing():
                await self.cog.nexttopic(interaction.channel, "DAE", interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji_buttons[4])
        async def over18(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            async with interaction.channel.typing():
                await self.cog.nexttopic(interaction.channel, "AskRedditAfterDark", interaction.user)

    @discord.slash_command(name="topic", description="For when you want to revive a dead chat")
    async def topic(self, ctx, selector: Literal["Classic", "Experimental"] = "Classic"):
        if selector == "Classic":
            embedVar = discord.Embed(title="Choose a question theme", description="Expect stupid questions as they are community submitted lol\n\n" + "\n".join(emoji_buttons[i] + " = " + ("General questions", "Ask men", "Ask women", "Does anybody else..?", "After dark")[i] for i in range(len(emoji_buttons))) + "\n" + 25 * "-")
            embedVar.set_footer(text="{} = Comments | {} = Next question | {} = Random question | {} = Try to refresh topics".format(emoji.emojize(":memo:"), emoji.emojize(":right_arrow:"), emoji.emojize(":shuffle_tracks_button:"), emoji.emojize(":counterclockwise_arrows_button:")))
            await ctx.send(embed=embedVar, view=self.TopicThemeButtons(self))
        else:
            embedVar = discord.Embed(title="Choose a question theme", description="Expect stupid questions as they are community submitted lol\n\nMix and match any categories.\n-----------")
            embedVar.set_footer(text="{} = Comments | {} = Next question | {} = Random question | {} = Try to refresh topics".format(emoji.emojize(":memo:"), emoji.emojize(":right_arrow:"), emoji.emojize(":shuffle_tracks_button:"), emoji.emojize(":counterclockwise_arrows_button:")))
            viewObj = discord.ui.View()
            viewObj.add_item(self.TopicDropdown(self))
            await ctx.send(embed=embedVar, view=viewObj)

    class TopicNextButtons(discord.ui.View):
        def __init__(self, cog, sub="AskReddit"):
            super().__init__(timeout=None)
            self.subname: str = sub
            self.cog = cog
            self.subr = None

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":memo:"))
        async def commentsbutton(self, button, interaction):
            # async with interaction.channel.typing():
            # await interaction.response.defer()
            button.style = discord.ButtonStyle.green
            button.disabled = True
            await interaction.edit(view=self)
            footer = interaction.message.embeds[0].footer
            if footer:
                ID = footer.text[4:11].strip()
            else:
                return
            # await reaction.message.channel.send(redditapi.reddithandler.getPostFromID(reaction.message.embeds[0].footer.text))
            embedVar = reddithandler.comments(await reddithandler.getPostFromID(ID), interaction.user.color)
            viewObj = discord.ui.View()
            viewObj.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="More", url="https://redd.it/" + ID))
            await interaction.send(embed=embedVar, view=viewObj)
            logger.debug(f"{interaction.user.name} requested comments")

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":right_arrow:"))
        async def nextbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            button.disabled = True
            self.children[1].disabled = True  # this is the same as before but somehow still wouldnt work
            self.children[2].disabled = True
            self.children[3].disabled = True
            await interaction.response.edit_message(view=self)
            await self.cog.nexttopic(interaction.channel, self.subname, interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, disabled=False, emoji=emoji.emojize(":shuffle_tracks_button:"))
        async def randbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            button.disabled = True
            try:
                await self.cog.randtopic(interaction.channel, self.subname, interaction.user)
                self.children[1].disabled = True
                self.children[3].disabled = True
            except asyncprawcore.exceptions.Forbidden:
                await embedutil.error(interaction, "This subreddit does not allow sorting by random, sorry.", delete=10.0)
                button.style = discord.ButtonStyle.grey
            else:
                await interaction.response.edit_message(view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":counterclockwise_arrows_button:"))
        async def reloadbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            button.disabled = True
            await interaction.response.edit_message(view=self)
            #async with interaction.channel.typing():
            reddithandler.reset(self.subname)

        async def on_timeout(self) -> None:
            for ch in self.children[1:-1]:
                ch.disabled = True
                #hm i would need a message reference to update the view frick

    async def nexttopic(self, channel, sub, requester): #TODO i should just replace this with interaction. im too lazy rn
        subm: asyncpraw.reddit.Submission = await reddithandler.submission(sub)
        embedVar = await reddithandler.prettyprint(subm, requester)
        if embedVar is None:
            await self.sendNoTopic(channel, sub)
        else:
            viewObj = self.TopicNextButtons(self, sub=sub)
            viewObj.add_item(
                discord.ui.Button(style=discord.ButtonStyle.link, url="https://redd.it/" + subm.id, emoji=emoji.emojize(":globe_with_meridians:")))
            viewObj.children[2].disabled = (sub == "AskWomen")
            await channel.send(embed=embedVar, view=viewObj)

    async def randtopic(self, channel, sub, requester):
        subr: asyncpraw.reddit.Subreddit = await reddit.subreddit(sub)
        ques: asyncpraw.reddit.Submission = await subr.random()
        if ques is None:
            await self.sendNoTopic(channel, sub)
        else:
            embedVar = await reddithandler.prettyprint(ques, requester) #it should tho
            viewObj = self.TopicNextButtons(self, sub=sub)
            viewObj.add_item(
                discord.ui.Button(style=discord.ButtonStyle.link, url="https://redd.it/" + ques.id, emoji=emoji.emojize(":globe_with_meridians:")))
            await channel.send(embed=embedVar, view=viewObj)

    class TopicEmptyButton(discord.ui.View):
        def __init__(self, cog, sub="None"):
            self.cog = cog
            self.sub = sub
            super().__init__(timeout=180)

        @discord.ui.button(label="Different topic", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":right_arrow_curving_left:"))
        async def differenttopicsbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            await self.cog.topic(interaction)

        @discord.ui.button(label="Random", style=discord.ButtonStyle.gray, disabled=False, emoji=emoji.emojize(":shuffle_tracks_button:"))
        async def randbutton2(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            async with interaction.channel.typing():
                await self.cog.randtopic(interaction.channel, self.sub, interaction.user)

    async def sendNoTopic(self, channel, sub):
        embedVar = discord.Embed(
            title="No new fresh posts available. Check back later, try random old posts (" + emoji.emojize(
                ":shuffle_tracks_button:") + ") or choose a different topic!",
            color=discord.Colour.red())
        embedVar.set_image(url="https://http.cat/404")
        await channel.send(embed=embedVar, view=self.TopicEmptyButton(self, sub=sub))

    @discord.slash_command(description="Disallow some sensitive themes and topics from coming up when binging",guild_ids=[860527626100015154, 800196118570205216])  # TODO make it admin only
    async def topic_filters(self, ctx):
        embedVar = discord.Embed(title="Filters", description="Selected options mean topics of those nature will be included. When done with your selection, just click off the select bar.",color=ctx.user.color)
        viewObj = reddithandler.filtersSettings(ctx)
        await ctx.send(embed=embedVar, view=viewObj)

    @discord.slash_command(name="sub", description="Retrieve a random post from a given subreddit.")
    async def sub(self, ctx: discord.Interaction, subreddit: str = discord.SlashOption(name="subreddit",
                                                                                       description="a subreddit name without the /r/")):
        await ctx.response.defer()
        sub = await reddit.subreddit(subreddit.strip("/r/"))
        await sub.load()
        if not ctx.channel.is_nsfw() and sub.over18:
            await ctx.send(embed=discord.Embed(
                title="That is an NSFW subreddit you are tying to send into a non-NSFW text channel.",
                color=discord.Color.red()))
            return
        try:
            try:
                sub = await reddit.subreddit(subreddit.strip("/r/"))
                post = await sub.random()
            except Exception as e:
                #        except redditapi.prawcore.exceptions.NotFound:
                #            await ctx.channel.send("That subreddit is not found??")
                #        except redditapi.prawcore.exceptions.Forbidden:
                #            await ctx.channel.send("Forbidden: received 403 HTTP response, what kinda sub are you trying to see?!?")
                await ctx.send(f"{e}")  # i don't really know how to handle these errors xd
                logger.error(e)
            else:
                if not post:
                    await ctx.send("That subreddit does not allow sorting by random, sorry.")
                    return
                if post.is_self:  # if only textpost, no link or image
                    viewObj = discord.ui.View()
                    viewObj.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        url="https://redd.it/" + post.id,
                        label="Comments",
                        emoji=emoji.emojize(":memo:")))
                    await ctx.send(embed=discord.Embed(
                        title=post.title,
                        description=(post.selftext if post.selftext else None)
                    ), view=viewObj)
                else:
                    await ctx.send(post.url)
        except Exception as e:
            await ctx.send(f"{e}")
            raise e

    @discord.slash_command(name="cat", description="Send a random cat pic")
    async def cat(self, ctx):
        await ctx.response.defer()
        # subs = "absolutelynotmeow_irl,Catsinasock,kittyhasaquestion,catloaf,thisismylifemeow,MEOW_IRL,noodlebones,bottlebrush,notmycat,Blep,CatsOnCats,PetAfterVet,CuddlePuddle,CatsAndPlants,curledfeetsies,teefies,tuckedinkitties,catfaceplant,CatsAndDogsBFF,squishypuppers,airplaneears,shouldercats,PeanutWhiskers,catbellies,CatCircles,catfaceplant,catsonglass,ragdolls,fatSquirrelHate,SupermodelCats,Catswhoyell,IllegallySmolCats,aww,AnimalsBeingBros,peoplefuckingdying,thecatdimension,TouchThaFishy,FancyFeet,cuddleroll,DrillCats,CatsWhoYell,catsareliquid,blurrypicturesofcats,spreadytoes,sorryoccupied,politecats,blackpussy,KittyTailWrap,thecattrapisworkings,khajiithaswares,catgrabs,stolendogbeds,bridgecats,standardissuecats,catswhoquack,catpranks,catsarealiens,dagadtmacskak,fatcat,fromKittenToCat,illegallySmolCats,MaineCoon,noodlebones,politecats,scrungycats,shouldercats,sorryoccupied,stolendogbeds,stuffOnCats,thinkcat,disneyeyes,cuddlykitties,wet_pussy,girlswithhugepussies,catsinboxes,catsonmeth,catsstandingup,catsstaringatthings,catsvsthemselves,catswhoblep,catswithjobs,catswithmustaches,OneOrangeBraincell".split(",")
        subs = await reddit.subreddit('absolutelynotmeow_irl+Catsinasock+kittyhasaquestion+catloaf+thisismylifemeow+MEOW_IRL+noodlebones+bottlebrush+notmycat+Blep+CatsOnCats+PetAfterVet+CuddlePuddle+CatsAndPlants+curledfeetsies+teefies+tuckedinkitties+catfaceplant+CatsAndDogsBFF+squishypuppers+airplaneears+shouldercats+PeanutWhiskers+catbellies+CatCircles+catfaceplant+catsonglass+ragdolls+fatSquirrelHate+SupermodelCats+Catswhoyell+IllegallySmolCats+aww+AnimalsBeingBros+peoplefuckingdying+thecatdimension+TouchThaFishy+FancyFeet+cuddleroll+DrillCats+CatsWhoYell+catsareliquid+blurrypicturesofcats+spreadytoes+sorryoccupied+politecats+blackpussy+KittyTailWrap+thecattrapisworkings+khajiithaswares+catgrabs+stolendogbeds+bridgecats+standardissuecats+catswhoquack+catpranks+catsarealiens+dagadtmacskak+fatcat+fromKittenToCat+illegallySmolCats+MaineCoon+noodlebones+politecats+scrungycats+shouldercats+sorryoccupied+stolendogbeds+stuffOnCats+thinkcat+disneyeyes+cuddlykitties+wet_pussy+girlswithhugepussies+catsinboxes+catsonmeth+catsstandingup+catsstaringatthings+catsvsthemselves+catswhoblep+catswithjobs+catswithmustaches+OneOrangeBraincell')
        while True:
            post = await subs.random()
            if post.url.startswith("https://i"):
                await ctx.send(post.url)
                return

    @discord.slash_command(name="bored", description="Word games to play with friends in a chat")
    async def bored(self, ctx: discord.Interaction):
        await ctx.response.defer()
        try:
            sub = await reddit.subreddit("ThreadGames")
            post = await sub.random()

            if post.is_self:
                viewObj = discord.ui.View()
                viewObj.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link, url="https://redd.it/" + post.id, label="Comments", emoji=emoji.emojize(":memo:")))
                await ctx.send(embed=discord.Embed(title=post.title, description=(post.selftext[:4096] if post.selftext else "")), view=viewObj)
            else:
                await ctx.send(post.url)
        except Exception as e:
            await ctx.send(f"{e}")
            raise e

    @discord.slash_command(name="beans", description="beeeeeeeeeeeeeeeaaaaaaaaaans")
    async def beans(self, ctx: discord.Interaction):
        await ctx.response.defer()
        try:
            sub = await reddit.subreddit("jellybeantoes")
            post = await sub.random()

            if post.is_self:
                viewObj = discord.ui.View()
                viewObj.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link, url="https://redd.it/" + post.id, label="Comments",
                    emoji=emoji.emojize(":memo:")))
                await ctx.send(
                    embed=discord.Embed(title=post.title, description=(post.selftext[:4096] if post.selftext else "")),
                    view=viewObj)
            else:
                await ctx.send(post.url)
        except Exception as e:
            await ctx.send(f"{e}")
            raise e

    @discord.slash_command(name="joke", description="Give me a joke!")
    async def jokes(self, ctx: discord.Interaction):
        await ctx.response.defer()
        try:
            # sub = await reddit.subreddit("3amjokes+cleandadjokes+dadjokes+TwoSentenceComedy+cleanjokes")
            sub = await reddit.subreddit("3amjokes+cleandadjokes+dadjokes+cleanjokes")
            post = await sub.random()

            if post.is_self:
                await ctx.send(
                    embed=discord.Embed(title=post.title, description=(f"||{post.selftext[:4092]}||" if post.selftext else "")))
            else:
                await ctx.send(post.url)
        except Exception as e:
            await ctx.send(f"{e}")
            raise e

    ##############
    # TODO check out
    # for submission in reddit.subreddit("all").stream.submissions(): #or reddit.front
    # strem = reddit.subreddit("all").stream
    # strem
    # print(submission)

    # and

    # for submission in reddit.subreddit("test").random_rising():
    # print(submission.title)

    # this piece of a crap code was made quite possibly drunk at midnight frustrated at a topic bot that ran out of questions to offer so take it with a grain of salt
    class RedditHandler(object):
        def __init__(self, cog):
            self.cog = cog
            self.usedposts = []  # array of used post ids
            self.subGenerators: dict[str:ListingGenerator] = {}  # dict of subs and their posts
            self.filters: dict[str, bool] = {}
            self.filterStrings: dict[str, list[str]] = {}
            self.num_of_comments = 4
            self.max_comment_length = 1024 - 16
            self.max_desc_length = 4090

        def openFilters(self):
            try:
                with open(root + "\\data\\redditfiltertoggles.txt", "r") as file:
                    self.filters: dict[str, ...] = json.load(file)
            except FileNotFoundError:
                self.filters = {"nsfw": True, "relationships": True, "serious": True, "cliche": False}
                logger.debug("generated filtersToggles")
                self.saveFilters()
            with open(root + "\\data\\redditfilterstrings.json", "r") as file:
                # for line in file.readlines():
                #     line = line.strip("\n").split("=")
                #     self.filterStrings[line[0]] = line[1].split(",")
                self.filterStrings = json.load(file)

        def saveFilters(self):
            with open(root + r"/data/redditfiltertoggles.txt", "w") as file:
                json.dump(self.filters, file)
            logger.info("saved filtersToggles")

        class FilterDropdown(discord.ui.Select):
            def __init__(self, cog, color):
                self.filters = cog.filters
                self.color = color
                self.cog = cog
                options = [discord.SelectOption(label=name.title(), default=value, value=name) for name, value in self.filters.items()]
                super().__init__(options=options, min_values=0, max_values=len(self.filters))

            async def callback(self, interaction):
                self.cog.filters = {i: False for i in self.filters.keys()}
                await interaction.response.edit_message(embed=discord.Embed(title="Filters", description="Filters have been set.", color=self.color), view=None)
                for option in self.values:
                    self.cog.filters[option] = True
                self.cog.saveFilters()
                for sub, posts in self.cog.subGenerators.items():
                    self.cog.subGenerators[sub] = self.cog.filterPost(posts)

        def filtersSettings(self, ctx):
            viewObj = discord.ui.View()
            viewObj.add_item(self.FilterDropdown(self, ctx.user.color))
            return viewObj

        async def getGenerator(self, subname: str = "AskReddit", new: bool = False):

            if not new:
                if subname in self.subGenerators:
                    return self.subGenerators[subname]

            subs = {"AskMen": reddit.subreddit("AskMen+askteenboys"),
                    "AskWomen": reddit.subreddit("AskWomen+AskTeenGirls"),
                    "DAE": reddit.subreddit("DAE+doesanybodyelse+amitheonlyone+AmItheAsshole")}
            # "DAE": reddit.subreddit("")}
            if subname in subs:
                subreddit = await subs[subname]
            else:
                subreddit = await reddit.subreddit(subname)

            if not new:
                gener = subreddit.hot()
            else:
                gener = subreddit.new()
            self.subGenerators[subname] = gener
            logger.debug(f"generated {subname} generator")
            return gener

        def filterPost(self, post: asyncpraw.reddit.Submission):  # TODO TEST FIX if multiple filters filter out the same q, the shit breaks
            if post.stickied:
                return False
            for filt, include in self.filters.items():
                if not include:
                    for word in self.filterStrings[filt]:  # filter key
                        if word in post.title: #or post.score < 25
                            logger.debug(f"found {word} in {post.title}, skipping")
                            return False
            return True

        async def submission(self, sub: str):
            try:
                while True:
                    post = await anext(self.subGenerators[sub])
                    if self.filterPost(post):
                        break

                post.title = post.title.replace("of reddit ", "")
                post.title = post.title.replace("of reddit,", "")
                post.title = post.title.replace("of Reddit ", "")
                post.title = post.title.replace("of Reddit,", "")
                post.title = post.title.replace("redditors", "people")
                post.title = post.title.replace("Redditors", "People")
                post.title = post.title.replace("DAE", "Does anyone else")
                post.title = post.title.replace("IAE", "Is anyone else")
                post.title = post.title.replace("AITOO", "Am i the only one")
                post.title = post.title.replace("ARAD", "After dark")
                return post
            except KeyError:
                logger.debug(f"{sub} sub hasn't been initialised yet")
                await self.getGenerator(sub)
                return await self.submission(sub)
            except StopAsyncIteration:
                await self.getGenerator(sub, new=True)
                return await self.submission(sub)

        @staticmethod
        async def getPostFromID(ID: str) -> asyncpraw.reddit.Submission:
            return await reddit.submission(ID)

        def basicprint(self, post):  #what was this for?
            pass
            #return embedVar

        async def prettyprint(self, post: asyncpraw.reddit.Submission, *attr):
            logger.debug(post.subreddit.display_name)
            # embedVar = discord.Embed(title=post.title if post.title and len(post.title) <= 256 else "\u200b", description=post.title if post.title and len(post.title) > 256 else (post.selftext[:self.max_desc_length] + ("... " if len(post.selftext) > self.max_comment_length else "")) if (post.selftext and len(post.selftext) <= self.max_desc_length) else "\u200b", color=attr[0].color if attr else discord.Colour.random())
            embedVar = discord.Embed(title=post.title if post.title and len(post.title) <= 256 else "\u200b", description=post.title if post.title and len(post.title) > 256 else (post.selftext[:self.max_desc_length] + ("... " if len(post.selftext) > self.max_comment_length else "")) if post.selftext else "\u200b", color=attr[0].color if attr else discord.Colour.random())
            embedVar.set_footer(text=f"id: {post.id} |{list(filter(lambda s: post.subreddit.display_name.lower() in s.id.lower(), subs))[0].emoji} | /topic to change topic" + (" | Low score. Might be stupid?!" if post.score < 100 else f" | {str(post.score)} points."))
            return embedVar

        def comments(self, post: asyncpraw.reddit.Submission, color=None):  # please dont judge me its so fucked up
            j = 0  # iterator variable, counts number of valid comments
            toolong = False
            embedVar = discord.Embed(title="What do other people think?", description=post.title + "\n________________\n" + post.selftext[:min(300, len(post.selftext))] + ("... " if len(post.selftext) > 299 else ""), color=color or discord.Color.gold())
            for comment in post.comments:
                if isinstance(comment.author, type(None)):  # if comment deleted
                    continue
                if comment.author.name == "AutoModerator":
                    continue
                if comment.stickied:  # mod comment
                    continue
                if len(comment.body) > self.max_comment_length:  # by default 1024-16
                    toolong = True
                    continue
                if j == 0:
                    embedVar.add_field(name="Replies:\n" + str(15 * "-"), value=comment.body, inline=False)
                    prev_comment = comment
                    j += 1
                    continue
                else:
                    score = prev_comment.score - 1
                    embedVar.add_field(name="{} {} {}agree{}.".format(abs(score), ("person" if abs(score) == 1 else "people"), ("dis" if score < 0 else ""), ("s" if score == 1 else "")),value=str(15 * "-") + "\n" + comment.body, inline=False)
                    j += 1
                    prev_comment = comment
                if j == self.num_of_comments:  # by default 4
                    break
            if j == 0:
                if toolong:
                    embedVar = discord.Embed(title="Comments too long.",
                                             description="Blame discord, can´t post longer messages than 1024 letters. You wouldn´t want to read a wall of text anyway.")
                    embedVar.add_field(name="{} comment{} available:".format(post.num_comments, ("s" if post.num_comments != 1 else "")), value="https://redd.it/" + post.id)
                    return embedVar
                else:
                    return discord.Embed(title="No comments available.",
                                         description="The topic was not popular enough.")
            else:
                score = prev_comment.score - 1
                # embedVar.add_field(name="{} {} {}agree{}.".format(abs(score),("person" if abs(score) == 1 else "people"),("dis" if score<0 else ""),("s" if score ==1 else "")),value=str(15*"-")+"\nMore at: https://redd.it/"+post.id,inline=False)
                embedVar.add_field(
                    name="{} {} {}agree{}.".format(abs(score), ("person" if abs(score) == 1 else "people"),("dis" if score < 0 else ""), ("s" if score == 1 else "")),value=str(15 * "-"), inline=False)
                return embedVar

        def reset(self, sub: str):
            del self.subGenerators[sub]


def setup(client):
    client.add_cog(TopicCog(client))
