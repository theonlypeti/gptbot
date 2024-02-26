import asyncio
import json
import os
import random
import re
from datetime import datetime
from io import BytesIO
from typing import Literal
import emoji
import nextcord as discord
import utils.embedutil
from utils.paginator import Paginator
from nextcord.ext import commands
from utils.antimakkcen import antimakkcen
from utils.getMsgFromLink import getMsgFromLink
import imageio.v3 as iio
import numpy as np
from string import Template
from utils.webhook_manager import WebhookManager

root = os.getcwd()  # "F:\\Program Files\\Python39\\MyScripts\\discordocska\\pipik"


class EmoteCog(commands.Cog):
    def __init__(self, client):
        global logger
        self.discord_emotes = dict()
        self.client = client
        self.emoteserver = None
        logger = client.logger.getChild(f"{self.__module__}")
        self.readEmotes()

    async def flipemote(self, emote, state, orient: Literal["H"] | Literal["V"]):
        if not emote:
            return None
        self.emoteserver: discord.Guild = self.emoteserver or self.client.get_guild(957469186798518282)
        em = discord.PartialEmoji.from_str(emote)
        em = discord.PartialEmoji.with_state(state, name=em.name, animated=em.animated, id=em.id)
        file = await em.to_file()

        # Read the image with imageio
        try:
            img = iio.imread(file.fp, extension="."+file.filename.split(".")[-1])  # TODO sometimes gifs have no transparency so the shape is (x,y,3) then (x,y,4), fix this //still not fixed
        except ValueError as e:
            logger.error(f"ValueError: {e=}")
            return None
        # emotelogger.debug(f"{img.shape=}")

        # Check if the image is animated (i.e., it has more than one frame)
        if len(img.shape) > 3 and img.shape[0] > 1:
            # Handle animated GIF
            flipped_imgs = []
            for frame in img:
                # Flip each frame
                if orient == "H":
                    flipped_img = frame[:, ::-1]
                elif orient == "V":
                    flipped_img = frame[::-1, :]
                flipped_imgs.append(flipped_img)
            # Save all frames to a BytesIO object
            with BytesIO() as image_binary:
                iio.imwrite(image_binary, np.array(flipped_imgs), format="gif", loop=0)
                image_binary.seek(0)
                logger.debug(f"{img.shape=}")
                newemoji = await self.emoteserver.create_custom_emoji(name=f"{em.name}flip{orient}",
                                                                      image=image_binary.read())
        else:
            logger.debug(f"{img.shape=}")
            # Handle static image
            if orient == "H":
                logger.debug(f"{img.shape=}")
                img = img[:, ::-1]
            elif orient == "V":
                img = img[::-1, :]
            with BytesIO() as image_binary:
                iio.imwrite(image_binary, img, format="png")
                logger.debug(f"{img.shape=}")
                image_binary.seek(0)
                newemoji = await self.emoteserver.create_custom_emoji(name=f"{em.name}flip{orient}", image=image_binary.read())

        return newemoji

    def saveEmotes(self):
        with open(root + "/data/pipikemotes.txt", "w") as file:
            json.dump(self.discord_emotes, file, indent=4)
        logger.info("saved emotes")

    def readEmotes(self):
        with open(root + "/data/pipikemotes.txt", "r") as file:
            self.discord_emotes = json.load(file)
        logger.debug(f"loaded {len(self.discord_emotes)} emotes")

    @commands.command()
    async def registerEmote(self, ctx, *attr):
        for emoji in attr:
            self.discord_emotes.update({emoji.split(":")[-2]: emoji})
        self.saveEmotes()

    @commands.command()
    async def unregisterEmote(self, ctx, *attr):
        for emoji in attr:
            del self.discord_emotes[emoji]
        self.saveEmotes()

    @commands.command()
    async def registerAnimatedEmotes(self, ctx, howmany: int):
        howmany = int(howmany)
        for emoji in reversed(ctx.message.guild.emojis):
            if emoji.animated and howmany:
                howmany -= 1
                self.discord_emotes.update({emoji.name: f"<a:{emoji.name}:{emoji.id}>"})
        self.saveEmotes()

    @commands.command()
    async def reloadEmotes(self, ctx):
        self.readEmotes()

    # class ReactSelect(discord.ui.Select):
    #     def __init__(self, message, client, emotes):
    #         self.optionen = []
    #         self.client = client
    #         self.emotes = emotes
    #         self.message = message
    #         for k in ["mood", "pog", "true", "same", "mmshrug", "kekcry", "tiny",
    #                   "peepoheart", "tired", "jerrypanik", "hny", "minor_inconvenience", "hapi", "funkyjam",
    #                   "business", "business2", "tavozz", "concern", "amusing"]: #,
    #                   #"ohgod", "blunder"]:  # populating the select component with options
    #             self.optionen.append(discord.SelectOption(label=k, value=self.emotes[k], emoji=self.emotes[k]))
    #         super().__init__(placeholder="Select an emote", options=self.optionen)
    #
    #     async def callback(self, interaction: discord.Interaction):
    #         emote = self.values[0]
    #
    #         def mycheck(reaction: discord.Reaction, user: discord.User):
    #             return not user.bot and self.message == reaction.message and str(reaction.emoji) == emote
    #
    #         emotelogger.debug(f"{interaction.user} used msg cmd add react with {emote} in {interaction.channel}")
    #         await self.message.add_reaction(emote)
    #         try:
    #             _, _ = await self.client.wait_for('reaction_add', timeout=6.0, check=mycheck)
    #
    #         except asyncio.TimeoutError:
    #             pass
    #         finally:
    #             await self.message.remove_reaction(emote, self.client.user)

    # @discord.message_command(name="Add reaction")
    # async def react(self, interaction, message):
    #     viewObj = discord.ui.View()
    #     viewObj.add_item(self.ReactSelect(message, self.client, self.discord_emotes))
    #     await interaction.send("Don't forget to click the react yourself too! Also spamming emotes might trip up the anti-spam filter.", ephemeral=True, view=viewObj)

    @discord.slash_command(name="emote", description="For using special emotes")  # TODO split these to subcommands, react, send and list? #im kinda happy with this rn
    async def emote(self, ctx: discord.Interaction,
                    emote = discord.SlashOption(name="emoji", #don't typehint this one, will not show the options automatically
                                                     description="An emoji name, leave blank if you want to list them all out.",
                                                     required=False, default=None),  #type: str
                    msg: str = discord.SlashOption(name="message_link",
                                                   description="Use 'copy message link' to specify a message to react to.",
                                                   required=False),
                    text: str = discord.SlashOption(name="text",
                                                    description="The text message to send along with any emotes, use :emotename: as placeholder like regular.",
                                                    required=False, default=None)):
        def check(reaction, user):
            logger.debug(f"{str(reaction.emoji)=}, {emote=}")
            return not user.bot and str(reaction.emoji) == emote

        channel: discord.TextChannel = ctx.channel
        logger.debug(f"{ctx.user}, {emote}, {datetime.now()}")
        if emote:
            if emote.endswith("+flipH"):
                flipped = True
                emotef = await self.flipemote(self.discord_emotes.get(emote.removesuffix("+flipH")), ctx.guild.me._state,orient="H")
            elif emote.endswith("+flipV"):
                flipped = True
                emotef = await self.flipemote(self.discord_emotes.get(emote.removesuffix("+flipV")), ctx.guild.me._state,orient="V")
            else:
                flipped = False
                emotef = self.discord_emotes.get(emote)
            if not emotef:
                await utils.embedutil.error(ctx, f"Emote {emote.split('+')[0]} not found")
                return
            emote = emotef
            if msg:
                await ctx.response.defer(ephemeral=True)
                mess = await getMsgFromLink(self.client, msg)
                await mess.add_reaction(emote)
                await ctx.send("Now go react on the message", ephemeral=True)
                try:
                    _, _ = await self.client.wait_for('reaction_add', timeout=6.0, check=check)
                except asyncio.TimeoutError:
                    logger.debug("emote timed out")
                finally:
                    await mess.remove_reaction(emote, self.client.user)

            else:
                try:
                    await ctx.response.defer(ephemeral=True)
                    async with WebhookManager(ctx, channel) as wh:
                        await wh.send(content=emote, username=ctx.user.display_name, avatar_url=ctx.user.avatar.url)
                except discord.errors.Forbidden:
                    await ctx.send(emote)
            if flipped:
                await asyncio.sleep(2)
                await self.emoteserver.delete_emoji(emote)

        elif text:
            await ctx.response.defer(ephemeral=True)
            try:
                flips = [m.start() for m in re.finditer('\+flipH', text)] #ends of emotes
                emotestoflip = [(text.rfind("{",0,i),i) for i in flips] #beginnings of toflip emotes
                emotestoflip = set([text[i[0]+1:i[1]] for i in emotestoflip]) #capturing their names from begin:end ranges, also making a set
                logger.debug(msg=",".join(map(str, emotestoflip)))
                flippedemotes = [await self.flipemote(self.discord_emotes[emotetoflip], ctx.guild.me._state, orient="H") for emotetoflip in emotestoflip] #flipping, adding to server
                self.discord_emotes.update({f"{i}+flipH": j for i, j in zip(emotestoflip, flippedemotes)}) #update the translation dict temporarily

                flips = [m.start() for m in re.finditer('\+flipV', text)]  # ends of emotes
                emotestoflipv = [(text.rfind("{", 0, i), i) for i in flips]  # beginnings of toflip emotes
                emotestoflipv = set([text[i[0] + 1:i[1]] for i in emotestoflipv])  # capturing their names from begin:end ranges, also making a set
                logger.debug(msg=",".join(map(str, emotestoflipv)))
                flippedemotesv = [await self.flipemote(self.discord_emotes[emotetoflip], ctx.guild.me._state, orient="V") for emotetoflip in emotestoflipv]  # flipping, adding to server
                self.discord_emotes.update({f"{i}+flipV": j for i, j in zip(emotestoflipv, flippedemotesv)})

                # #emotelogger.debug(self.discord_emotes)
                # text = text.replace("{", "{self.discord_emotes['")
                # text = text.replace("}", "']}")
                # text = eval(f'f"{text}"')  #this is apparently a security risk, it requires a malicious string to be in the discord_emotes dict, but still
                class MyTemplate(Template):
                    delimiter = ':'
                    pattern = r"""
                    \:                       # Escape and start delimiter
                    (?:
                      (?P<escaped>\:) |      # Escape sequence of two delimiters
                      (?P<named>[_a-z][_a-z0-9]*)\b     # delimiter and a Python identifier
                      (?:
                        \:                   # Unescaped delimiter
                        (?:
                          (?P<braced>[_a-z][_a-z0-9]*)\b |   # Braced identifier
                          (?P<invalid>)              # Other ill-formed delimiter exprs
                        )
                      )?
                    )
                    """

                template = MyTemplate(text)
                text = template.safe_substitute(self.discord_emotes)

                if msg:
                    mess: discord.PartialMessage = await getMsgFromLink(self.client, msg)
                    await mess.reply(f"{ctx.user.display_name} says:\n{text}")
                    # await ctx.send(f"Hi, {ctx.user.display_name} wanted to tell you something..", delete_after=5)
                    await ctx.send(f"Done", delete_after=5)
                else:
                    async with WebhookManager(ctx, channel) as wh:
                        await wh.send(content=f"{text}", username=ctx.user.display_name, avatar_url=ctx.user.avatar.url)
                for i in flippedemotes + flippedemotesv:
                    await self.emoteserver.delete_emoji(i)
                for i in emotestoflip:
                    del self.discord_emotes[f"{i}+flipH"]
                for i in emotestoflipv:
                    del self.discord_emotes[f"{i}+flipV"]

            except Exception as e:
                logger.error(e)
                await ctx.send(str(e), ephemeral=True)
                raise e

        elif not emote:
            emotestr = ";".join([f"{v} {k}" for k, v in self.discord_emotes.items()])
            splitat = 0
            embeds = []
            if emotestr:
                while True:
                    prevslice = splitat
                    splitat = emotestr.rfind(";", prevslice, prevslice+4096)
                    embeds.append(discord.Embed(title="Emotes", description=emotestr[prevslice:splitat], color=ctx.user.color))

                    # if len(emotestr) > 4096:
                    #     for i in range(splitat, len(emotestr), 1024): #TODO do splitat here too
                    #         embedVar.add_field(name=i, value=emotestr[i:min(i + 1024, len(emotestr))]) #or rpratition()
                    #embedVar.set_footer(text=f"{len(emotestr)} / 6000 chars in one message")

                    if len(emotestr) - splitat <= 4096:
                        embeds.append(discord.Embed(title="Emotes", description=emotestr[splitat:len(emotestr)], color=ctx.user.color))
                        break
                [embed.set_footer(text=f"page {n}/{len(embeds)}") for n, embed in enumerate(embeds, start=1)]

                pagi = Paginator(func=lambda pagin: embeds[pagin.page], select=None, inv=embeds, itemsOnPage=1)
                await pagi.render(ctx, ephemeral=True)
                # await ctx.send(embeds=embeds, ephemeral=True)
            return
        else:
            await ctx.send("What")

    @emote.on_autocomplete("emote")
    async def emote_autocomplete(self, interaction, emote: str):
        if not emote:
            # send the full autocomplete list
            randomemotes = list(self.discord_emotes.keys())
            random.shuffle(randomemotes)
            await interaction.response.send_autocomplete(randomemotes[:25])
            return
        # send a list of nearest matches from the list of emotes
        get_near_emote = [i for i in self.discord_emotes.keys() if i.casefold().startswith(emote.casefold())]
        get_near_emote = get_near_emote[:25]
        if len(get_near_emote) == 1:
            get_near_emote.append(get_near_emote[0] + "+flipH")
            get_near_emote.append(get_near_emote[0] + "+flipV")
        await interaction.response.send_autocomplete(get_near_emote)

    @emote.on_autocomplete("text")  # does not really work
    async def emotetext_autocomplete(self, interaction, text: str):
        if not text:
            return None
        text = text.rpartition(":")
        emote = text[2]
        if emote:
            get_near_emote = [text[0]+text[1]+i+":" for i in self.discord_emotes.keys() if i.casefold().startswith(emote.casefold())]
            get_near_emote = get_near_emote[:25]
            await interaction.response.send_autocomplete(get_near_emote)

    class AddReactLettersModal(discord.ui.Modal):
        def __init__(self, message: discord.Message):
            self.message = message
            super().__init__(title="Type a word to spell out with reacts.")
            self.word = discord.ui.TextInput(label="Word")
            self.add_item(self.word)

        async def callback(self, interaction):
            word = ""
            logger.info(f"{interaction.user} word-reacts {self.word.value} on message {self.message.content}")
            myword = antimakkcen(self.word.value)
            for letter in myword.upper():
                if letter == "A" and chr(127397 + ord("A")) in word:
                    word += chr(127344)
                elif letter == "B" and chr(127397 + ord("B")) in word:
                    word += chr(127345)
                elif letter == "I" and chr(127397 + ord("I")) in word:
                    word += chr(8505)
                elif letter == "M" and chr(127397 + ord("M")) in word:
                    word += chr(9410)
                elif letter == "O" and chr(127397 + ord("O")) in word:
                    word += chr(127358)
                elif letter == "P" and chr(127397 + ord("P")) in word:
                    word += chr(127359)
                elif letter == " ":
                    word += emoji.emojize(":blue_square:")
                elif letter == "?":
                    word += emoji.emojize(":white_question_mark:")# emoji.emojize(":red_question_mark:")
                elif letter == "!":
                    word += emoji.emojize(":white_exclamation_mark:") #emoji.emojize(":red_exclamation_mark:")
                else:
                    word += chr(127397 + ord(letter.upper()))
            word = list(dict.fromkeys(antimakkcen(word))) #what the hell is this doing is this just a set() but with extra steps? ACTUALLY YES set is unordered, dict is ordered!!!!
            if len(word) != len(myword):
                await interaction.send("Word has duplicate letter, can't make out the whole word", ephemeral=True)
            else:
                await interaction.send("Working on it...", ephemeral=True)

            for letter in word:
                await self.message.add_reaction(letter)

    @discord.message_command(name="Word react")
    async def wordreact(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(self.AddReactLettersModal(message))


def setup(client):
    client.add_cog(EmoteCog(client))
