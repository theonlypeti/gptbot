import asyncio
import json
import logging
import os
import random
import re
from datetime import datetime
from io import BytesIO
from typing import Literal
import nextcord as discord
from PIL import Image
from nextcord.ext import commands
from utils.antimakkcen import antimakkcen
from utils.getMsgFromLink import getMsgFromLink

root = os.getcwd()  # "F:\\Program Files\\Python39\\MyScripts\\discordocska\\pipik"


class EmoteCog(commands.Cog):
    def __init__(self, client, baselogger):
        self.discord_emotes = dict()
        self.client = client
        self.emoteserver = None
        self.emotelogger = baselogger.getChild("EmoteLogger")
        self.readEmotes()

    async def flipemote(self, emote, state, orient: Literal["H"] | Literal["V"]):
        self.emoteserver: discord.Guild = self.emoteserver or self.client.get_guild(957469186798518282)
        em = discord.PartialEmoji.from_str(emote)
        em = discord.PartialEmoji.with_state(state, name=em.name, animated=em.animated, id=em.id)
        file = await em.to_file()
        img = Image.open(file.fp)  # invalid start byte if em.read
        if orient == "H":
            img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        elif orient == "V":
            img = img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        with BytesIO() as image_binary:
            img.save(image_binary, format="gif" if em.animated else "png")
            image_binary.seek(0)
            newemoji = await self.emoteserver.create_custom_emoji(name=f"{em.name}flip{orient}", image=image_binary.read())
        return newemoji

    def saveEmotes(self):
        with open(root + "/data/pipikemotes.txt", "w") as file:
            json.dump(self.discord_emotes, file, indent=4)
        self.emotelogger.info("saved emotes")

    def readEmotes(self):
        with open(root + "/data/pipikemotes.txt", "r") as file:
            self.discord_emotes = json.load(file)
        self.emotelogger.debug(f"loaded {len(self.discord_emotes)} emotes")

    @commands.command()
    async def registerEmote(self, ctx, *attr):
        for emoji in attr:
            self.discord_emotes.update({emoji.split(":")[-2]: emoji})
        self.saveEmotes()

    @commands.command()
    async def registerAnimatedEmotes(self, ctx, howmany):
        howmany = int(howmany)
        for emoji in reversed(ctx.message.guild.emojis):
            if emoji.animated and howmany:
                howmany -= 1
                self.discord_emotes.update({emoji.name: f"<a:{emoji.name}:{emoji.id}>"})
        self.saveEmotes()

    @commands.command()
    async def reloadEmotes(self, ctx):
        self.readEmotes()

    class ReactSelect(discord.ui.Select):
        def __init__(self, message, client, emotes):
            self.optionen = []
            self.client = client
            self.emotes = emotes
            self.message = message
            for k in ["same", "mood", "true", "kekw", "kekno", "kekfu", "kekwait", "kekcry", "kekdoubt", "tiny",
                      "peepoheart", "tired", "jerrypanik", "hny", "minor_inconvenience", "doggo", "funkyjam",
                      "business", "business2", "tavozz", "concern", "amusing", "ofuk",
                      "ohgod"]:  # populating the select component with options
                self.optionen.append(discord.SelectOption(label=k, value=self.emotes[k], emoji=self.emotes[k]))
            super().__init__(placeholder="Select an emote", options=self.optionen)

        async def callback(self, interaction):
            def check(reaction, user):
                return not user.bot

            await self.message.add_reaction(self.values[0])
            _, _ = await self.client.wait_for('reaction_add', timeout=6.0, check=check) #reaction, user
            await self.message.remove_reaction(self.values[0], self.client.user)

    @discord.message_command(name="Add reaction")
    async def react(self, interaction, message):
        viewObj = discord.ui.View()
        viewObj.add_item(self.ReactSelect(message, self.client, self.discord_emotes))
        await interaction.send("Dont forget to click the react yourself too! Also spamming emotes might trip up the anti-spam filter.",ephemeral=True, view=viewObj)

    @discord.slash_command(name="emote", description="For using special emotes") #TODO split these to subcommands, react, send and list? #im kinda happy with this rn
    async def emote(self, ctx: discord.Interaction,
                    emote: str = discord.SlashOption(name="emoji",
                                                     description="An emoji name, leave blank if you want to list them all out.",
                                                     required=False, default=None),
                    msg: str = discord.SlashOption(name="message_link",
                                                   description="Use 'copy message link' to specify a message to react to.",
                                                   required=False),
                    text: str = discord.SlashOption(name="text",
                                                    description="The text message to send along with any emotes, use {emotename} as placeholder.",
                                                    required=False, default=None)):
        def check(reaction, user):
            return not user.bot and (str(reaction.emoji) in list(self.discord_emotes.values()))

        self.emotelogger.debug(f"{ctx.user}, {emote}, {datetime.now()}")
        if emote:
            if emote.endswith("+flipH"):
                flipped = True
                emote = await self.flipemote(self.discord_emotes[emote.removesuffix("+flipH")], ctx.guild.me._state,orient="H")
            elif emote.endswith("+flipV"):
                flipped = True
                emote = await self.flipemote(self.discord_emotes[emote.removesuffix("+flipV")], ctx.guild.me._state,orient="V")
            else:
                flipped = False
                emote = self.discord_emotes[emote]
            if msg:
                #await ctx.response.defer() nono because i wont be able to ephemeral
                mess = await getMsgFromLink(self.client, msg)
                await mess.add_reaction(emote)
                await ctx.send("Now go react on the message", ephemeral=True)
                try:
                    _, _ = await self.client.wait_for('reaction_add', timeout=6.0, check=check)
                except asyncio.TimeoutError:
                    self.emotelogger.debug("emote timed out")
                finally:
                    await mess.remove_reaction(emote, self.client.user)

            else:
                await ctx.response.defer()
                await ctx.send(emote)
            if flipped:
                await self.emoteserver.delete_emoji(emote)

        elif text:
            await ctx.response.defer()
            try:
                flips = [m.start() for m in re.finditer('\+flipH', text)] #ends of emotes
                emotestoflip = [(text.rfind("{",0,i),i) for i in flips] #beginnings of toflip emotes
                emotestoflip = set([text[i[0]+1:i[1]] for i in emotestoflip]) #capturing their names from begin:end ranges, also making a set
                self.emotelogger.debug(msg=",".join(map(str, emotestoflip)))
                flippedemotes = [await self.flipemote(self.discord_emotes[emotetoflip], ctx.guild.me._state, orient="H") for emotetoflip in emotestoflip] #flipping, adding to server
                self.discord_emotes.update({f"{i}+flipH": j for i, j in zip(emotestoflip, flippedemotes)}) #update the translation dict temporarily

                flips = [m.start() for m in re.finditer('\+flipV', text)]  # ends of emotes
                emotestoflipv = [(text.rfind("{", 0, i), i) for i in flips]  # beginnings of toflip emotes
                emotestoflipv = set([text[i[0] + 1:i[1]] for i in emotestoflipv])  # capturing their names from begin:end ranges, also making a set
                self.emotelogger.debug(msg=",".join(map(str, emotestoflipv)))
                flippedemotesv = [await self.flipemote(self.discord_emotes[emotetoflip], ctx.guild.me._state, orient="V") for emotetoflip in emotestoflipv]  # flipping, adding to server
                self.discord_emotes.update({f"{i}+flipV": j for i, j in zip(emotestoflipv, flippedemotesv)})

                #self.emotelogger.debug(self.discord_emotes)
                text = text.replace("{", "{self.discord_emotes['")
                text = text.replace("}", "']}")
                text = eval(f'f"{text}"')
                if msg:
                    mess: discord.PartialMessage = await getMsgFromLink(self.client, msg)
                    await mess.reply(text)
                    await ctx.send(f"Hi, {ctx.user.display_name} wanted to tell you something..", delete_after=5)
                else:
                    await ctx.send(f"{text}")
                for i in flippedemotes + flippedemotesv:
                    await self.emoteserver.delete_emoji(i)
                for i in emotestoflip:
                    del self.discord_emotes[f"{i}+flipH"]
                for i in emotestoflipv:
                    del self.discord_emotes[f"{i}+flipV"]

            except Exception as e:
                self.emotelogger.error(e)
                await ctx.send(e, ephemeral=True)
                raise e

        elif not emote:
            emotestr = ";".join([f"{v} {k}" for k, v in self.discord_emotes.items()])
            if emotestr:
                splitat = emotestr.rfind(";", 0, 4096)
                embedVar = discord.Embed(title="Emotes", description=emotestr[:splitat], color=ctx.user.color)
                if len(emotestr) > 4096:
                    for i in range(splitat, len(emotestr), 1024): #TODO do splitat here too
                        embedVar.add_field(name=i, value=emotestr[i:min(i + 1024, len(emotestr))]) #or rpratition()
                embedVar.set_footer(text=f"{len(emotestr)} / 6000 chars in one message")
                await ctx.send(embed=embedVar, ephemeral=True)
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

    @emote.on_autocomplete("text") #does not really work
    async def emote_autocomplete(self, interaction, text: str):
        if not text:
            return None
        text = text.rpartition("{")
        emote = text[2]
        if emote:
            get_near_emote = [text[0]+text[1]+i+"}" for i in self.discord_emotes.keys() if i.casefold().startswith(emote.casefold())]
            get_near_emote = get_near_emote[:25]
            #self.emotelogger.debug(get_near_emote)
            await interaction.response.send_autocomplete(get_near_emote)

    class FancyLinkModal(discord.ui.Modal):
        def __init__(self, mode):
            super().__init__(title="Custom link")
            self.mode = mode
            self.link = discord.ui.TextInput(label="Link", placeholder="https://example.com")
            self.displaytext = discord.ui.TextInput(label="Link display text", placeholder="Click me")
            self.hovertext = discord.ui.TextInput(label="Link hover text", placeholder="opens in new page", required=False)
            self.context = discord.ui.TextInput(label="Surrounding text (use {} as link placeholder)", placeholder="Please head to {} link", required=False, style=discord.TextInputStyle.paragraph)

            for item in (self.link, self.displaytext, self.hovertext, self.context):
                self.add_item(item)

        async def callback(self, interaction: discord.Interaction):
            if self.hovertext.value:
                custom = f"[__{self.displaytext.value}__]({self.link.value}\n" + '"{}"'.format(self.hovertext.value) + ")"
            else:
                custom = f"[__{self.displaytext.value}__]({self.link.value})"
            await interaction.send(self.context.value.format(custom) if "{}" in self.context.value else self.context.value + custom if self.context.value else custom)

    @discord.slash_command(name="makelink")
    async def makelink(self, interaction: discord.Interaction, mode: Literal["Simple", "Complex"]):
        if mode == "Simple":
            await interaction.response.send_modal(self.FancyLinkModal(mode=mode))
        else:
            await interaction.send("WIP lol")

    class AddReactLettersModal(discord.ui.Modal):
        def __init__(self, message: discord.Message, logger: logging.Logger):
            self.message = message
            self.logger = logger
            super().__init__(title="Type a word to spell out with reacts.")
            self.word = discord.ui.TextInput(label="Word")
            self.add_item(self.word)

        async def callback(self, interaction):
            word = ""
            self.logger.info(f"{interaction.user} word-reacts {self.word.value} on message {self.message.content}")
            myword = antimakkcen(self.word.value)
            for letter in myword.upper():
                if letter == "A" and chr(127397 + ord("A")) in word:
                    word += chr(127344)
                elif letter == "B" and chr(127397 + ord("B")) in word:
                    word += chr(127345)
                if letter == "I" and chr(127397 + ord("I")) in word:
                    word += chr(8505)
                if letter == "M" and chr(127397 + ord("M")) in word:
                    word += chr(9410)
                elif letter == "O" and chr(127397 + ord("O")) in word:
                    word += chr(127358)
                else:
                    word += chr(127397 + ord(letter.upper()))
            word = list(dict.fromkeys(antimakkcen(word))) #what the hell is this doing
            if len(word) != len(myword):
                await interaction.send("Word has duplicate letter, can't make out the whole word", ephemeral=True)
            else:
                await interaction.send("On it...", ephemeral=True)

            for letter in word:
                await self.message.add_reaction(letter)

    @discord.message_command(name="Word react")
    async def reacts(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(self.AddReactLettersModal(message, self.emotelogger))

def setup(client, baselogger):
    client.add_cog(EmoteCog(client, baselogger))
