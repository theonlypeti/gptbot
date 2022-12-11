import os
import random
from nextcord.ext import commands
import praw
import nextcord as discord
import json
import emoji
from dotenv import load_dotenv
load_dotenv(r"./credentials/reddit.env")

reddit = praw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID"),
                     client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                     user_agent=os.getenv("REDDIT_USER_AGENT"),
                     username=os.getenv("REDDIT_USERNAME"),
                     password=os.getenv("REDDIT_PWD"))

emoji_buttons = (emoji.emojize(":red_question_mark:"), emoji.emojize(":men’s_room:"), emoji.emojize(":men’s_room:"),
                 emoji.emojize(":women’s_room:"), emoji.emojize(":women’s_room:"),
                 emoji.emojize(":person_raising_hand:"), emoji.emojize(":person_raising_hand:"),
                 emoji.emojize(":no_one_under_eighteen:"))
subs = ("AskReddit", "AskMen", "AskTeenBoys", "AskWomen", "AskTeenGirls", "DAE", "DoesAnybodyElse", "AskRedditAfterDark")
subemoji = {k: v for k, v in zip(subs, emoji_buttons)}
emoji_buttons = (emoji.emojize(":red_question_mark:"), emoji.emojize(":men’s_room:"), emoji.emojize(":women’s_room:"),emoji.emojize(":person_raising_hand:"), emoji.emojize(":no_one_under_eighteen:"))
root = os.getcwd()

#TODO async praw, see bottemplate

class TopicCog(commands.Cog):
    def __init__(self, client, baselogger):
        global reddithandler, topicLogger
        self.client = client
        topicLogger = baselogger.getChild('topicLogger')
        reddithandler = self.RedditHandler(self)
        reddithandler.openFilters()

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
    async def topic(self, ctx):
        embedVar = discord.Embed(title="Choose a question theme",description="Expect stupid questions as they are community submitted lol\n\n" + "\n".join(emoji_buttons[i] + " = " + ("General questions", "Ask men", "Ask women", "Does anybody else..?", "After dark")[i] for i in range(len(emoji_buttons))) + "\n" + 25 * "-")
        embedVar.set_footer(text="{} = Comments | {} = Next question | {} = Random question | {} = Try to refresh topics".format(emoji.emojize(":memo:"), emoji.emojize(":right_arrow:"), emoji.emojize(":shuffle_tracks_button:"),emoji.emojize(":counterclockwise_arrows_button:")))
        await ctx.send(embed=embedVar, view=self.TopicThemeButtons(self))

    class TopicNextButtons(discord.ui.View):
        def __init__(self, cog, sub="AskReddit"):
            super().__init__(timeout=None)
            self.sub = sub
            self.cog = cog

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
            embedVar = reddithandler.comments(reddithandler.getPostFromID(ID),interaction.user.color)
            viewObj = discord.ui.View()
            viewObj.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="More", url="https://redd.it/" + ID))
            await interaction.send(embed=embedVar, view=viewObj)
            topicLogger.debug(f"{interaction.user.name} requested comments")

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":right_arrow:"))
        async def nextbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            button.disabled = True
            self.children[1].disabled = True  # this is the same as before but somehow still wouldnt work
            self.children[2].disabled = True
            self.children[3].disabled = True
            await interaction.response.edit_message(view=self)
            await self.cog.nexttopic(interaction.channel, self.sub, interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, disabled=False,emoji=emoji.emojize(":shuffle_tracks_button:"))
        async def randbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            button.disabled = True
            self.children[1].disabled = True
            self.children[3].disabled = True
            await interaction.response.edit_message(view=self)
            await self.cog.randtopic(interaction.channel, self.sub, interaction.user)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":counterclockwise_arrows_button:"))
        async def reloadbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            button.disabled = True
            await interaction.response.edit_message(view=self)
            #async with interaction.channel.typing():
            reddithandler.reset()

    async def nexttopic(self, channel, sub, requester):
        embedVar = reddithandler.prettyprint(reddithandler.submission(sub), requester)
        if embedVar == None:
            await self.sendNoTopic(channel, sub)
        else:
            viewObj = self.TopicNextButtons(self, sub=sub)
            viewObj.children[2].disabled = (sub == "AskWomen")
            await channel.send(embed=embedVar, view=viewObj)

    async def randtopic(self, channel, sub, requester):
        ques = reddit.subreddit(sub).random()
        if ques is None:
            await self.sendNoTopic(channel, sub)
        else:
            embedVar = reddithandler.prettyprint(ques, requester)
            await channel.send(embed=embedVar, view=self.TopicNextButtons(self,sub=sub))

    class TopicEmptyButton(discord.ui.View):
        def __init__(self,cog, sub="None"):
            self.cog = cog
            self.sub = sub
            super().__init__(timeout=180)

        @discord.ui.button(label="Different topic", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":right_arrow_curving_left:"))
        async def differenttopicsbutton(self, button, interaction):
            button.style = discord.ButtonStyle.green
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            self.cog.topic(interaction)

        @discord.ui.button(label="Random", style=discord.ButtonStyle.gray, disabled=False,emoji=emoji.emojize(":shuffle_tracks_button:"))
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
        embedVar.set_thumbnail(url="https://cdn-0.emojis.wiki/emoji-pics/google/stop-sign-google.png")
        await channel.send(embed=embedVar, view=self.TopicEmptyButton(self, sub=sub))

    @discord.slash_command(description="Disallow some sensitive themes and topics from coming up when binging",guild_ids=[860527626100015154, 800196118570205216])  # TODO make it admin only
    async def topic_filters(self, ctx):
        embedVar = discord.Embed(title="Filters", description="Selected options mean topics of those nature will be included. When done with your selection, just click off the select bar.",color=ctx.user.color)
        viewObj = reddithandler.filtersSettings(ctx)
        await ctx.send(embed=embedVar, view=viewObj)

    @discord.slash_command(name="sub", description="Retrieve a random post from a given subreddit.")
    async def sub(self, ctx, subreddit: str = discord.SlashOption(name="subreddit", description="a subreddit name without the /r/")):
        #await ctx.response.defer()
        if (not ctx.channel.is_nsfw() and reddit.subreddit(subreddit.removeprefix("/r/")).over18) and not ctx.user.id == 617840759466360842:
            await ctx.send(embed=discord.Embed(title="That is an NSFW subreddit you are tying to send into a non-NSFW text channel.",color=discord.Color.red()))
            return
        try:
            await ctx.response.defer()
            try:
                post = reddit.subreddit(subreddit.removeprefix("/r/")).random()
            except Exception as e:
                ##        except redditapi.prawcore.exceptions.NotFound:
                ##            await ctx.channel.send("That subreddit is not found??")
                ##        except redditapi.prawcore.exceptions.Forbidden:
                ##            await ctx.channel.send("Forbidden: received 403 HTTP response, what kinda sub are you trying to see?!?")
                await ctx.send(e)
                topicLogger.error(e)
            else:
                if not post:
                    await ctx.send("That subreddit does not allow sorting by random, sorry.")
                    return
                if post.is_self:
                    viewObj = discord.ui.View()
                    viewObj.add_item(discord.ui.Button(style=discord.ButtonStyle.link, url="https://redd.it/" + post.id,label="Comments", emoji=emoji.emojize(":memo:")))
                    await ctx.send(embed=discord.Embed(title=post.title, description=(post.selftext if post.selftext else None)), view=viewObj)
                else:
                    await ctx.send(post.url)
        except Exception as e:
            await ctx.send(e)
            raise e

    @discord.slash_command(name="cat", description="Send a random cat pic")
    async def cat(self, ctx):
        await ctx.response.defer()
        subs = "absolutelynotmeow_irl,Catsinasock,kittyhasaquestion,catloaf,thisismylifemeow,MEOW_IRL,noodlebones,bottlebrush,notmycat,Blep,CatsOnCats,PetAfterVet,CuddlePuddle,CatsAndPlants,curledfeetsies,teefies,tuckedinkitties,catfaceplant,CatsAndDogsBFF,squishypuppers,airplaneears,shouldercats,PeanutWhiskers,catbellies,CatCircles,catfaceplant,catsonglass,ragdolls,fatSquirrelHate,SupermodelCats,Catswhoyell,IllegallySmolCats,aww,AnimalsBeingBros,peoplefuckingdying,thecatdimension,TouchThaFishy,FancyFeet,cuddleroll,DrillCats,CatsWhoYell,catsareliquid,blurrypicturesofcats,spreadytoes,sorryoccupied,politecats,blackpussy,KittyTailWrap,thecattrapisworkings,khajiithaswares,catgrabs,stolendogbeds,bridgecats,standardissuecats,catswhoquack,catpranks,catsarealiens,dagadtmacskak,fatcat,fromKittenToCat,illegallySmolCats,MaineCoon,noodlebones,politecats,scrungycats,shouldercats,sorryoccupied,stolendogbeds,stuffOnCats,thinkcat,disneyeyes,cuddlykitties,wet_pussy,girlswithhugepussies,catsinboxes,catsonmeth,catsstandingup,catsstaringatthings,catsvsthemselves,catswhoblep,catswithjobs,catswithmustaches,OneOrangeBraincell".split(",")
        while True:
            post = [i for i in reddit.subreddit(random.choice(subs)).hot(limit=20)]
            random.shuffle(post)
            for i in post:
                if i.url.startswith("https://i"):
                    await ctx.send(i.url)
                    return

    @discord.slash_command(name="bored", description="Word games to play with friends in a chat")
    async def bored(self, ctx):
        try:
            post = reddit.subreddit("threadgames").random()
        except Exception as e:
            await ctx.send(e)
            raise e
        else:
            if post.is_self:
                viewObj = discord.ui.View()
                viewObj.add_item(discord.ui.Button(style=discord.ButtonStyle.link, url="https://redd.it/" + post.id, label="Comments", emoji=emoji.emojize(":memo:")))
                await ctx.send(embed=discord.Embed(title=post.title, description=(post.selftext if post.selftext else "")), view=viewObj)
            else:
                await ctx.send(post.url)

    ##############
    # TODO check out
    # for submission in reddit.subreddit("all").stream.submissions(): or reddit.front
    # print(submission)

    # and

    # for submission in reddit.subreddit("test").random_rising():
    # print(submission.title)

    # this piece of a crap code was made quite possibly drunk at midnight frustrated at a topic bot that ran out of questions to offer so take it with a grain of salt
    class RedditHandler(object):
        def __init__(self, cog):
            self.cog = cog
            self.usedposts = []  # array of used post ids
            self.availablePosts = {}  # dict of subs and their posts
            self.filters = {}
            self.filterStrings = {}
            self.num_of_comments = 4
            self.max_comment_length = 1024 - 16

        def openFilters(self):
            try:
                with open(root + "\\data\\redditfiltertoggles.txt", "r") as file:
                    self.filters = json.load(file)
            except FileNotFoundError:
                self.filters = {"nsfw": True, "relationships": True, "serious": True,"cliche":False}
                topicLogger.info("generated filtersToggles")
            with open(root + "\\data\\redditfilterstrings.txt", "r") as file:
                for line in file.readlines():
                    line = line.strip("\n").split("=")
                    self.filterStrings[line[0]] = line[1].split(",")

        def saveFilters(self):
            with open(root + r"/data/redditfiltertoggles.txt", "w") as file:
                json.dump(self.filters, file)
            topicLogger.info("saved filtersToggles")

        class FilterDropdown(discord.ui.Select):
            def __init__(self, cog, color):
                self.filters = cog.filters
                self.color = color
                self.cog = cog
                options = [discord.SelectOption(label=name.title(), default=value, value=name) for name, value in self.filters.items()]
                super().__init__(options=options, min_values=0, max_values=len(self.filters))

            async def callback(self, interaction):
                self.cog.filters = {i: False for i in self.filters.keys()}
                await interaction.response.edit_message(embed=discord.Embed(title="Filters", description="Filters have been set.", color=self.color),view=None)
                for option in self.values:
                    self.cog.filters[option] = True
                self.cog.saveFilters()
                for sub, posts in self.cog.availablePosts.items():
                    self.cog.availablePosts[sub] = self.cog.filterPosts(posts)

        def filtersSettings(self, ctx):
            viewObj = discord.ui.View()
            viewObj.add_item(self.FilterDropdown(self, ctx.user.color))
            return viewObj

        def downloadPosts(self, subreddit):
            posts = []
            for submission in subreddit.hot(limit=100):
                posts.append(submission)
            topicLogger.debug(len(posts))
            if len(posts) < 10:
                topicLogger.debug("getting from new")
                for submission in subreddit.new(limit=20):
                    posts.append(submission)
            topicLogger.debug(len(posts))
            if len(posts) < 10:
                topicLogger.debug("getting from random")
                if subreddit.random() is not None:
                    posts.append(subreddit.random())
            for post in posts:
                post.title = post.title.replace("people of reddit", "People")
                post.title = post.title.replace("People of reddit", "People")
                post.title = post.title.replace("of reddit", "")
                post.title = post.title.replace("of Reddit", "")
                post.title = post.title.replace("redditors", "")
                post.title = post.title.replace("Redditors", "")
                # print(post.title in self.usedposts,post.title,self.usedposts)
            posts2 = [post for post in posts if post.id not in self.usedposts and not post.stickied] #why not do it with ids instead #TODO
            # shuffle(posts)
            posts = sorted(posts2, key=lambda a: a.score)
            return posts

        def getPosts(self, sub="AskReddit"):
            if sub == "AskMen":
                subreddit = reddit.subreddit("AskMen+AskTeenBoys")
            elif sub == "AskWomen":
                subreddit = reddit.subreddit("AskWomen+AskTeenGirls")
            if sub == "DAE":
                subreddit = reddit.subreddit("DAE+doesanybodyelse")
            else:
                subreddit = reddit.subreddit(sub)
            posts = self.downloadPosts(subreddit)
            self.availablePosts[sub] = self.filterPosts(posts)
            topicLogger.debug(f"found {len(posts)} topics")

        def filterPosts(self, availablePosts):  # TODO TEST FIX if multiple filters filter out the same q, the shit breaks
            # if self.filters["nsfw"]:
            # posts = [i for i in posts if i.score > 25]
            for filt in self.filters.items():
                if not filt[1]:  # filter value
                    for post in availablePosts:
                        for word in self.filterStrings[filt[0]]:  # filter key
                            if word in post.title:
                                topicLogger.debug(f"{word}, {post.title}")
                                availablePosts.remove(post)
                                break
            topicLogger.debug(f"found {len(availablePosts)} good topics")
            return availablePosts

        def submission(self, sub):
            try:
                if len(self.availablePosts[sub]) == 0:
                    self.getPosts(sub)
                    if len(self.availablePosts[sub]) == 0:
                        return None
                    submission = self.submission(sub)
                    return submission
                else:
                    post = self.availablePosts[sub].pop()
                    # posts.remove(post)
                    self.usedposts.append(post.id)
                    self.usedposts = self.usedposts[:500]
                    topicLogger.debug(",".join([str(len(i)) for i in self.availablePosts.values()]) + f" and {len(self.usedposts)}")
                    return post

            except KeyError:
                topicLogger.debug("sub hasnt been initialised yet")
                self.getPosts(sub)
                return self.submission(sub)

        def getPostFromID(self, ID):
            return reddit.submission(ID)

        def basicprint(self, post):  #what was this for?
            pass
            #return embedVar

        def prettyprint(self, post, *attr):
            embedVar = discord.Embed(title=post.title if len(post.title) <= 256 else "\u200b",description=post.title if len(post.title) > 256 else (post.selftext[:min(self.max_comment_length, len(post.selftext))] + ("... " if len(post.selftext) > self.max_comment_length else "")) if (post.selftext and len(post.selftext) <= 1000) else "\u200b",color=attr[0].color if attr else discord.Colour.random())
            embedVar.set_footer(text=f"id: {post.id}" + " |{} | /topic to change topic".format(subemoji[post.subreddit.display_name]) + (" | Low score. Might be stupid?!" if post.score < 100 else " | " + str(post.score) + " points."))
            return embedVar

        def comments(self, post, color=None):  # please dont judge me its so fucked up
            if post is None:
                return discord.Embed(title="?", description="No question in cache.")
            else:
                j = 0  # iterator variable, counts number of valid comments
                toolong = False
                embedVar = discord.Embed(title="What do other people think?",description=post.title + "\n________________\n" + post.selftext[:min(300,len(post.selftext))] + ("... " if len(post.selftext) > 299 else ""),color=color or discord.Color.gold())
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
                        embedVar.add_field(name="{} {} {}agree{}.".format(abs(score), ("person" if abs(score) == 1 else "people"),("dis" if score < 0 else ""), ("s" if score == 1 else "")),value=str(15 * "-") + "\n" + comment.body, inline=False)
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

        def reset(self):
            self.availablePosts = {}


def setup(client, baselogger):
    client.add_cog(TopicCog(client, baselogger))
