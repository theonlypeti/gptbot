import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO
import emoji
import nextcord as discord
from PIL import Image, ImageDraw, ImageFont
from numpy import clip
from profanity_check import profanity_check
from utils import antimakkcen
from nextcord.ext import commands


class ListenerCog(commands.Cog):
    def __init__(self, client):
        self.logger = client.logger.getChild(f"{self.__module__}")
        self.client = client
        self.stunlocked = None
        self.us = set()
        self.timeouts = defaultdict(int)
        self.already_checked = []
        self.readtimeouts()
        self.readus()

    def readtimeouts(self):
        try:
            with open(r"data/timeouts.txt", "r") as file:
                for k, v in json.load(file).items():
                    self.timeouts.update({k: v})
        except IOError:
            with open(r"data/timeouts.txt", "w") as file:
                json.dump({}, file, indent=4)

    def writeus(self):
        with open(r"data/us.txt", "w") as file:
            json.dump(list(self.us), file, indent=4)

    def readus(self):
        try:
            with open(r"data/us.txt", "r") as file:
                self.us = set(json.load(file))
                self.logger.debug(f"Read {len(self.us)} us from file")
        except IOError as e:
            self.logger.error(e)
            with open(r"data/us.txt", "w") as file:
                json.dump([], file, indent=4)

    @commands.Cog.listener("on_message")
    async def free_nitro(self, msg: discord.Message):
        # if msg.guild.id not in []:
        if True:
            if "free nitro" in antimakkcen.antimakkcen(msg.content).casefold():
                await msg.channel.send("bitch what the fok **/ban**")

    @commands.Cog.listener("on_message")
    async def someone(self, msg: discord.Message):
        # if msg.guild.id in []:
        if True:
            if not msg.author.bot:
                if any(word in msg.content for word in ("@someone", "@anyone", "@random")):
                    members = [member for member in msg.guild.members if
                               msg.channel.permissions_for(member).read_messages]
                    await msg.reply(random.choice(members).mention)

    @commands.Cog.listener("on_message")
    async def profanity(self, msg: discord.Message):
        if msg.guild and msg.guild.id in []:
            if not msg.author.bot:
                if any(profanity_check.predict(msg.content.split(" "))):
                    await msg.reply("This is a christian minecraft server! No naughty words!")

    @commands.Cog.listener("on_message")
    async def on_reply_to_amogus(self, msg: discord.Message):
        paid_users = ()
        if msg.author.id not in paid_users:
            if not msg.author.bot:
                if msg.reference:
                    repliedto = msg.reference.cached_message
                    if repliedto:
                        if repliedto.author == msg.guild.me:
                            if repliedto.attachments:
                                if repliedto.attachments[0].filename == "amogus.png":
                                    if any(profanity_check.predict(msg.content.split(" "))):
                                        text = "**0.99€** to **SK87 7500 3000 0300 1307 3022** \n+ discord username/id as comment\ndisable amogus for your account\nverification time varies"
                                        await msg.reply(text)
                                        self.logger.warning("Triggered lol")

    @commands.Cog.listener("on_message")
    async def amogus(self, msg: discord.Message):
        if msg.guild and msg.guild.id not in (800196118570205216,):
            words = msg.content.split(" ")
            for word in words:
                if (word.lower().endswith("us") or word.lower().endswith("usz")) and len(word) in range(4, 15) and word.lower() not in self.us:
                    self.us.add(word.lower())
                    self.writeus()
                    img = Image.open(r"data/amogus.png")  # TODO extract this writing thing to a func?
                    d = ImageDraw.Draw(img)
                    textsize = img.width * (1 / (len(word)))
                    textsize = int(clip(textsize, 30, 60))
                    fnt = ImageFont.truetype('impact.ttf', size=textsize)

                    newquestion = ""
                    for i in range(0, len(word), 38):
                        newquestion += word[i:i + 38] + "\n"

                    textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100,
                                  "fill": (255, 255, 255), "anchor": "mm"}
                    d.multiline_text((img.width / 2, textsize + (textsize * len(word) // 38)), newquestion,
                                     **textconfig)
                    img.thumbnail((192, 231))

                    with BytesIO() as image_binary:
                        img.save(image_binary, "png")
                        image_binary.seek(0)
                        await msg.reply(file=discord.File(fp=image_binary, filename=f'amogus.png'))
                    break

    @commands.Cog.listener("on_reaction_add")
    async def kekcounter(self, reaction: discord.Reaction, user: discord.Member):
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

        if str(reaction.emoji) in (
        "<:kekcry:871410695953059870>", "<:kekw:800726027290148884>", "<:hapi:889603218273878118>", ":joy:",
        "<:kekw:1101064898391314462>", ":rofl:"):
            # if reaction.message.author.id in (569937005463601152, 422386822350635008):
            if reaction.message.guild.id in (691647519771328552,):
                # if True:
                if user.id == reaction.message.author.id:  # (569937005463601152, 422386822350635008):
                    kapja: discord.Member = reaction.message.author
                    self.already_checked.append(reaction.message.id)
                    timeout = self.timeouts.get(str(kapja.id), 0)
                    uzenet = discord.Embed(
                        description="Imagine saját vicceiden nevetni. <:bonkdoge:950439465904644128> <a:catblushy:913875026606948393>")
                    uzenet.set_footer(text=f"Current timeout is at {2 ** timeout} minutes.")
                    await reaction.message.reply(embed=uzenet)
                    await kapja.timeout(timedelta(minutes=2 ** timeout), reason="Saját magára rakta a keket")
                    self.timeouts[str(kapja.id)] += 1
                    self.logger.debug(self.timeouts)

        elif emoji.demojize(str(reaction.emoji)) in (
        ":thumbs_down:", "<:2head:913874980033421332>", "<:bruh:913875008697286716>", "<:brainlet:766681101305118721>",
        "<:whatchamp:913874952887873596>"):
            # if reaction.message.author.id in (569937005463601152, 422386822350635008): #csak bocira timeout
            # if True: #mindenkire timeout
            if reaction.message.guild.id in (601381789096738863, 691647519771328552):
                kapja = reaction.message.author
                timeout = self.timeouts.get(str(kapja.id), 0)
                if reaction.count >= 3:
                    if reaction.message.id not in self.already_checked:
                        self.already_checked.append(reaction.message.id)
                        await kapja.timeout(timedelta(minutes=2 ** timeout), reason="Nem volt vicces")
                        uzenet = discord.Embed(description=random.choice((
                                                                         f"Nem volt vicces, {reaction.message.author.display_name} <:nothapi:1007757789629796422>.",
                                                                         "Ki kérdezett")))
                        uzenet.set_footer(text=f"Current timeout is at {2 ** timeout} minutes.")
                        await reaction.message.reply(embed=uzenet)
                        self.timeouts[str(kapja.id)] += 1
                        self.logger.debug(self.timeouts)

        if emoji.demojize(str(reaction.emoji)) in (
        "<:kekcry:871410695953059870>", "<:kekw:800726027290148884>", "<:hapi:889603218273878118>", ":joy:",
        "<:kekw:1101064898391314462>", ":rofl:"):
            # if reaction.message.author.id == 569937005463601152:
            # if True:
            if reaction.message.guild.id in (691647519771328552,):
                if reaction.count >= 3:
                    if reaction.message.id not in self.already_checked:
                        self.already_checked.append(reaction.message.id)
                        uzenet = random.choice(good_responses)
                        sent = reaction.message.created_at
                        tz_info = sent.tzinfo
                        now = datetime.now(tz_info)
                        if (now - sent) < timedelta(minutes=10):
                            await reaction.message.reply(uzenet, mention_author=True)
                        else:
                            await reaction.message.reply(uzenet, mention_author=False)
                        try:
                            self.timeouts[str(reaction.message.author.id)] -= 1
                            self.logger.debug(self.timeouts)
                        except KeyError as e:
                            self.logger.info(e)

        with open(r"data/timeouts.txt", "w") as file:
            json.dump(self.timeouts, file, indent=4)
        return reaction, user

    @commands.Cog.listener()
    async def on_typing(self, channel: discord.TextChannel, who: discord.Member, when: datetime):
        if self.stunlocked:
            if who.id == self.stunlocked.id:
                try:
                    await who.timeout(timedelta(seconds=15), reason="Got stunlocked")
                    await channel.send(f"Shut your bitch ass up, {who.display_name}.")
                except Exception as e:
                    await channel.send("Stunlock failed. Maybe i dont have permission to timeout people?", delete_after=10)
                    self.stunlocked = None

    @discord.user_command(name="Stunlock", guild_ids=(601381789096738863,))
    async def stunlock(self, interaction: discord.Interaction, user: discord.User):
        if self.stunlocked == user:
            self.stunlocked = None
        else:
            self.stunlocked = user
        await interaction.send(f"Stunlokced {self.stunlocked}", ephemeral=True)


def setup(client):
    client.add_cog(ListenerCog(client))
