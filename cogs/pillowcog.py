from io import BytesIO
from typing import Union, Tuple
import emoji
import nextcord as discord
from nextcord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

THUMBNAIL_SIZE = (720, 480)

#TODO add quality and speed options
#TODO check when right click, if bot has permission to that channel
#TODO highlighter
#TODO use layers, use dropdowns to select them and shit
#TODO make custom emojis

class PillowCog(commands.Cog):
    def __init__(self,client, baselogger): #TODO add some debug loggings?
        self.client = client

    class Selection:
        def __init__(self, img: Image, boundary: tuple):
            copy = img.copy()
            self.original = copy
            self.boundary = boundary
            self.image = copy.crop(self.boundary)

        def rotateBoundary(self): #rotating around selection center point
            w = self.image.width
            h = self.image.height
            oldpos = self.boundary
            newpos = (oldpos[0] + w / 2 - h / 2,
                      oldpos[1] + h / 2 - w / 2,
                      oldpos[2] - w / 2 + h / 2,
                      oldpos[3] - h / 2 + w / 2)
            self.boundary = tuple(map(int, newpos))

    class EditorView(discord.ui.View):
        def __init__(self, cog, message: discord.Message, image: Image, filetype: str):
            self.filetype = filetype
            self.cog = cog
            self.message = message
            self.img = image
            self.selection = None
            super().__init__()
            if not self.selection:
                self.children[4].disabled = True

        @discord.ui.button(label="Add Text", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":memo:"))
        async def texteditorbutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.TextInputModal(self))
            pass #edit text button modal, okbuttn, edit size select, edit font select, edit color select?, edit outline select?

        @discord.ui.button(label="Make selection", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':white_square_button:'))
        async def selectionbutton(self, button, interaction):
            await interaction.response.defer()
            viewObj = self.cog.SelectionView(self, self.selection)
            thumbnail = viewObj.drawBoundaries()
            await self.cog.show(interaction.message, thumbnail, self.filetype, view=viewObj)

        @discord.ui.button(label="Rotate/Flip", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':right_arrow_curving_left:'))
        async def rotatebutton(self, button, interaction):
            viewObj = self.cog.TransformView(self)
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Corrections", style=discord.ButtonStyle.gray,emoji=emoji.emojize(':level_slider:'),disabled=False)
        async def slidersbutton(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            viewObj = self.cog.CorrectionsView(self)
            await self.message.edit(view=viewObj) # contrast, saturation, brightness, hue?, gamma?

        @discord.ui.button(label="Crop", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':scissors:'))
        async def cropbutton(self, button, interaction):
            await interaction.response.defer()
            if self.selection is not None:
                self.img = self.selection.image
                self.selection = None
                thumbnail = self.cog.makeThumbnail(self)
                await self.cog.show(interaction.message, thumbnail, self.filetype, view=self)

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
        def __init__(self, returnView):
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message: discord.Message = returnView.message
            self.filetype = returnView.filetype
            super().__init__()
            #button for a modal to enter dimensions
            #select with aspect ratio options

    class FiltersDropdown(discord.ui.Select):
        def __init__(self, returnView):
            self.returnview = returnView
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            options = [discord.SelectOption(label="Deepfry"), discord.SelectOption(label="Blur"), discord.SelectOption(label="Invert"), discord.SelectOption(label="Cancel")]
            super().__init__(options=options)

        def deepfry(self, img):
            img = ImageEnhance.Contrast(img).enhance(2)
            img = ImageEnhance.Sharpness(img).enhance(2)
            img = ImageEnhance.Color(img).enhance(5)
            return img.effect_spread(distance=img.size[0])

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            if self.returnview.selection:
                toedit = self.returnview.selection.image
            else:
                toedit = self.img

            if self.values[0] == "Cancel":
                await self.message.edit(view=self.returnview)
                return
            elif self.values[0] == "Deepfry":
                toedit = self.deepfry(toedit)

            elif self.values[0] == "Blur":
                toedit = toedit.filter(ImageFilter.GaussianBlur(3))

            elif self.values[0] == "Invert":
                toedit = toedit.convert("RGB")#.point(lambda x: 255 - x)
                toedit = ImageOps.invert(toedit)

            if self.returnview.selection:
                self.returnview.img.paste(toedit, self.returnview.selection.boundary)
                self.returnview.selection.image = toedit
            else:
                self.returnview.img = toedit

            await self.cog.returnMenu(view=self.returnview)

    class CorrectionsView(discord.ui.View):
        def __init__(self, returnView, corrections: dict = None):
            self.returnview = returnView
            self.cog = returnView.cog
            self.img = returnView.img.copy()
            self.message = returnView.message
            self.filetype = returnView.filetype
            self.selection = returnView.selection
            self.corrections: dict = corrections or {"brightness": 100, "contrast": 100, "sharpness": 100, "saturation": 100}
            super().__init__()

        def applyCorrections(self, img: Image) -> Image:
            copy = img
            for corr, value in self.corrections.items():
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

        @discord.ui.button(label="Edit corrections", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":level_slider:", language="alias"))
        async def editcorrectionsbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.CorrectionsModal(self, self.corrections))

        @discord.ui.button(label="Done", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finalizecorrectbutton(self, button, interaction):
            await interaction.response.defer()
            if self.selection:
                self.selection.image = self.applyCorrections(self.selection.image)
                self.returnview.img.paste(self.selection.image, box=self.selection.boundary)
            else:
                self.returnview.img = self.applyCorrections(self.returnview.img)
            await self.cog.returnMenu(self.returnview)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"))
        async def canceleditbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.returnMenu(self.returnview)

    class CorrectionsModal(discord.ui.Modal):
        def __init__(self, returnView, corrections: dict = None):
            super().__init__(title="Image corrections (0-999)%")
            self.cog = returnView.cog
            self.filetype = returnView.filetype
            self.returnView = returnView
            self.selection = returnView.selection

            self.brightness = discord.ui.TextInput(label="Brightness", default_value=corrections["brightness"], min_length=1, max_length=3)
            self.contrast = discord.ui.TextInput(label="Contrast", default_value=corrections["contrast"], min_length=1, max_length=3)
            self.sharpness = discord.ui.TextInput(label="Sharpness", default_value=corrections["sharpness"], min_length=1, max_length=3)
            self.saturation = discord.ui.TextInput(label="Saturation", default_value=corrections["saturation"], min_length=1, max_length=3)

            for item in (self.brightness, self.contrast, self.sharpness, self.saturation):
                self.add_item(item)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                corrections = {"brightness": int(self.brightness.value) or 100, "contrast": int(self.contrast.value) or 100, "sharpness": int(self.sharpness.value) or 100, "saturation": int(self.saturation.value) or 100}
            except ValueError:
                await interaction.send("Input numbers only!",ephemeral=True)
                return
            self.returnView.corrections = corrections
            if self.selection:
                sel = self.returnView.applyCorrections(self.selection.image)
                self.returnView.img.paste(sel, box=self.selection.boundary)
                th = self.cog.makeThumbnail(self.returnView)
            else:
                th = self.cog.makeThumbnail(self.returnView)
                th = self.returnView.applyCorrections(th)
            await self.cog.show(interaction.message, th, self.filetype, view=self.returnView)

    class TransformView(discord.ui.View):
        def __init__(self, returnView):
            self.returnView = returnView
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message: discord.Message = returnView.message
            self.filetype = returnView.filetype
            self.selection = returnView.selection
            super().__init__()

        @discord.ui.button(label="Left", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_right_hook:", language="alias"))
        async def rotateleft(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if self.selection:
                self.img = self.returnView.img.copy()
                drawctx = ImageDraw.Draw(self.returnView.img)
                #drawctx.rectangle(self.selection.boundary,fill=(0, 0, 0))
                self.selection.rotateBoundary()
                self.selection.image = self.selection.image.transpose(method=Image.Transpose.ROTATE_90)
                self.returnView.img.paste(self.selection.image, box=self.selection.boundary)
            else:
                self.img = self.returnView.img.transpose(method=Image.Transpose.ROTATE_90)
            th = self.cog.makeThumbnail(self)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Right", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":leftwards_arrow_with_hook:", language="alias"))
        async def rotateright(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if self.selection:
                self.img = self.returnView.img.copy()
                drawctx = ImageDraw.Draw(self.img)
                #drawctx.rectangle(self.selection.boundary,fill=(0, 0, 0))
                self.selection.rotateBoundary()
                self.selection.image = self.selection.image.transpose(method=Image.Transpose.ROTATE_270)
                self.img.paste(self.selection.image, box=self.selection.boundary)
            else:
                self.img = self.img.transpose(method=Image.Transpose.ROTATE_270)
            th = self.cog.makeThumbnail(self)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Flip Horizont", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":left_right_arrow:", language="alias"))
        async def horizontalflip(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if self.selection:
                self.selection.image = self.selection.image.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
                self.returnView.img.paste(self.selection.image, box=self.selection.boundary)
            else:
                self.img = self.img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
            th = self.cog.makeThumbnail(self)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Flip Vertical", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_up_down:", language="alias"))
        async def verticalflip(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if self.selection:
                self.selection.image = self.selection.image.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
                self.returnView.img.paste(self.selection.image,box=self.selection.boundary)
            else:
                self.img = self.img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
            th = self.cog.makeThumbnail(self)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"),row=1)
        async def cancelflipbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.returnMenu(self.returnView)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"),row=1)
        async def finalizeflipbutton(self, button, interaction):
            await interaction.response.defer()
            self.returnView.img = self.img
            await self.message.edit(view=self.returnView) #no need to make a new thumbnail

    class SelectionView(discord.ui.View):
        def __init__(self, returnView, boundaries=None):
            self.cog = returnView.cog
            self.img = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            self.returnView = returnView
            self.boundaries = boundaries.boundary if boundaries else None#(0,0,self.img.width,self.img.height) # dont make this into an or
            super().__init__() #TODO maybe a rotate selection? not sure if needed, just rewrite the numbers yourself, along with flip H/V options

        def drawBoundaries(self):
            copy = self.img.copy()
            drawctx = ImageDraw.Draw(copy)

            #divisor lines every 100pxs
            for w in range(0,copy.width,100):
                drawctx.line(((w, 0), (w, copy.height)), fill=(255, 120, 255), width=2 if copy.width > 400 else 1)
            for h in range(0,copy.height,100):
                drawctx.line(((0, h), (copy.width, h)), fill=(255, 120, 255), width=1)

            #boundary lines
            if self.boundaries:
                drawctx.rectangle(self.boundaries,
                                  outline=(255, 125, 0),
                                  width=6 if copy.size[0] > 400 else 2)
            copy.thumbnail(THUMBNAIL_SIZE)
            return copy

        @discord.ui.button(label="Edit boundaries", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":white_square_button:",language="alias"))
        async def editboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.SelectionMakeModal(self.boundaries, self))

        @discord.ui.button(label="Move boundaries", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":left_right_arrow:", language="alias")) #TODO maybe make an emoji for this a 4 way arrow
        async def moveboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.SelectionMoveModal(self.boundaries, self))

        @discord.ui.button(label="Shrink/Expand", style=discord.ButtonStyle.gray,emoji=emoji.emojize(":arrow_up_down:", language="alias")) #TODO make emoji maybe 4 way arrow but roatetd 45 degrees
        async def expandboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.SelectionExpandModal(self.boundaries, self))

        @discord.ui.button(label="Deselect", style=discord.ButtonStyle.red, emoji=emoji.emojize(":white_square_button:"))
        async def deselbutton(self, button, interaction):
            self.boundaries = None
            thumbnail = self.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"), row=1)
        async def finalizeselectingbutton(self, button, interaction):
            if self.boundaries:
                try:
                    self.returnView.selection = self.cog.Selection(self.img, self.boundaries)
                    self.returnView.children[4].disabled = False  # enabling crop button
                except ValueError as e:
                    await interaction.send(e, delete_after=10)
                    return
            else:
                self.returnView.selection = None
                self.returnView.children[4].disabled = True  # disabling crop button

            await self.cog.returnMenu(self.returnView)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"), row=1)
        async def canceleditbutton(self, button, interaction):
            await self.cog.returnMenu(self.returnView)

    class SelectionMoveModal(discord.ui.Modal):
        def __init__(self,boundaries: Tuple[int, int, int, int], view):
            super().__init__(title="Move crop boundaries")
            self.boundaries = boundaries
            self.returnView = view

            self.leftcrop = discord.ui.TextInput(label="top left corner | [X] pixels from left", default_value=str(boundaries[0]))
            self.topcrop = discord.ui.TextInput(label="top left corner | [Y] pixels from top", default_value=str(boundaries[1]))
            self.add_item(self.leftcrop)
            self.add_item(self.topcrop)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            wmax = self.returnView.img.width
            hmax = self.returnView.img.height
            if self.boundaries is None:
                self.boundaries = (0, 0, self.returnView.img.width, self.returnView.img.height)
            boundary_width = int(self.boundaries[2])-int(self.boundaries[0])
            boundary_height = int(self.boundaries[3])-int(self.boundaries[1])
            try:
                boundaries = (max(0, int(self.leftcrop.value)), #left
                              max(0, int(self.topcrop.value)), #top
                              min(wmax, int(self.leftcrop.value)+boundary_width), #right
                              min(hmax, int(self.topcrop.value)+boundary_height)) #bottom
            except ValueError:
                await interaction.send("Input numbers only!",ephemeral=True)
                return
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class SelectionExpandModal(discord.ui.Modal):
        def __init__(self, boundaries: Tuple[int, int, int, int], view):
            super().__init__(title="Expand/Shrink crop boundaries")
            self.boundaries = boundaries
            self.returnView = view

            self.factor = discord.ui.TextInput(label="Expand (+) / Shrink (-)",default_value="0")
            self.add_item(self.factor)

        async def callback(self, interaction: discord.Interaction):
            factor = int(self.factor.value)
            wmax = self.returnView.img.width
            hmax = self.returnView.img.height
            await interaction.response.defer()
            if self.boundaries is None:
                self.boundaries = (0, 0, self.returnView.img.width, self.returnView.img.height)
            try:
                boundaries = (max(0, int(self.boundaries[0]) - factor),
                              max(0, int(self.boundaries[1]) - factor),
                              min(wmax, int(self.boundaries[2]) + factor),
                              min(hmax, int(self.boundaries[3]) + factor))
            except ValueError:
                await interaction.send("Input numbers only!",ephemeral=True)
                return
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class SelectionMakeModal(discord.ui.Modal):
        def __init__(self, boundaries: Tuple[int, int, int, int], view):
            super().__init__(title="Set selection boundaries")
            self.returnView = view
            boundaries = boundaries or (0, 0, self.returnView.img.width, self.returnView.img.height)
            self.topcrop = discord.ui.TextInput(label="top boundary", default_value=str(boundaries[1]))
            self.bottomcrop = discord.ui.TextInput(label="bottom boundary", default_value=str(boundaries[3]))
            self.leftcrop = discord.ui.TextInput(label="left boundary", default_value=str(boundaries[0]))
            self.rightcrop = discord.ui.TextInput(label="right boundary", default_value=str(boundaries[2]))
            self.add_item(self.topcrop)
            self.add_item(self.bottomcrop)
            self.add_item(self.leftcrop)
            self.add_item(self.rightcrop)

        async def callback(self,interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                boundaries = (int(self.leftcrop.value),
                              int(self.topcrop.value),
                              int(self.rightcrop.value),
                              int(self.bottomcrop.value))
            except ValueError:
                await interaction.send("Input numbers only!",ephemeral=True)
                return
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class TextInputModal(discord.ui.Modal):
        #def __init__(self,returnView: EditorView):
        def __init__(self, returnView):
            self.returnView = returnView

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
            if self.returnView.selection:
                d = ImageDraw.Draw(self.returnView.selection.image)
                img = self.returnView.selection.image
            else:
                d = ImageDraw.Draw(self.returnView.img)
                img = self.returnView.img

            mult = ((100 - (len(max(top, bottom, key=len))*2))/100)
            textsize = (img.width//10) * max(mult, 0.5)
            textsize = int(max(textsize, 20)) #todo devize an algorithm to determine optimal size
            fnt = ImageFont.truetype('impact.ttf', size=textsize) #TODO font select maybe? who knows maybe when modal dropdowns are available
            #fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 40)

            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width":img.width//100, "fill": (255, 255, 255), "anchor": "mm"}
            d.multiline_text((img.width/2, textsize), top, **textconfig)
            d.multiline_text((img.width/2, img.height-textsize), bottom, **textconfig)
            #d.multiline_text((self.img.size[0] / 2, self.img.size[1] - (self.img.size[1] // 10)), bottom, **textconfig)

            if self.returnView.selection:
                self.returnView.img.paste(self.returnView.selection.image, self.returnView.selection.boundary)

            await self.returnView.cog.returnMenu(self.returnView)

    @discord.message_command(name="Image editor")
    async def imeditor(self,interaction: discord.Interaction, msg: discord.Message):
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
    async def imageeditorcommand(self, interaction: discord.Interaction, img: discord.Attachment = discord.SlashOption(name="image", description="The image to edit.", required=True)):
        await interaction.response.defer()
        await self.makeEditor(interaction, img)

    async def makeEditor(self, interaction: discord.Interaction, img: discord.Attachment):
        filetype = img.content_type.split("/")[1]
        image = await img.read()
        image = Image.open(BytesIO(image))
        viewObj = self.EditorView(self, interaction.message, image, filetype)
        th = self.makeThumbnail(viewObj)
        message = await self.show(interaction, th, filetype, viewObj)
        viewObj.message = message

    def makeThumbnail(self,view) -> Image:
        if view.selection:
            return self.drawSelection(view.img,view.selection)
        copy = view.img.copy()
        copy.thumbnail(THUMBNAIL_SIZE)
        return copy

    def drawSelection(self,img: Image, sel: Selection) -> Image:
        copy = img.copy()
        drawctx = ImageDraw.Draw(copy)

        # boundary lines
        drawctx.rectangle(sel.boundary,
                          outline=(255, 125, 0),
                          width=6 if copy.size[0] > 400 else 2)
        copy.thumbnail(THUMBNAIL_SIZE)
        return copy

    async def returnMenu(self, view: Union[SelectionView, CorrectionsView, EditorView]):
        ft = view.filetype
        if view.selection:
            th = self.drawSelection(view.img, view.selection)
        else:
            th = self.makeThumbnail(view)
        await self.show(view.message, img=th, filetype=ft, view=view)

    async def show(self, interface: Union[discord.Interaction, discord.Message], img: Image, filetype: str, view: discord.ui.View = None) -> discord.Message:
        with BytesIO() as image_binary:
            img.save(image_binary, filetype)
            image_binary.seek(0)

            if isinstance(interface, discord.Interaction):
                msg = await interface.send(file=discord.File(fp=image_binary, filename=f'image.{filetype}'), view=view)

            elif isinstance(interface, discord.Message):
                msg = await interface.edit(file=discord.File(fp=image_binary, filename=f'image.{filetype}'), view=view)
            else:
                raise NotImplementedError("interface must be either discord.Interaction or discord.Message")
            return msg


def setup(client,baselogger):
    client.add_cog(PillowCog(client,baselogger))