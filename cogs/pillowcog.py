from io import BytesIO
from typing import Union
import emoji
import nextcord as discord
from nextcord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

THUMBNAIL_SIZE = (720, 480)

#TODO make working on selections only
#TODO add quality and speed options

class PillowCog(commands.Cog):
    def __init__(self,client, baselogger):
        self.client = client

    class EditorView(discord.ui.View):
        def __init__(self, cog, message: discord.Message, image: Image, filetype: str):
            self.filetype = filetype
            self.cog = cog
            self.message = message
            self.img = image
            super().__init__()

        @discord.ui.button(label="Add Text", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":memo:"))
        async def texteditorbutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.TextInputModal(self))
            pass #edit text button modal, okbuttn, edit size select, edit font select, edit color select?, edit outline select?

        @discord.ui.button(label="Rotate/Flip", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':right_arrow_curving_left:'))
        async def rotatebutton(self, button, interaction):
            viewObj = self.cog.TransformView(self)
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Corrections", style=discord.ButtonStyle.gray,emoji=emoji.emojize(':level_slider:'),disabled=False)
        async def slidersbutton(self, button, interaction):
            viewObj = self.cog.CorrectionsView(self)
            await self.message.edit(view=viewObj) # contrast, saturation, brightness, hue?, gamma?

        @discord.ui.button(label="Crop", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':scissors:'))
        async def cropbutton(self, button, interaction):
            await interaction.response.defer()
            viewObj = self.cog.CropView(self)
            thumbnail = viewObj.drawBoundaries()
            await self.cog.show(interaction.message, thumbnail, self.filetype, view=viewObj)

        @discord.ui.button(label="Rescale", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':pinching_hand:'),disabled=True)
        async def resizebutton(self, button, interaction):
            pass  # modal buttons for height and width aspect ratio? but in pixels? and a select for common aspect ratios

        @discord.ui.button(label="Filters", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':smile:',language="alias"),disabled=False)
        async def filtersbutton(self, button, interaction):
            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.FiltersDropdown(returnView=self))
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finishbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.show(self.message, self.img, self.filetype, view=None) #note to self, using interaction.message here would not work for some reason

    class RescaleView(discord.ui.View):
        def __init__(self,returnView):
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message: discord.Message = returnView.message
            self.filetype = returnView.filetype
            super().__init__()
            #button for a modal to enter dimensions
            #select with aspect ratio options
            #okbutton
            #cancelbutton

    class FiltersDropdown(discord.ui.Select):
        def __init__(self, returnView):
            self.returnview: discord.ui.View = returnView
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            options = [discord.SelectOption(label="Deepfry"), discord.SelectOption(label="Blur"),discord.SelectOption(label="Invert"),discord.SelectOption(label="Cancel")]
            super().__init__(options=options)

        def deepfry(self,img):
            img = ImageEnhance.Contrast(img).enhance(2)
            img = ImageEnhance.Sharpness(img).enhance(2)
            img = ImageEnhance.Color(img).enhance(2)
            return img.effect_spread(distance=img.size[0])

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()

            if self.values[0] == "Cancel":
                await self.message.edit(view=self.returnview)
                return
            elif self.values[0] == "Deepfry":
                self.img = self.deepfry(self.img)

            elif self.values[0] == "Blur":
                self.img = self.img.filter(ImageFilter.GaussianBlur(3))

            elif self.values[0] == "Invert":
                self.img = self.img.convert("RGB")#.point(lambda x: 255 - x)
                self.img = ImageOps.invert(self.img)

            self.returnview.img = self.img
            await self.cog.returnMenu(view=self.returnview)

    class CorrectionsView(discord.ui.View):
        def __init__(self, returnView: discord.ui.View, corrections: dict = None):
            self.returnview: discord.ui.View = returnView
            self.cog = returnView.cog
            self.img = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            self.corrections: dict = corrections or {"brightness": 100, "contrast": 100, "sharpness": 100, "saturation": 100}
            super().__init__()

        def applyCorrections(self,img: Image) -> Image:
            copy = img
            for corr,value in self.corrections.items():
                if value != 100:
                    if corr == "brightness":
                        copy = ImageEnhance.Brightness(copy).enhance(value/100)
                    elif corr == "contrast":
                        copy = ImageEnhance.Contrast(copy).enhance(value/100)
                    elif corr == "sharpness":
                        copy = ImageEnhance.Sharpness(copy).enhance(value/100)
                    elif corr == "saturation":
                        copy = ImageEnhance.Color(copy).enhance(value/100)
            return copy

        @discord.ui.button(label="Edit corrections", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":level_slider:", language="alias"))
        async def editcorrectionsbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.CorrectionsModal(self,self.corrections))

        @discord.ui.button(label="Done", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finalizecorrectbutton(self, button, interaction):
            await interaction.response.defer()
            self.img = self.applyCorrections(self.img)
            await self.cog.returnMenu(self)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"))
        async def canceleditbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.returnMenu(self)

    class CorrectionsModal(discord.ui.Modal):
        def __init__(self,returnView,corrections: dict = None):
            super().__init__(title="Image corrections (0-200)%")
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message: discord.Message = returnView.message
            self.filetype = returnView.filetype
            self.returnView = returnView

            self.brightness = discord.ui.TextInput(label="Brightness", default_value=corrections["brightness"],min_length=1,max_length=3)
            self.contrast = discord.ui.TextInput(label="Contrast", default_value=corrections["contrast"],min_length=1,max_length=3)
            self.sharpness = discord.ui.TextInput(label="Sharpness", default_value=corrections["sharpness"],min_length=1,max_length=3)
            self.saturation = discord.ui.TextInput(label="Saturation", default_value=corrections["saturation"],min_length=1,max_length=3)

            for item in (self.brightness,self.contrast,self.sharpness,self.saturation):
                self.add_item(item)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                corrections = {"brightness": int(self.brightness.value) or 100, "contrast": int(self.contrast.value) or 100, "sharpness": int(self.sharpness.value) or 100, "saturation": int(self.saturation.value) or 100}
            except ValueError:
                await interaction.send("Input numbers only!",ephemeral=True)
                return
            self.returnView.corrections = corrections
            th = self.cog.makeThumbnail(self.img)
            th = self.returnView.applyCorrections(th)
            await self.cog.show(interaction.message, th, self.filetype, view=self.returnView)

    class TransformView(discord.ui.View):
        def __init__(self,returnView: discord.ui.View):
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message: discord.Message = returnView.message
            self.filetype = returnView.filetype
            super().__init__()

        @discord.ui.button(label="Left", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_right_hook:",language="alias"))
        async def rotateleft(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.ROTATE_90)
            th = self.cog.makeThumbnail(self.img)
            await self.cog.show(interaction.message, th, self.filetype,view=self)

        @discord.ui.button(label="Right", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":leftwards_arrow_with_hook:", language="alias"))
        async def rotateright(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.ROTATE_270)
            th = self.cog.makeThumbnail(self.img)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Flip Horizont", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":left_right_arrow:", language="alias"))
        async def horizontalflip(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
            th = self.cog.makeThumbnail(self.img)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Flip Vertical", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":arrow_up_down:", language="alias"))
        async def verticalflip(self, button, interaction: discord.Interaction):
            self.img = self.img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
            th = self.cog.makeThumbnail(self.img)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finalizeflipbutton(self, button, interaction):
            await interaction.response.defer()
            await self.message.edit(view=self.cog.EditorView(self.cog, self.message, self.img, self.filetype))

    class CropView(discord.ui.View):
        def __init__(self, returnView, boundaries: dict = None):
            self.cog = returnView.cog
            self.img = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            self.boundaries = boundaries or {"left":0,"top":0,"right":self.img.width,"bottom":self.img.height}
            super().__init__()

        def drawBoundaries(self):
            copy = self.img.copy()
            drawctx = ImageDraw.Draw(copy)
            drawctx.rectangle((self.boundaries["left"],self.boundaries["top"],self.boundaries["right"],self.boundaries["bottom"]),outline=(255,125,0),width=6)
            copy.thumbnail(THUMBNAIL_SIZE)
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
            await self.cog.returnMenu(self)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"))
        async def canceleditbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.returnMenu(self)

    class CropInputModal(discord.ui.Modal):
        def __init__(self,boundaries: dict,view):
            super().__init__(title="Set crop boundaries")
            self.returnView: discord.ui.View = view

            self.topcrop = discord.ui.TextInput(label="top boundary",default_value = str(boundaries["top"]))
            self.bottomcrop = discord.ui.TextInput(label="bottom boundary",default_value = str(boundaries["bottom"]))
            self.leftcrop = discord.ui.TextInput(label="left boundary",default_value = str(boundaries["left"]))
            self.rightcrop = discord.ui.TextInput(label="right boundary",default_value = str(boundaries["right"]))
            self.add_item(self.topcrop)
            self.add_item(self.bottomcrop)
            self.add_item(self.leftcrop)
            self.add_item(self.rightcrop)

        async def callback(self,interaction: discord.Interaction):
            await interaction.response.defer()
            boundaries = {"left": int(self.leftcrop.value),"top": int(self.topcrop.value), "right": int(self.rightcrop.value), "bottom": int(self.bottomcrop.value)}
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()

            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class TextInputModal(discord.ui.Modal):
        #def __init__(self,returnView: EditorView):
        def __init__(self, returnView):
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
            d = ImageDraw.Draw(self.img)

            # draw multiline text
            textconfig = {"font":fnt,"stroke_fill":(0,0,0),"stroke_width":self.img.size[0]//100,"fill":(255,255,255),"anchor":"mm"}
            d.multiline_text((self.img.size[0]/2, textsize), top, **textconfig)
            d.multiline_text((self.img.size[0]/2, self.img.size[1]-textsize), bottom, **textconfig)
            #d.multiline_text((self.img.size[0] / 2, self.img.size[1] - (self.img.size[1] // 10)), bottom, **textconfig)

            th = self.returnView.cog.makeThumbnail(self.img)

            await self.returnView.cog.show(interaction.message,th,self.filetype,self.returnView)


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
        await self.makeEditor(interaction, img)

    @discord.slash_command(name="imageditor",description="Image editor in development")
    async def imageeditorcommand(self,interaction: discord.Interaction, img: discord.Attachment = discord.SlashOption(name="image",description="The image to edit.",required=True)):
        await interaction.response.defer()
        await self.makeEditor(interaction,img)

    async def makeEditor(self, interaction: discord.Interaction, img: discord.Attachment):
        filetype = img.content_type.split("/")[1]
        image = await img.read()
        image = Image.open(BytesIO(image))
        th = self.makeThumbnail(image)
        viewObj = self.EditorView(self, interaction.message, image, filetype)
        message = await self.show(interaction, th, filetype, viewObj)
        viewObj.message = message

    def makeThumbnail(self,img: Image) -> Image:
        copy = img.copy()
        copy.thumbnail(THUMBNAIL_SIZE)
        return copy

    async def returnMenu(self, view: Union[CropView,CorrectionsView]):
        img = view.img
        ft = view.filetype
        th = self.makeThumbnail(img)
        viewObj = self.EditorView(self, view.message, img, ft)
        await self.show(view.message, img=th, filetype=ft, view=viewObj)

    async def show(self, interface: Union[discord.Interaction, discord.Message], img: Image, filetype: str, view: discord.ui.View = None) -> discord.Message:
        with BytesIO() as image_binary:
            img.save(image_binary, filetype)
            image_binary.seek(0)

            if isinstance(interface, discord.Interaction):
                msg = await interface.send(file=discord.File(fp=image_binary, filename=f'image.{filetype}'), view=view)

            elif isinstance(interface,discord.Message):
                msg = await interface.edit(file=discord.File(fp=image_binary, filename=f'image.{filetype}'), view=view)
            else:
                raise NotImplementedError("interface must be either discord.Interaction or discord.Message")
            return msg

def setup(client,baselogger):
    client.add_cog(PillowCog(client,baselogger))