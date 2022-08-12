import PIL.ImageQt
import emoji
import nextcord as discord
from nextcord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

class PillowCog(commands.Cog):
    def __init__(self,client,baselogger):
        self.client = client

    class EditorView(discord.ui.View):
        def __init__(self, cog: commands.Cog, message: discord.Message, image: PIL.Image, filetype: str):
            self.filetype = filetype
            self.cog = cog
            self.message = message
            self.img = image
            super().__init__()

        @discord.ui.button(label="Text", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":memo:"))
        async def texteditorbutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.TextInputModal(self))

            pass #edit text button modal, okbuttn, edit size select, edit font select, edit color select?, edit outline select?

        @discord.ui.button(label="Rotate/Flip", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':right_arrow_curving_left:'))
        async def rotatebutton(self, button, interaction):
            viewObj = self.cog.TransformView(self)
            await self.message.edit(view=viewObj)
            pass #90,180,-90,flipH,flipV

        @discord.ui.button(label="Corrections", style=discord.ButtonStyle.gray,emoji=emoji.emojize(':level_slider:'),disabled=1)
        async def slidersbutton(self, button, interaction):
            pass  # contrast, saturation, brightness, hue?, gamma?

        @discord.ui.button(label="Crop", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':scissors:'))
        async def cropbutton(self, button, interaction):
            await interaction.response.defer()
            viewObj = self.cog.CropView(self)
            thumbnail = viewObj.drawBoundaries()
            thumbnail.save(f"{interaction.user.id}.{self.filetype}")
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"),view=viewObj)
            # button with modal for each corner and have a preview drawn with lines and an ok button?

        @discord.ui.button(label="Rescale", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':pinching_hand:'),disabled=1)
        async def resizesbutton(self, button, interaction):
            pass  # modal buttons for height and width aspect ratio? but in pixels? and a select for common aspect ratios

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finishbutton(self, button, interaction):
            await interaction.response.defer()
            self.img.save(f"{interaction.user.id}.{self.filetype}")
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"),view=None)

    class TransformView(discord.ui.View):
        def __init__(self,returnView: discord.ui.View):
            self.cog = returnView.cog
            self.img = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            super().__init__()

        def makeThumbnail(self,interaction: discord.Interaction):
            copy = self.img.copy()
            copy.thumbnail(tuple(map(lambda x: x // 2, copy.size)))
            copy.save(f"{interaction.user.id}.{self.filetype}")

        @discord.ui.button(label="Left", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_right_hook:",language="alias"))
        async def rotateleft(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.ROTATE_90)
            self.makeThumbnail(interaction)
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"))

        @discord.ui.button(label="Right", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":leftwards_arrow_with_hook:", language="alias"))
        async def rotateright(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.ROTATE_270)
            self.makeThumbnail(interaction)
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"))

        @discord.ui.button(label="Flip Horizont", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":left_right_arrow:", language="alias"))
        async def horizontalflip(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
            self.makeThumbnail(interaction)
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"))

        @discord.ui.button(label="Flip Vertical", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":arrow_up_down:", language="alias"))
        async def verticalflip(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
            self.makeThumbnail(interaction)
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"))

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finalizecropbutton(self, button, interaction):
            await interaction.response.defer()
            await self.message.edit(view=self.cog.EditorView(self.cog, self.message, self.img, self.filetype))

    class CropView(discord.ui.View):
        def __init__(self,returnView: discord.ui.View, boundaries: dict = None):
            self.cog = returnView.cog
            self.img = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            self.boundaries = boundaries or {"left":0,"top":0,"right":self.img.width,"bottom":self.img.height}
            super().__init__()

        async def returnMenu(self, interaction: discord.Interaction):
            copy = self.img.copy()
            copy.thumbnail(tuple(map(lambda x: x // 2, copy.size)))
            copy.save(f"{interaction.user.id}.{self.filetype}")
            await self.message.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"),view=self.cog.EditorView(self.cog, self.message, self.img, self.filetype))

        def drawBoundaries(self):
            copy = self.img.copy()
            drawctx = ImageDraw.Draw(copy)
            drawctx.rectangle((self.boundaries["left"],self.boundaries["top"],self.boundaries["right"],self.boundaries["bottom"]),outline=(255,125,0),width=4)
            copy.thumbnail(tuple(map(lambda x: x//2,copy.size)))
            return copy

        def processImage(self):
            self.img = self.img.crop(tuple(self.boundaries.values())) #left,upper,right,bottom

        @discord.ui.button(label="Edit boundaries", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":white_square_button:",language="alias"))
        async def editboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.CropInputModal(self.boundaries,self))

        @discord.ui.button(label="Crop", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finalizecropbutton(self, button, interaction):
            await interaction.response.defer()
            self.processImage()
            await self.returnMenu(interaction)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"))
        async def canceleditbutton(self, button, interaction):
            await interaction.response.defer()
            await self.returnMenu(interaction)

    class CropInputModal(discord.ui.Modal):
        def __init__(self,boundaries: dict,view: discord.ui.View):
            super().__init__(title="Set crop boundaries")
            self.returnView = view

            self.topcrop = discord.ui.TextInput(label="n pixels from the TOP",default_value = str(boundaries["top"]))
            self.bottomcrop = discord.ui.TextInput(label="bottom boundary",default_value = str(boundaries["bottom"]))
            self.leftcrop = discord.ui.TextInput(label="n pixels from the LEFT",default_value = str(boundaries["left"]))
            self.rightcrop = discord.ui.TextInput(label="right boundary",default_value = str(boundaries["right"]))
            self.add_item(self.topcrop)
            self.add_item(self.bottomcrop)
            self.add_item(self.leftcrop)
            self.add_item(self.rightcrop)

        async def callback(self,ctx):
            await ctx.response.defer()
            boundaries = {"left": int(self.leftcrop.value),"top": int(self.topcrop.value), "right": int(self.rightcrop.value), "bottom": int(self.bottomcrop.value)}
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            thumbnail.save(f"{ctx.user.id}.{self.returnView.filetype}")
            await self.returnView.message.edit(file=discord.File(f"{ctx.user.id}.{self.returnView.filetype}"),view=self.returnView)

    class TextInputModal(discord.ui.Modal):
        def __init__(self,returnView: discord.ui.View):
            self.returnView = returnView
            self.img = returnView.img
            self.msg = returnView.message
            self.filetype = returnView.filetype
            super().__init__(title="Add text to your image")
            self.toptext = discord.ui.TextInput(label="Top Text",required=False,style=discord.TextInputStyle.short)
            self.add_item(self.toptext)
            self.bottomtext = discord.ui.TextInput(label="Bottom Text",required=False)
            self.add_item(self.bottomtext)

        async def callback(self,interaction: discord.Interaction):
            await interaction.response.defer()
            top = self.toptext.value
            bottom = self.bottomtext.value
            if not top and not bottom:
                return

            mult = ((100 - (len(max(top,bottom,key=len))*2))/100)
            textsize = (self.img.size[0]//10) * max(mult,0.5)
            textsize = int(max(textsize,10))
            fnt = ImageFont.truetype('impact.ttf', size=textsize)
            #fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 40)
            # get a drawing context
            d = ImageDraw.Draw(self.img)

            # draw multiline text
            textconfig = {"font":fnt,"stroke_fill":(0,0,0),"stroke_width":self.img.size[0]//100,"fill":(255,255,255),"anchor":"mm"}
            d.multiline_text((self.img.size[0]/2, textsize), top, **textconfig)
            d.multiline_text((self.img.size[0]/2, self.img.size[1]-textsize), bottom, **textconfig)
            #d.multiline_text((self.img.size[0] / 2, self.img.size[1] - (self.img.size[1] // 10)), bottom, **textconfig)

            thumbnail = self.img.copy()
            thumbnail.thumbnail(tuple(map(lambda x: x // 2, thumbnail.size)))
            thumbnail.save(f"{interaction.user.id}.{self.filetype}")

            #img.show()
            await self.msg.edit(file=discord.File(f"{interaction.user.id}.{self.filetype}"),view=self.returnView)

    @discord.message_command(name="Image editor")
    async def imeditor(self,interaction:discord.Interaction,msg:discord.Message):
        if not msg.attachments:
            if "https:" in msg.content:
                if msg.content.startswith("https:"):
                    pass #todo
                else:
                    pass #todo
            return
        elif len(msg.attachments) > 1:
            img = msg.attachments[0] #TODO selector
        else:
            img = msg.attachments[0]
        await interaction.response.defer()
        await img.save(f"{interaction.user.id}")
        filetype = img.content_type.split("/")[1]
        img = await img.read()
        img = Image.open(BytesIO(img))
        copy: PIL.Image = img.copy()
        copy.thumbnail(tuple(map(lambda x: x // 2, copy.size)))
        copy.save(f"{interaction.user.id}.{filetype}")
        viewObj = self.EditorView(self, interaction.message, img, filetype)
        message = await interaction.send(file=discord.File(f"{interaction.user.id}.{filetype}"), view=viewObj)
        viewObj.message = message

    @discord.slash_command(name="imageditor",description="Image editor in development")
    async def imageeditorcommand(self,interaction: discord.Interaction, img: discord.Attachment = discord.SlashOption(name="image",description="The image to edit.",required=True)):
        await interaction.response.defer()
        filetype = img.content_type.split("/")[1]
        img = await img.read()
        img = Image.open(BytesIO(img))
        copy: PIL.Image = img.copy()
        copy.thumbnail(tuple(map(lambda x: x // 2, copy.size)))
        copy.save(f"{interaction.user.id}.{filetype}")
        viewObj = self.EditorView(self,interaction.message,img, filetype)
        message = await interaction.send(file=discord.File(f"{interaction.user.id}.{filetype}"),view=viewObj)
        viewObj.message = message


def setup(client,baselogger):
    client.add_cog(PillowCog(client,baselogger))