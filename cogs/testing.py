import logging
import os
import random
import traceback
from io import BytesIO
from pathlib import Path
import time as time_module
from bs4 import BeautifulSoup as html
import aiohttp
import nextcord as discord
from nextcord.ext import tasks
from PIL import Image, ImageOps, ImageDraw, ImageFont
from EdgeGPT.EdgeGPT import ConversationStyle
from utils.getMsgFromLink import getMsgFromLink
from nextcord.ext import commands
from textwrap import wrap

TESTSERVER = (860527626100015154,)
root = os.getcwd()

class Selection:
    def __init__(self, img: Image, boundary: tuple):
        copy = img.copy()
        self.image = copy.crop(boundary)
        self.boundary = boundary

class Testing(commands.Cog):
    def __init__(self, client, baselogger: logging.Logger):
        self.logger = baselogger.getChild(__name__)
        self.selection = None
        self.client: discord.Client = client
        # self.wiki.start()

    @tasks.loop(minutes=1)
    async def wiki(self):
        self.logger.debug("ran")
        async with aiohttp.ClientSession() as session:
            async with session.get('https://en.wikipedia.org/wiki/Special:Random') as req:
                link = req.url
        await self.client.get_channel(790588807770669126).send(link)

    @wiki.before_loop  # i could comment this out but then it would look not pretty how my bootup time shot up by 5s haha
    async def before_wiki(self):
        self.logger.debug('getting wiki')
        await self.client.wait_until_ready()

    class testvw(discord.ui.View):
        def __init__(self):
            self.msg = None
            super().__init__(timeout=0)

        @discord.ui.button(label="test")
        async def test(self, button, interaction):
            print("test")
            button.style = discord.ButtonStyle.green
            await self.msg.edit(view=self)

        async def on_timeout(self) -> None:
            print("timeout")
            self.children[0].disabled = True
            await self.msg.edit(view=self)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.display_name == "Peti"

    class TextInputModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="d")
            self.bottomtext = discord.ui.TextInput(label="Bottom Text", required=False)
            self.add_item(self.bottomtext)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            await interaction.response.send_modal(self)

    # @discord.slash_command(name="scrape", description="testing", guild_ids=TESTSERVER)
    # async def scrape(self, ctx: discord.Interaction):
    #     await ctx.response.defer()
    #     channel: discord.TextChannel = ctx.channel
    #     counter = 0
    #     async for message in channel.history(limit=220):
    #         if message.content.startswith("https://discord.com/channels"):
    #             print(message.content)
    #             counter += 1
    #     #await channel.purge(limit=220,check= lambda a: a.content.startswith("https://discord.com/channels") and a.created_at().month >= 4,bulk=True)
    #     await ctx.send("done")
    #     print(counter)

    # @discord.slash_command(name="testingvw", description="testing")
    # async def testing(self, ctx):
    #     viewObj = self.testvw()
    #     viewObj.msg = await ctx.send(content="Hello", view=viewObj, tts=True)

    # @discord.slash_command(name="modaltesting", description="testing", guild_ids=TESTSERVER)
    # async def modaltesting(self, ctx):
    #     await ctx.response.send_modal(self.TextInputModal())

    async def showimg(self,
                      interface: discord.Interaction | discord.Message,
                      img: Image,
                      filetype: str,
                      view: discord.ui.View = None,
                      txt: str = None) -> discord.Message:

        with BytesIO() as image_binary:
            if img:
                img.save(image_binary, filetype)
                image_binary.seek(0)

            if isinstance(interface, discord.Interaction):
                msg = await interface.send(txt, file=discord.File(fp=image_binary, filename=f'image.{filetype}'), view=view)

            elif isinstance(interface, discord.Message):
                if img:
                    msg = await interface.edit(file=discord.File(fp=image_binary, filename=f'image.{filetype}'), view=view, content=txt)
                else:
                    msg = await interface.edit(view=view, content=txt)

            else:
                raise NotImplementedError("interface must be either discord.Interaction or discord.Message")
        return msg

    @discord.message_command(name="flowersss", guild_ids=(601381789096738863,691647519771328552))
    async def flowersprofilka(self, interaction: discord.Interaction, msg: discord.Message):
        await interaction.response.defer()
        with BytesIO() as image:
            await msg.attachments[0].save(image)
            # await user.display_avatar.save(image)
            img = Image.open(image)
            for i in range(56):
                mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
                mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
                virag = mappa + "/" + random.choice(os.listdir(mappa))
                with open(virag, "rb") as file:
                    virag = Image.open(file)
                    size = img.width // 8
                    virag.thumbnail((size, size))
                    img.paste(virag, (random.choice([i for i in range(-size // 3, int(img.width - (size * 1))) if
                                                     i not in range(size * 1, img.width - size * 3)]),
                                      random.randint(0, img.height - size * 2)), virag)

            for i in range(24):
                mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
                mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
                virag = mappa + "/" + random.choice(os.listdir(mappa))
                with open(virag, "rb") as file:
                    virag = Image.open(file)
                    size = img.width // 8
                    virag.thumbnail((size, size))
                    img.paste(virag,
                              (random.randint(0, img.width), random.randint(img.height - size * 2, img.height - size)),
                              virag)

            d = ImageDraw.Draw(img)
            fnt = ImageFont.truetype('FREESCPT.TTF', size=size)

            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100,
                          "fill": (255, 255, 255), "anchor": "mm"}

            # szoveg = random.choice(("Jó éjszakát mindenkinek", "Kellemes ünnepeket", "Áldott hétvégét kívánok", "Meghalt a Jóska xd"))
            szoveg = random.choice(("Dobrú noc vám prajem!", "Pozehnaný víkend vám prajem!", "Kávicka pohodicka",
                                    "Príjemné popoludnie prajem!"))
            d.multiline_text((img.width / 2, img.height - size), szoveg, **textconfig)

        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await interaction.send(file=discord.File(image_binary, "flowers.PNG"))

    # @discord.message_command(name="flowers", description="viragok")
    # async def flowerss(self, interaction: discord.Interaction, msg: discord.Message):
    #     # async def caesar(self, interaction: discord.Interaction, text: discord.Message):
    #     await interaction.response.defer()
    #     img =
    #     img = Image.new("RGBA", (3072, 2048), (0, 0, 0, 0))
    #     for i in range(num):
    #         mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
    #         mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
    #         virag = mappa + "/" + random.choice(os.listdir(mappa))
    #         with open(virag, "rb") as file:
    #             virag = Image.open(file)
    #             img.paste(virag, (random.randint(0, img.width), random.randint(0, img.height)), virag)
    #
    #     with BytesIO() as image_binary:
    #         img.save(image_binary, "PNG")
    #         image_binary.seek(0)
    #         await interaction.send(file=discord.File(image_binary, "flowers.PNG"))

    @discord.slash_command(name="imgtest", guild_ids=TESTSERVER)
    async def imgtest(self, interaction: discord.Interaction, img: discord.Attachment):
        # with BytesIO() as file_binary:
        #     await img.save(file_binary)
        #     await interaction.send(file=discord.File(fp=file_binary, filename="img.png"))

        fp = BytesIO(await img.read())
        await interaction.send(file=discord.File(fp, "test.png"))

    # @discord.message_command(name="En-/Decrypt")
    # async def caesar(self, interaction: discord.Interaction, text: discord.Message):
    #     if text.type == discord.MessageType.chat_input_command and text.embeds[0].title == "Message":
    #         text = text.embeds[0].description
    #     else:
    #         text = text.content
    #     await interaction.send("".join([chr(((ord(letter) - 97 + 13) % 26) + 97) if letter.isalpha() and letter.islower() else chr(((ord(letter) - 65 + 13) % 26) + 65) if letter.isalpha() and letter.isupper() else letter for letter in text]))

    # @discord.slash_command(name="muv", description="semi", guild_ids=[860527626100015154, 601381789096738863])
    # async def movebogi(self, ctx, chanel: discord.abc.GuildChannel):
    #    await ctx.user.move_to(chanel)

    # @discord.slash_command(name="muvraw", description="semi", guild_ids=[860527626100015154, 601381789096738863])
    # async def movebogi2(self, ctx, chanel):
    #     chanel = ctx.guild.get_channel(int(chanel))
    #     await ctx.user.move_to(chanel)

    # @discord.message_command(name="Unemojize")
    # async def unemojize(self, interaction: discord.Interaction, message):
    #     await interaction.response.send_message(f"`{emoji.demojize(message.content)}`", ephemeral=True)

    @discord.slash_command(name="whtest2", guild_ids=TESTSERVER)
    async def whtest2(self, interaction: discord.Interaction):
        channel: discord.TextChannel = interaction.channel
        whs = await channel.webhooks()
        await interaction.send(content=", ".join([str(wh.url) for wh in whs]))


    @discord.slash_command(name="chatgpt")
    async def query(self, interaction: discord.Interaction, query: str, model: str =discord.SlashOption(name="model", description="What model to use when responding", choices=("Creative", "Balanced", "Precise"),default="Balanced", required=False)):
        from EdgeGPT.EdgeUtils import Query, Cookie
        # import json
        await interaction.response.defer()
        # Cookie.current_filepath = r"./data/cookies/bing_cookies_bp.json"
        Cookie.dir_path = r"./data/cookies"
        print(os.listdir(Cookie.dir_path))
        Cookie.import_data()
        print(model.lower())
        try:
            # cookies = json.loads(open(r"../data/bing_cookies_my.json", encoding="utf-8").read())  # might omit cookies option
            q = Query(query)
            # q = Query(query, cookie_files={Path(r"/data/cookies/bing_cookies_my.json")}, style=model.lower())
            # q = Query(query)
            await q.log_and_send_query(True, False)
        except Exception as e:
            embed = discord.Embed(title=query, description=e, color=discord.Color.red())
            await interaction.send(embed=embed, delete_after=180)
            return
        text = q.output
        for text in wrap(text, 4000):
            embed = discord.Embed(title=query, description=text, color=interaction.user.color)
            await interaction.send(embed=embed)

    @discord.slash_command(name="wh", guild_ids=TESTSERVER + (800196118570205216, 601381789096738863, 409081549645152256, 691647519771328552))
    async def whtet3(self, interaction: discord.Interaction, txt: str, name: str, pfp_link: str = None, tts: bool = False, channel: discord.TextChannel = None):
        chann: discord.PartialMessage|discord.Interaction = await getMsgFromLink(self.client, channel) if channel else interaction
        channel: discord.TextChannel = chann.channel
        self.logger.debug(f"{channel.name}, {interaction.user.display_name}, {txt}")
        whs = [0]
        try:
            whs = await channel.webhooks()
        except discord.errors.Forbidden as e:
            print(e)
            return
        else:
            if whs == [0]:
                print("no whs")
                return
            else:
                if not (wh := (discord.utils.find(lambda wh: wh.name == f"emotehijack{channel.id}", whs))):
                    wh = await channel.create_webhook(name=f"emotehijack{channel.id}")
                await wh.send(content=f"{txt}", username=name, avatar_url=pfp_link, tts=tts)
                await interaction.send("done", ephemeral=True)

def setup(client, baselogger):
    client.add_cog(Testing(client, baselogger))
