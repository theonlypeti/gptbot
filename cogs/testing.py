import asyncio
import logging
import os
import random
from io import BytesIO
from typing import Union, Optional
import nextcord as discord
from PIL import Image, ImageOps, ImageDraw, ImageFont
from nextcord.ext import commands
from pycaw.utils import AudioUtilities

TESTSERVER = (860527626100015154,)

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
        with open(r"data/karomkodasok.txt","r", encoding="UTF-8") as file:
            self.karomkodasok = file.readlines()
        self.logger.debug(f"{len(self.karomkodasok)} bad words loaded.")

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


    @discord.slash_command(name="pick", description="pick",guild_ids=TESTSERVER)
    async def fut(self, ctx):
        pass

    @fut.subcommand(name="shop", description="shop")
    async def fut3(self, ctx):
        await ctx.response.defer()
        orig = os.getcwd()
        if ctx.user.id != 617840759466360842:
            return
        os.chdir(r"D:\Users\Peti.B\Pictures\microsoft\Windows\shop")
        sample = [file for file in os.listdir() if not file.endswith(".mp4")]
        await ctx.send(files=[discord.File(random.choice(sample))])
        os.chdir(orig)

    @fut.subcommand(name="kat", description="kat")
    async def fut4(self, ctx):
        await ctx.response.defer()
        orig = os.getcwd()
        if ctx.user.id != 617840759466360842:
            return
        os.chdir(r"D:\Users\Peti.B\Pictures\Mobil Backup\other\pokemons\KT")
        sample = [file for file in os.listdir() if not file.endswith(".mp4")]
        await ctx.send(files=[discord.File(random.choice(sample))])
        os.chdir(orig)

    @fut.subcommand(name="reddit")
    async def fut2(self, ctx):
        await ctx.response.defer()
        orig = os.getcwd()
        if ctx.user.id != 617840759466360842:
            return
        os.chdir(r"D:\Users\Peti.B\Pictures\microsoft\Windows\reddit")
        sample = [file for file in os.listdir() if not file.endswith(".mp4")]
        await ctx.send(files=[discord.File(random.choice(sample))])
        os.chdir(orig)

    async def showimg(self,
                    interface: Union[discord.Interaction, discord.Message],
                    img: Image,
                    filetype: str,
                    view: discord.ui.View = None,
                    txt:str = None) -> discord.Message:

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

    # @discord.slash_command(name="flowers", description="viragok")
    # async def flowers(self, interaction: discord.Interaction, num: int):
    #     await interaction.response.defer()
    #     img = Image.new("RGBA", (3072, 2048), (0, 0, 0, 0))
    #     for i in range(num):
    #         mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
    #         mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
    #         virag = mappa + "/" + random.choice(os.listdir(mappa))
    #         with open(virag, "rb") as file:
    #             print(i)
    #             virag = Image.open(file)
    #             img.paste(virag, (random.randint(0, img.width), random.randint(0, img.height)), virag)
    #
    #     with BytesIO() as image_binary:
    #         img.save(image_binary, "PNG")
    #         image_binary.seek(0)
    #         await interaction.send(file=discord.File(image_binary, "flowers.PNG"))

    @discord.user_command(name="Karomkodas")
    async def karmokdoas(self, interaction: discord.Interaction, user: discord.User):
        # await interaction.response.defer() #if deferred, the tts doesn't work
        csunya = " ".join(random.choice(self.karomkodasok).strip().lower() for _ in range(5))
        await interaction.send(content=f"{user.mention} te {csunya}!", tts=True)


def setup(client, baselogger):
    client.add_cog(Testing(client, baselogger))
