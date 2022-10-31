import asyncio
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
    def __init__(self, client, baselogger):
        self.selection = None
        self.client = client

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

    @discord.slash_command(name="pick", description="pick", guild_ids=TESTSERVER)
    async def fut(self, ctx):
        await ctx.response.defer()
        orig = os.getcwd()
        if ctx.user.id != 617840759466360842:
            return
        os.chdir(r"D:\Users\Peti.B\Pictures\microsoft\Windows\shop")
        sample = [file for file in os.listdir() if not file.endswith(".mp4")]
        await ctx.send(files=[discord.File(random.choice(sample))])
        os.chdir(orig)

    # @discord.slash_command(name="testselections", description="Image editor in development")
    # async def testimageeditorcommand(self, interaction: discord.Interaction,
    #                              img: discord.Attachment = discord.SlashOption(name="image",
    #                                                                            description="The image to edit.",
    #                                                                            required=True)):
    #     await interaction.response.defer()
    #     filetype = img.content_type.split("/")[1]
    #     image = await img.read()
    #     img = Image.open(BytesIO(image))
    #     img = img.convert("RGB")  # .point(lambda x: 255 - x)
    #     selection = Selection(img, (0, 0, img.size[0]/2, img.size[1]/2))   #left top right bottom
    #     selection.image = ImageOps.invert(selection.image)
    #     img.paste(selection.image, box=selection.boundary)
    #     with BytesIO() as image_binary:
    #         img.save(image_binary, filetype)
    #         image_binary.seek(0)
    #         await interaction.send(file=discord.File(fp=image_binary, filename=f'image.{filetype}'))

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

    # class TestDeleteButton(discord.ui.View):
    #     def __init__(self, cog, img=None):
    #         self.message = None
    #         self.img = img
    #         self.cog = cog
    #         super().__init__(timeout=None)
    #
    #     @discord.ui.button(label="Delete me")
    #     async def removeeview(self, button, interaction):
    #         print(interaction.message, "\n", self.message)
    #         print(interaction.message.id, self.message.id, interaction.message == self.message)
    #
    #         await self.cog.showimg(interaction.message, img=self.img, filetype="png", view=None,txt="Removing view via inter.message with a file present")  # this one will not remove the view
    #         await asyncio.sleep(4)
    #         await self.cog.showimg(interaction.message, img=None, filetype="png", view=None, txt="Removing view via inter.message with file not included")  # this one will remove the view
    #         await asyncio.sleep(4)
    #         await self.cog.showimg(interaction.message, img=self.img, filetype="png", view=self, txt="lets try again")
    #         await asyncio.sleep(2)
    #         await self.cog.showimg(self.message, img=self.img, filetype="png", view=None, txt="Removing view via a saved var:WebhookMessage with a file present")  # this one will remove the view
    #         await asyncio.sleep(4)
    #         await self.cog.showimg(self.message, img=self.img, filetype="png", view=self, txt="lets try again")
    #         await asyncio.sleep(2)
    #         await self.cog.showimg(self.message, img=None, filetype="png", view=None, txt="Removing view via a saved var:WebhookMessage without a file")  # this one will remove the view

    # @discord.slash_command(name="testeditview", description="bug maybe")
    # async def testimageeditorcommand(self, interaction: discord.Interaction, img: discord.Attachment):
    #     await interaction.response.defer()
    #     image = await img.read()
    #     img = Image.open(BytesIO(image))
    #     view = self.TestDeleteButton(self, img)
    #     msg = await self.showimg(interaction, img, "png", view, txt="Hi")
    #     view.message = msg

    @discord.slash_command(name="flowers", description="viragok")
    async def flowers(self, interaction: discord.Interaction, num: int):
        await interaction.response.defer()
        img = Image.new("RGBA", (3072, 2048), (0, 0, 0, 0))
        for i in range(num):
            mappak = os.listdir(r"D:\Users\Peti.B\Downloads\viragok")
            mappa = r"D:\Users\Peti.B\Downloads\viragok/" + random.choice(mappak)
            virag = mappa + "/" + random.choice(os.listdir(mappa))
            with open(virag, "rb") as file:
                print(i)
                virag = Image.open(file)
                img.paste(virag, (random.randint(0, img.width), random.randint(0, img.height)), virag)

        with BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)
            await interaction.send(file=discord.File(image_binary, "flowers.PNG"))

    # @discord.slash_command(name="flipemote", description="flips an emote",guild_ids=tuple())
    # async def flipemote(self, interaction: discord.Interaction, emote: str):
    #     emoteserver: discord.Guild = self.client.get_guild(957469186798518282)
    #     em = discord.PartialEmoji.from_str(emote)
    #     em = discord.PartialEmoji.with_state(interaction.guild.me._state,name=em.name,animated=em.animated,id=em.id)
    #     print(em)
    #     # with BytesIO() as image_binary:
    #     #     img.save(image_binary, format="png")
    #     #     image_binary.seek(0)
    #     file = await em.to_file()
    #     img = Image.open(file.fp) #invalid start byte if em.read
    #     img = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
    #     with BytesIO() as image_binary:
    #         img.save(image_binary, format="png")
    #         image_binary.seek(0)
    #         newemoji = await emoteserver.create_custom_emoji(name=f"{em.name}flip", image=image_binary.read())
    #     await interaction.send(f"{newemoji}")
    #     await emoteserver.delete_emoji(newemoji)


def setup(client, baselogger):
    client.add_cog(Testing(client, baselogger))
