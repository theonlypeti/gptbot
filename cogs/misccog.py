import os
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
from textwrap import TextWrapper
from typing import Optional, Literal
import emoji
import nextcord as discord
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from nextcord import Interaction
from numpy import clip
# from pipikNextcord import root #  dont freaking do this, causes to rerun the main file
from pycaw.utils import AudioUtilities
from utils import embedutil, antimakkcen
from utils.bf import bf
from nextcord.ext import commands

stunlocked = None


class MiscallenousCog(commands.Cog):
    def __init__(self, client):
        global logger
        logger = client.logger.getChild(f"{__name__}Logger")
        self.client = client
        with open(r"data/karomkodasok.txt", "r", encoding="UTF-8") as file:
            self.karomkodasok = file.readlines()
        logger.debug(f"{len(self.karomkodasok)} bad words loaded.")

        self.T9 = {key * i: letter for i, key, letter in
                    zip([(num % 3) + 1 for num in range(0, 26)], [str(q // 3) for q in range(6, 30)],
                        sorted(set(string.ascii_uppercase) - {"S", "Z"}))} | {"7777": "S", "9999": "Z", "0": " "}
        self.T9rev = {v: k for k, v in self.T9.items()}

    @discord.user_command(name="Karomkodas")
    async def karmokdoas(self, interaction: discord.Interaction, user: discord.User):
        # await interaction.response.defer() #if deferred, the tts doesn't work
        csunya = " ".join(random.choice(self.karomkodasok).strip().lower() for _ in range(5))
        await interaction.send(content=f"{user.mention} te {csunya}!", tts=True)

    class CaesarModal(discord.ui.Modal):
        def __init__(self, title):
            super().__init__(title=title)
            self.inputtext = discord.ui.TextInput(label="Input the text", style=discord.TextInputStyle.paragraph)
            self.add_item(self.inputtext)

        async def callback(self, ctx):
            text = antimakkcen.antimakkcen(self.inputtext.value)
            textik = ("".join([chr(((ord(letter) - 97 + 13) % 26) + 97) if letter.isalpha() and letter.islower() else chr(
                ((ord(letter) - 65 + 13) % 26) + 65) if letter.isalpha() and letter.isupper() else letter for letter in text]))
            embedVar = discord.Embed(title="Message", type="rich", description=textik)
            embedutil.setuser(embedVar, ctx.user)
            await ctx.send(embed=embedVar)

    @discord.slash_command(description="Encrypt/Decrypt", name="caesar")
    async def caesar_modal(self, ctx: discord.Interaction):
        modal = self.CaesarModal(title="ROT13 cypher")
        await ctx.response.send_modal(modal)

    class BfModal(discord.ui.Modal):
        def __init__(self, title):
            super().__init__(title=title)
            self.codetext = discord.ui.TextInput(label="Input the code", style=discord.TextInputStyle.paragraph,
                                                 default_value="+[-->-[>>+>-----<<]<--<---]>-.>>>+.>>..+++[.>]<<<<.+++.------.<<-.>>>>+.")
            self.add_item(self.codetext)

            self.inputtext = discord.ui.TextInput(label="input from user (if any)", required=False, style=discord.TextInputStyle.paragraph, placeholder="123")
            self.add_item(self.inputtext)

        async def callback(self, ctx):
            output = bf(self.codetext.value, self.inputtext.value)
            embedVar = discord.Embed(title="Brainfuck code output", type="rich", description=output)
            embedVar.set_author(name=ctx.user.display_name, icon_url=ctx.user.avatar.url)
            await ctx.send(embed=embedVar)

    @discord.slash_command(description="Brainfuck interpreter", name="brainfuck")
    async def bf_modal(self, ctx: discord.Interaction):
        modal = self.BfModal(title="Brainfuck")
        await ctx.response.send_modal(modal)

    @discord.slash_command(description="Yes or no", name="yesorno")
    async def yesorno(self, ctx: discord.Interaction, question: Optional[str]):
        if not question:
            await ctx.send(
                "https://cdn.discordapp.com/attachments/607897146750140457/1040242560964251678/3d-yes-or-no-little-man-drawings_csp19386099.jpg")
        else:
            img = Image.open(r"data/yesorno.jpeg")
            d = ImageDraw.Draw(img)
            textsize = img.width * (1 / (len(question)))
            textsize = int(np.clip(textsize, 25, 60))
            fnt = ImageFont.truetype('impact.ttf', size=textsize)

            newquestion = ""
            for i in range(0, len(question), 38):
                newquestion += question[i:i + 38] + "\n"

            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100, "fill": (255, 255, 255), "anchor": "mm"}
            d.multiline_text((img.width / 2, textsize + (textsize * len(question) // 38)), newquestion, **textconfig)
            with BytesIO() as image_binary:
                img.save(image_binary, "jpeg")
                image_binary.seek(0)
                await ctx.send(file=discord.File(fp=image_binary, filename=f'yesorno.jpeg'))
        mesage = await ctx.original_message()
        await mesage.add_reaction("<:yes:1040243872095281152>")
        await mesage.add_reaction("<:no:1040243824489943040>")

    # @commands.has_permissions(manage_server=True) #that wont work
    @discord.slash_command(name="pfp", description="chooses a random emote for the servers profile pic.", guild_ids=[860527626100015154, 552498097528242197], dm_permission=False)
    async def pfp(self, interaction: discord.Interaction):
        os.chdir("D:\\Users\\Peti.B\\Pictures\\microsoft\\emotes")
        emotes = [emote for emote in os.listdir() if not emote.endswith(".gif") or interaction.guild.premium_tier]
        await interaction.send(f"Picking from {len(emotes)} emotes...")
        img = random.choice(emotes)
        logger.info(f"Changing pfp to {img} in {interaction.guild.name} on behalf of {interaction.user.name}")
        with open(img, "rb") as file:
            await interaction.guild.edit(icon=file.read())
        os.chdir(interaction.client.root)

    @discord.slash_command(name="ticho", description="Uber hlasitost", guild_ids=(860527626100015154,))
    async def ticho(self, ctx: discord.Interaction, message: Optional[str]):
        ogname = ctx.guild.me.display_name
        await ctx.guild.me.edit(nick=ctx.user.name)
        for session in AudioUtilities.GetAllSessions():
            if session.Process and session.Process.name() in ("chrome.exe", "JetAudio.exe"):
                session.SimpleAudioVolume.SetMasterVolume(session.SimpleAudioVolume.GetMasterVolume() / 3, None)
        await ctx.send(content=message or "Tíško si poprosím", tts=True)
        await ctx.guild.me.edit(nick=ogname)

    @discord.slash_command(name="time", description="/time help for more info")
    async def time(self, ctx,
                   time: str = discord.SlashOption(name="time",
                                                   description="Y.m.d H:M or just parts of them, or relative (minutes=30 etc...)"),
                   arg: str = discord.SlashOption(name="format", description="raw = copypasteable, full = not relative",
                                                  required=False, choices=["raw", "full", "raw+full"], default=""),
                   message: str = discord.SlashOption(name="message",
                                                      description="Your message to insert the timestamp into, use {} as a placeholder",
                                                      required=False)):
        now = datetime.now()
        try:
            if "." in time and ":" in time:  # if date and time is given
                try:
                    timestr = datetime.strptime(time, "%Y.%m.%d %H:%M")
                except ValueError:
                    timestr = datetime.strptime(time, "%m.%d %H:%M")
                    timestr = timestr.replace(year=now.year)
                    if timestr < now:
                        timestr = timestr.replace(year=now.year + 1)
            elif "H:M" in time:
                await ctx.send("Nono, you need to input actual TIME in there not the string H:M")
                return
            elif "." in time: #only date
                try:
                    timestr = datetime.strptime(time, "%Y.%m.%d")
                except ValueError:
                    timestr = datetime.strptime(time, "%m.%d")
                    timestr = timestr.replace(year=now.year)
                    if timestr < now:
                        timestr = timestr.replace(year=now.year + 1)
            elif ":" in time:  # if only time is given
                timestr = now.replace(**{"hour": int(time.split(":")[0]), "minute": int(time.split(":")[1]), "second": 0})  # i could have done strptime %H:%M but it would have given me a 1970 date
            elif "=" in time:  # if relative
                timestr = now + timedelta(**{k.strip(): int(v.strip()) for k, v in [i.split("=") for i in time.split(",")]})
            else:  # if no time is given
                embedVar = discord.Embed(title="Timestamper", description="Usage examples", color=ctx.user.color)
                embedVar.add_field(name="/time 12:34", value="Today´s date with time given")
                embedVar.add_field(name="/time 2022.12.31 12:34", value="Full date format")
                embedVar.add_field(name="/time hours=1,minutes=30", value="Relative to current time")
                embedVar.add_field(name="optional arg: raw/full/raw+full",
                                   value="raw= Copy pasteable timestamp\nfull= Written out date instead of relative time")
                embedVar.add_field(name="optional message:", value="Brb {}; Meeting starts at {} be there!")
                await ctx.send(embed=embedVar)
                return
            style = 'F' if "full" in arg else 'R'
            israw = "raw" in arg
            logger.debug(f"{ctx.user} used /time as {time} for {timestr}")
            mention = f"{'`' if israw else ''}{discord.utils.format_dt(timestr, style=style)}{'`' if israw else ''}"
            await ctx.send(message.format(
                mention) if message and "{}" in message else f"{message} {mention}" if message else mention)
        except Exception as e:
            await ctx.send(e)
            raise e

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
                custom = f"\u200b[__{self.displaytext.value}__]({self.link.value}\n" + '"{}"'.format(self.hovertext.value) + ")"
            else:
                custom = f"\u200b[__{self.displaytext.value}__]({self.link.value})"
            await interaction.send(self.context.value.format(custom) if "{}" in self.context.value else self.context.value + custom if self.context.value else custom)

    @discord.slash_command(name="makelink")
    async def makelink(self, interaction: discord.Interaction, mode: Literal["Simple", "Complex"]):
        if mode == "Simple":
            await interaction.response.send_modal(self.FancyLinkModal(mode=mode))
        else:
            await interaction.send("WIP lol") #TODO
    # buttons to add colored text -> dropdown for color + rainbow -> modal to inpu
    # button for link, if added disable copying, only send to channel //actually probably works now
    # add select for components if add newline or not //what?
    # add time modal maybe with multi parse but idk how to do full or relative
    # add fancytext unicode shit (honestly idk what you mean like smalltext and like fancy font?)

    async def randomcase(self, interaction: discord.Interaction, message: discord.Message):
        """Spongebob mocking"""
        assert message.content
        await message.reply("".join(random.choice([betu.casefold(), betu.upper()]) for betu in message.content) + " <:pepeclown:803763139006693416>")

    async def shout(self, interaction: discord.Interaction, message: discord.Message):
        """Louder for the ppl in the back"""
        assert message.content
        await message.reply("# " + message.content)

    async def t9(self, interaction: discord.Interaction, message: discord.Message):
        if message.content.replace(" ", "").isnumeric():
            await message.reply("".join([self.T9[numbers] for numbers in message.content.split(" ")]))
        else:
            await message.reply(" ".join([self.T9rev[letter.upper()] for letter in antimakkcen.antimakkcen(message.content)]))

    async def caesarcmd(self, interaction: discord.Interaction, message: discord.Message):
        """Caesar (de)cypher"""
        text = antimakkcen.antimakkcen(message.content)
        textik = ("".join([chr(((ord(letter) - 97 + 13) % 26) + 97) if letter.isalpha() and letter.islower() else chr(
            ((ord(letter) - 65 + 13) % 26) + 65) if letter.isalpha() and letter.isupper() else letter for letter in
                           text]))
        await message.reply(textik)

    async def unemojize(self, interaction, message):
        await interaction.send(f"`{emoji.demojize(message.content)}`", ephemeral=True)

    class MiscMessageSelector(discord.ui.Select):
        def __init__(self, cog, message: discord.Message):
            super().__init__()
            self.cog: MiscallenousCog = cog
            self.message = message
            self.cmds = [self.cog.randomcase, self.cog.caesarcmd, self.cog.t9, self.cog.shout, self.cog.unemojize]
            cmd = self.cmds[0]

            self.options = [discord.SelectOption(label=cmd.__doc__ or cmd.__name__.capitalize(), value=i) for i, cmd in enumerate(self.cmds)]

        async def callback(self, interaction: Interaction) -> None:
            cmd = self.cmds[int(self.values[0])]
            await cmd(interaction, self.message)

    @discord.message_command(name="Message manipulation")
    async def misc_msg_cmnds(self, interaction: discord.Interaction, message: discord.Message):
        assert message.content
        viewObj = discord.ui.View()
        viewObj.add_item(self.MiscMessageSelector(self, message))
        await interaction.send(view=viewObj, ephemeral=True)

    class RatioModal(discord.ui.Modal):
        def __init__(self, message: discord.Message):
            super().__init__(title="Fact check")
            self.message = message
            self.fact = discord.ui.TextInput(label="Fact check their message", required=True)
            self.add_item(self.fact)

        async def callback(self, interaction: Interaction) -> None:
            txt = self.fact.value
            img = Image.open(r"data/ratio.png")
            d = ImageDraw.Draw(img)
            # textsize = img.width * (1 / (len(txt)))
            # textsize = int(clip(textsize, 25, 25))
            textsize = 20
            fnt = ImageFont.truetype(r'C:\Users\booth\AppData\Local\Microsoft\Windows\Fonts\Roboto-Regular.ttf', size=textsize)

            txt = "\n".join([text for text in TextWrapper(width=80, break_long_words=False, replace_whitespace=False).wrap(txt)])

            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": 1,
                          "fill": (255, 255, 255), "anchor": "ls"}
            d.multiline_text((40, 90), txt, **textconfig)
            with BytesIO() as image_binary:
                img.save(image_binary, "png")
                image_binary.seek(0)
                await self.message.reply(file=discord.File(fp=image_binary, filename=f'ratio.png'))

    @discord.message_command(name="Twitter fact check")
    async def ratio(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(self.RatioModal(message))

    @discord.user_command(name="FbAnna profilka", force_global=True)
    async def flowersprofilka(self, interaction: discord.Interaction, user: discord.User):
        flowerdir = r"D:\Users\Peti.B\Pictures\viragok"
        await interaction.response.defer()
        with BytesIO() as image:
            await user.display_avatar.save(image)
            img = Image.open(image)
            mappak = os.listdir(flowerdir)
            for i in range(56):
                mappa = flowerdir + "\\" +random.choice(mappak)
                virag = mappa + "\\" + random.choice(os.listdir(mappa))
                with open(virag, "rb") as file:
                    virag = Image.open(file)
                    size = img.width // 8
                    virag.thumbnail((size, size))
                    img.paste(virag, (random.choice([i for i in range(-size // 3, int(img.width - (size * 1))) if i not in range(size * 1, img.width - size * 3)]), random.randint(0, img.height - size * 2)), virag)

            for i in range(24):
                mappa = fr"{flowerdir}\{random.choice(mappak)}"
                virag = fr"{mappa}\{random.choice(os.listdir(mappa))}"
                with open(virag, "rb") as file:
                    virag = Image.open(file)
                    size = img.width // 8
                    virag.thumbnail((size, size))
                    img.paste(virag, (random.randint(0, img.width), random.randint(img.height - size * 2, img.height - size)), virag)

            d = ImageDraw.Draw(img)
            fnt = ImageFont.truetype('FREESCPT.TTF', size=size)

            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100,
                          "fill": (255, 255, 255), "anchor": "mm"}

            # szoveg = random.choice(("Jó éjszakát mindenkinek", "Kellemes ünnepeket", "Áldott hétvégét kívánok", "Meghalt a Jóska xd"))
            szoveg = random.choice(("Dobrú noc vám prajem!", "Pozehnaný víkend vám prajem!", "Kávicka pohodicka", "Príjemné popoludnie prajem!"))
            d.multiline_text((img.width / 2, img.height - size), szoveg, **textconfig)

        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await interaction.send(file=discord.File(image_binary, "flowers.PNG"))

    @discord.user_command(name="Stunlock", guild_ids=(601381789096738863,))
    async def stunlock(self, interaction: discord.Interaction, user: discord.User):
        global stunlocked
        if stunlocked == user:
            stunlocked = None
        else:
            stunlocked = user
        await interaction.send(f"Stunlokced {stunlocked}", ephemeral=True)

    # @client.slash_command(name="banboci", description="Timeout boci mindkét accját.",guild_ids=(601381789096738863,), dm_permission=False)
    # async def banboci(interaction: discord.Interaction, minutes: float, reason: str):
    #     boci1: discord.Member = interaction.guild.get_member(569937005463601152)
    #     await boci1.timeout(timeout=timedelta(minutes=minutes), reason=reason)
    #     boci2: discord.Member = interaction.guild.get_member(422386822350635008)
    #     await boci2.timeout(timeout=timedelta(minutes=minutes), reason=reason)
    #     await interaction.send(f"Timeouted both Boci accounts for {minutes} minutes, reason: {reason}")

    @discord.slash_command(name="csgo")
    async def csgo(self, interaction: discord.Interaction, how_many_needed: int = discord.SlashOption(choices=[1,2,3,4])):
        # "({self.link.value}\n" + '"{}"'.format(self.hovertext.value) + ")"
        title = f"[__Launch!__](steam://rungameid/730\n" + '"{}"'.format('Launch CS2') + ")"
        embedVar = discord.Embed(title=f"{interaction.user.display_name} is LFG for CS2",
                              description=f"{how_many_needed} needed!")
                              # description=f"{how_many_needed} needed!\n{title}")
        embedVar.add_field(name=interaction.user.display_name, value=f"I'm ready! {emoji.emojize(':check_mark_button:')}")
        viewObj = discord.ui.View(timeout=None)
        viewObj.add_item(self.Whenimcoming(interaction))
        await interaction.send(discord.utils.find(lambda a: any(i in a.name.lower() for i in ("csgo", "pangtok", "szieszgo", "cs2")), interaction.guild.roles).mention, embed=embedVar, view=viewObj)

    class Whenimcoming(discord.ui.StringSelect):
        def __init__(self, inter: discord.Interaction):
            super().__init__()
            self.inter = inter
            self.options = [discord.SelectOption(label="I'm ready!", emoji=emoji.emojize(":check_mark_button:"))] + [discord.SelectOption(label=f"im here in {i} mins", value=str(i), emoji=emoji.emojize(f":{ {1: 'one', 2: 'two', 3: 'three', 4: 'six'}[n] }_o’clock:")) for n,i in enumerate((5,10,15,30),start=1)]
            self.options += [discord.SelectOption(label="Later", emoji=emoji.emojize(":sunset:")), discord.SelectOption(label="I don't play CSGO", emoji=emoji.emojize(":no_bell:", language="alias"))]

        async def callback(self, interaction: discord.Interaction) -> None:
            val = self.values[0]
            self.msg: discord.Message = await self.inter.original_message()
            embed: discord.Embed = self.msg.embeds[0]
            readys = int(embed.description[0])
            ppl = [i.name for i in embed.fields]
            if interaction.user.display_name in ppl:
                person: int = ppl.index(interaction.user.display_name)
                embed.remove_field(person)
                readys += 1
            if val.isdigit() or val == "I'm ready!":

                now = datetime.now()
                readys -= 1

                if val.isdigit():
                    timestr = now + timedelta(minutes=int(val))
                    embed.add_field(name=interaction.user.display_name, value=discord.utils.format_dt(timestr, style="R"), inline=False)
                else:
                    embed.add_field(name=interaction.user.display_name, value=f"{val} {emoji.emojize(':check_mark_button:')}", inline=False)

            elif val == "Later":
                embed.add_field(name=interaction.user.display_name, value=f"{val} {emoji.emojize(':cross_mark:')}", inline=False)
            elif val == "I don't play CSGO":
                await interaction.user.remove_roles(discord.utils.find(lambda a: any(i in a.name.lower() for i in ("csgo", "pangtok", "szieszgo")), interaction.guild.roles), reason="Removed by themselves.")
            else:
                pass

            # title = f"[__Launch!__](steam://rungameid/730\n" + '"{}"'.format('Launch CSGO') + ")"
            # # embed.description = f"{max(0,readys)} needed!\n{title}"
            # embed.description = f"{max(0,readys)} needed!"
            title = f"[__Launch!__](steam://rungameid/730 'Launch CSGO')"
            embed.description = f"{max(0, readys)} needed!\n{title}"
            await self.msg.edit(embed=embed)

    @commands.Cog.listener()
    async def on_typing(self, channel: discord.TextChannel, who: discord.Member, when: datetime):
        if stunlocked:
            if who.id == stunlocked.id:
                await who.timeout(timedelta(seconds=15), reason="Te csak ne írjál")
                await channel.send(f"Te csak ne írjál semmit, {who.display_name}.")


def setup(client):
    client.add_cog(MiscallenousCog(client))
