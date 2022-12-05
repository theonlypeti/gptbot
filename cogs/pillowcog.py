from io import BytesIO
from logging import Logger
from math import ceil
from typing import Union, Tuple, List
import emoji
import nextcord as discord
from nextcord.ext import commands #remove in all cogs? used for prefix cmds
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

THUMBNAIL_SIZE = (720, 480)

#TODO add quality and speed options for the thumbnail (as in size)
#TODO check when right click, if bot has permission to that channel
#TODO highlighter effect
#TODO use layers, use dropdowns to select them and shit
#TODO make custom emojis for the buttons

class PillowCog(commands.Cog):
    def __init__(self, client, baselogger: Logger):
        global pillowlogger
        self.client = client
        pillowlogger = baselogger.getChild("pillowlogger")

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
            self.img: Image = image
            self.selection = None
            super().__init__()

        @discord.ui.button(label="Add Text", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":memo:"))
        async def texteditorbutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.TextInputModal(self))
            pass #edit text button modal, okbuttn, edit size select, edit font select, edit color select?, edit outline select?

        @discord.ui.button(label="Make selection", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':white_square_button:'))
        async def selectionbutton(self, button, interaction):
            await interaction.response.defer()
            viewObj = self.cog.SelectionView(self, self.selection)
            viewObj.add_item(self.cog.AspectRatioSelect(viewObj))
            thumbnail = viewObj.drawBoundaries()
            await self.cog.show(interaction.message, thumbnail, self.filetype, view=viewObj)

        @discord.ui.button(label="Rotate/Flip", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':right_arrow_curving_left:'))
        async def rotatebutton(self, button, interaction):
            viewObj = self.cog.TransformView(self)
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Corrections", style=discord.ButtonStyle.gray,emoji=emoji.emojize(':level_slider:'), disabled=False)
        async def slidersbutton(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            viewObj = self.cog.CorrectionsView(self)
            await self.message.edit(view=viewObj)  # contrast, saturation, brightness, hue?, gamma?

        @discord.ui.button(label="Crop", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':scissors:'))
        async def cropbutton(self, button, interaction):
            await interaction.response.defer()
            if self.selection is not None:
                self.img = self.selection.image
                self.selection = None
                thumbnail = self.cog.makeThumbnail(self)
                await self.cog.show(interaction.message, thumbnail, self.filetype, view=self)
            else:
                await interaction.send(embed=discord.Embed(description="Define a selection first using the **Make selection** button", color=discord.Color.red()), ephemeral=True)

        @discord.ui.button(label="Rescale", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':pinching_hand:'), disabled=True)
        async def resizebutton(self, button, interaction):
            pass  # modal buttons for height and width aspect ratio? but in pixels? and a select for common aspect ratios

        @discord.ui.button(label="Filters", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':smile:', language="alias"), disabled=False)
        async def filtersbutton(self, button, interaction):
            viewObj = discord.ui.View()
            viewObj.add_item(self.cog.FiltersDropdown(returnView=self))
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finishbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.show(self.message, self.img, self.filetype, view=None) #note to self, using interaction.message here would not work for some reason

        @discord.ui.button(label="Upload to", style=discord.ButtonStyle.green)#, emoji=emoji.emojize(":check_mark_button:"))
        async def uploadbutton(self, button, interaction):
            await interaction.response.defer()
            viewObj = self.cog.UploadView(self)
            th = self.img.copy()
            th.thumbnail(THUMBNAIL_SIZE) #dont want selection lines
            await self.cog.show(interaction.message, th, self.filetype, view=viewObj)

    class UploadView(discord.ui.View):
        def __init__(self, returnView):
            self.returnView = returnView
            self.selection = returnView.selection #used only for returning to previous menu
            self.cog = returnView.cog
            self.img = returnView.img
            super().__init__()

        @discord.ui.button(label="Upload as emote")
        async def uploademotebutton(self, button, interaction: discord.Interaction):
            modal = self.cog.NameEmoteModal(self, "single")
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Split as multiple emotes")
        async def splitemotesbutton(self, button, interaction: discord.Interaction):
            emotesneeded = ceil(self.img.width / 256) * ceil(self.img.height/256)
            if interaction.guild.emoji_limit - len(interaction.guild.emojis) < emotesneeded:
                await interaction.send(embed=discord.Embed(description=f"Not enough emote slots on this server. {emotesneeded} needed", color=discord.Color.red()), delete_after=15)
                return
            modal = self.cog.NameEmoteModal(self, "split")
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Upload as sticker")
        async def uploadstickerbutton(self, button, interaction: discord.Interaction):
            modal = self.cog.NameEmoteModal(self, "sticker")
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Upload as server pfp")
        async def uploadpfpbutton(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            with BytesIO() as image_binary:
                self.img.save(image_binary, "png")
                image_binary.seek(0)
                await interaction.guild.edit(icon=image_binary.read())

        @discord.ui.button(label="Cancel")
        async def canceluploadbutton(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            await self.cog.returnMenu(self.returnView)

    class NameEmoteModal(discord.ui.Modal):
        def __init__(self, view, mode: str):
            super().__init__(title=f"Name your {'emote' if mode != 'sticker' else 'sticker'}")
            self.mode = mode
            self.img = view.img
            self.emotename = discord.ui.TextInput(label=f"{'Emote' if mode != 'sticker' else 'Sticker'} name")
            self.add_item(self.emotename)
            self.emote = discord.ui.TextInput(label="Emoji for sticker (Win + .)")
            if mode == "sticker":  # im lazy to make 3 separate modals
                self.add_item(self.emote)

        async def callback(self, interaction: discord.Interaction):
            try:
                name = self.emotename.value
                if self.mode == "split":
                    await interaction.response.defer()
                    th, tw = 0, 0 #target height/width
                    while th < self.img.height: #ceil(self.height/256) * 256
                        th += 256
                    while tw < self.img.width:
                        tw += 256
                    ni = Image.new(self.img.mode, (tw, th), (0, 0, 0, 0)) #make a new image, size rounded to a multiple of 256, all empty pixels
                    ni.paste(self.img, (0, 0)) #original image anchored to top left
                    for h in range(0, th, 256):
                        nh = h + 256
                        for w in range(0, tw, 256):
                            nw = w + 256
                            em = ni.copy()
                            pillowlogger.debug(f"{h=},{w=},{nh=},{nw=}")
                            em = em.crop((w, h, nw, nh)) #TODO dont copy if doesnt modify orig image
                            with BytesIO() as image_binary:
                                em.save(image_binary, "png")
                                image_binary.seek(0)
                                await interaction.guild.create_custom_emoji(name=f"{name}_{h//256}_{w//256}", image=image_binary.read())

                elif self.mode == "sticker":
                    await interaction.response.defer()
                    emote = self.emote.value
                    if not emoji.is_emoji(emote) and not emoji.is_emoji(emote := emoji.emojize(f":{emote.strip(':')}:", language="alias")):
                        pillowlogger.debug(emote)
                        await interaction.send(embed=discord.Embed(description="You need to supply a default emoji.", color=discord.Color.red()))
                        return
                    em = self.img.copy()
                    em.thumbnail((320, 320))
                    with BytesIO() as image_binary:
                        em.save(image_binary, "PNG")
                        image_binary.seek(0)
                        await interaction.guild.create_sticker(name=name, emoji=emoji.demojize(emote, language="alias", delimiters=("", "")), file=discord.File(image_binary))

                else:
                    await interaction.response.defer()
                    em = self.img.copy()
                    em.thumbnail((256, 256))
                    with BytesIO() as image_binary:
                        em.save(image_binary, "png")
                        image_binary.seek(0)
                        await interaction.guild.create_custom_emoji(name=name, image=image_binary.read())
            except discord.Forbidden:
                await interaction.send(embed=discord.Embed(description="The bot does not have manage server or manage emojis permissions.", color=discord.Color.red()))
            except discord.HTTPException as e:
                pillowlogger.error(f"{e}")
                await interaction.send(f"{e}")

    class RescaleView(discord.ui.View):
        def __init__(self, returnView):
            self.cog = returnView.cog
            self.img: Image = returnView.img
            self.message: discord.Message = returnView.message
            self.filetype = returnView.filetype
            super().__init__()
            #button for a modal to enter dimensions
            #select with aspect ratio options

    class FiltersDropdown(discord.ui.Select): #TODO add flowers filter
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
                await self.cog.returnMenu(view=self.returnview)
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
                await interaction.send("Input numbers only!", ephemeral=True)
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
                self.selection.rotateBoundary()
                self.selection.image = self.selection.image.transpose(method=Image.Transpose.ROTATE_90)
                self.img.paste(self.selection.image, box=self.selection.boundary)
            else:
                self.img = self.img.transpose(method=Image.Transpose.ROTATE_90)
            th = self.cog.makeThumbnail(self)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Right", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":leftwards_arrow_with_hook:", language="alias"))
        async def rotateright(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            if self.selection:
                self.img = self.returnView.img.copy()
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
                self.returnView.img.paste(self.selection.image, box=self.selection.boundary)
            else:
                self.img = self.img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
            th = self.cog.makeThumbnail(self)
            await self.cog.show(interaction.message, th, self.filetype, view=self)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"), row=1)
        async def cancelflipbutton(self, button, interaction):
            await interaction.response.defer()
            await self.cog.returnMenu(self.returnView)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"), row=1)
        async def finalizeflipbutton(self, button, interaction):
            await interaction.response.defer()
            self.returnView.img = self.img
            await self.message.edit(view=self.returnView) #no need to make a new thumbnail #TODO maybe cache thumbnails? i dont know if its a good idea to keep the images saved hashtag gdpr

    class SelectionView(discord.ui.View):
        def __init__(self, returnView, boundaries=None):
            self.cog = returnView.cog
            self.img = returnView.img
            self.message = returnView.message
            self.filetype = returnView.filetype
            self.returnView = returnView
            self.boundaries = boundaries.boundary if boundaries else None#(0,0,self.img.width,self.img.height) # dont make this into an or
            super().__init__()

        def drawBoundaries(self):
            copy = self.img.copy()
            drawctx = ImageDraw.Draw(copy)

            #divisor lines every 100pxs
            for w in range(0, copy.width, 100):
                drawctx.line(((w, 0), (w, copy.height)), fill=(255, 120, 255), width=2 if copy.width > 400 else 1)
            for h in range(0, copy.height, 100):
                drawctx.line(((0, h), (copy.width, h)), fill=(255, 120, 255), width=2 if copy.width > 400 else 1)

            #boundary lines
            if self.boundaries:
                bsize = 6 if copy.size[0] > 400 else 2
                drawctx.rectangle(self.boundaries,
                                  outline=(255, 125, 0),
                                  width=bsize)
            copy.thumbnail(THUMBNAIL_SIZE)
            return copy

        @discord.ui.button(label="Edit boundaries", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":white_square_button:", language="alias"))
        async def editboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.SelectionMakeModal(self.boundaries, self))

        @discord.ui.button(label="Move boundaries", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":left_right_arrow:", language="alias")) #TODO maybe make an emoji for this a 4 way arrow
        async def moveboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.SelectionMoveModal(self.boundaries, self))

        @discord.ui.button(label="Shrink/Expand", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_up_down:", language="alias")) #TODO make emoji maybe 4 way arrow but roatetd 45 degrees
        async def expandboundariesbutton(self, button, interaction: discord.Interaction):
            await interaction.response.send_modal(self.cog.SelectionExpandModal(self.boundaries, self))

        @discord.ui.button(label="Deselect", style=discord.ButtonStyle.red, emoji=emoji.emojize(":white_square_button:"), row=2)
        async def deselbutton(self, button, interaction):
            self.boundaries = None
            thumbnail = self.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self)

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"), row=2)
        async def finalizeselectingbutton(self, button, interaction):
            if self.boundaries:
                try:
                    self.returnView.selection = self.cog.Selection(self.img, self.boundaries)
                    self.returnView.children[4].disabled = False  # enabling crop button #TODO redo this with custom_id so if i move the buttons this would still work
                except ValueError as e:
                    await interaction.send(e, delete_after=10)
                    return
            else:
                self.returnView.selection = None
                self.returnView.children[4].disabled = True  # disabling crop button

            await self.cog.returnMenu(self.returnView)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji=emoji.emojize(":cross_mark:"), row=2)
        async def canceleditingbutton(self, button, interaction):
            await self.cog.returnMenu(self.returnView)

    class AspectRatioSelect(discord.ui.Select):
        def __init__(self, returnView):
            self.returnView = returnView
            opts = [discord.SelectOption(label=i) for i in ("16:9","9:16","4:3","3:4","21:9","9:21","32:9","9:32","3:2","2:3","1:1")]
            super().__init__(options=opts, placeholder="Select a ratio")

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            w, h = self.returnView.img.size  #glossary: nw,nh=new width/height;asp,nasp= (new) aspect ratio; hdiff,wdiff = height/width difference;
            nw, nh = map(int, self.values[0].split(":"))
            asp, nasp = h/w, nh/nw
            pillowlogger.debug(f"{w=},{h=},,{nh=},{nw=},,{asp=},{nasp=}")
            if asp > nasp:  # crop from top/bottom
                nh = h/asp
                nh *= nasp
                nw = w
            elif asp < nasp:  # crop from sides
                nw = w/nasp
                nw *= asp
                nh = h
            hdiff = (h-nh)/2
            wdiff = (w-nw)/2
            top = hdiff
            left = wdiff
            bottom = h - hdiff
            right = w - wdiff
            pillowlogger.debug(f"{w=},{h=},,{nh=},{nw=},,{asp=},{nasp=}")
            pillowlogger.debug(f"{top=},{left=},{bottom=},{right=}")
            self.returnView.selection = ()
            boundaries = (int(left), int(top), int(right), int(bottom))
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class SelectionMoveModal(discord.ui.Modal):
        def __init__(self, boundaries: Tuple[int, int, int, int], returnView):
            super().__init__(title="Move crop boundaries")
            self.boundaries = boundaries
            self.returnView = returnView

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
                await interaction.send("Input numbers only!", ephemeral=True)
                return
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class SelectionExpandModal(discord.ui.Modal):
        def __init__(self, boundaries: Tuple[int, int, int, int], view):
            super().__init__(title="Expand/Shrink crop boundaries")
            self.boundaries = boundaries
            self.returnView = view

            self.factor = discord.ui.TextInput(label="Expand (+) / Shrink (-)", default_value="0")
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
                await interaction.send("Input numbers only!", ephemeral=True)
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

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                boundaries = (int(self.leftcrop.value),
                              int(self.topcrop.value),
                              int(self.rightcrop.value),
                              int(self.bottomcrop.value))
            except ValueError:
                await interaction.send("Input numbers only!", ephemeral=True)
                return
            self.returnView.boundaries = boundaries
            thumbnail = self.returnView.drawBoundaries()
            await self.returnView.cog.show(interaction.message, thumbnail, self.returnView.filetype, self.returnView)

    class TextInputModal(discord.ui.Modal):
        def __init__(self, returnView):
            self.returnView = returnView

            super().__init__(title="Add text to your image")
            self.toptext = discord.ui.TextInput(label="Top Text", required=False, style=discord.TextInputStyle.short)
            self.add_item(self.toptext)
            self.bottomtext = discord.ui.TextInput(label="Bottom Text", required=False)
            self.add_item(self.bottomtext)

        async def callback(self, interaction: discord.Interaction):
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

            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width//100, "fill": (255, 255, 255), "anchor": "mm"}
            d.multiline_text((img.width/2, textsize), top, **textconfig)
            d.multiline_text((img.width/2, img.height-textsize), bottom, **textconfig)
            #d.multiline_text((self.img.size[0] / 2, self.img.size[1] - (self.img.size[1] // 10)), bottom, **textconfig)

            if self.returnView.selection:
                self.returnView.img.paste(self.returnView.selection.image, self.returnView.selection.boundary)

            await self.returnView.cog.returnMenu(self.returnView)

    class AttachmentSelectDropdown(discord.ui.Select):
        def __init__(self, attachments: List[discord.Attachment], cog):
            self.cog = cog
            self.attachments = attachments
            opts = [discord.SelectOption(label=i.filename, value=str(n)) for n, i in enumerate(attachments)]
            super().__init__(options=opts, placeholder="Select an image to edit")

        async def callback(self, interaction: discord.Interaction):
            val = int(self.values[0])
            await self.cog.makeEditor(interaction.message, self.attachments[val])

    @discord.message_command(name="Image editor")
    async def imeditor(self, interaction: discord.Interaction, msg: discord.Message):
        await interaction.response.defer()
        if not msg.attachments:
            if "https:" in msg.content:
                if msg.content.startswith("https://cdn.discordapp.com/attachments"): #or imgur
                    pass  #todo
                else:
                    pass  #todo
            return
        elif len(msg.attachments) > 1:
            viewObj = discord.ui.View()
            viewObj.add_item(self.AttachmentSelectDropdown(attachments=msg.attachments, cog=self))
            await interaction.send(view=viewObj)
        else:
            img = msg.attachments[0]
            await self.makeEditor(interaction, img)

    @discord.slash_command(name="imageditor", description="Image editor in development")
    async def imageeditorcommand(self, interaction: discord.Interaction, img: discord.Attachment = discord.SlashOption(name="image", description="The image to edit.", required=True)):
        await interaction.response.defer()
        await self.makeEditor(interaction, img)

    async def makeEditor(self, interaction: discord.Interaction | discord.Message, img: discord.Attachment):
        filetype = img.content_type.split("/")[1]
        image = await img.read()
        image = Image.open(BytesIO(image)) #invalid start byte
        msg = interaction.message if isinstance(interaction, discord.Interaction) else interaction
        viewObj = self.EditorView(self, msg, image, filetype)
        th = self.makeThumbnail(viewObj)
        message = await self.show(interaction, th, filetype, viewObj)
        viewObj.message = message

    def makeThumbnail(self, view: EditorView) -> Image:
        if view.selection:
            return self.drawSelection(view.img, view.selection)
        copy = view.img.copy()
        copy.thumbnail(THUMBNAIL_SIZE)
        return copy

    def drawSelection(self, img: Image, sel: Selection) -> Image:
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


def setup(client, baselogger):
    client.add_cog(PillowCog(client, baselogger))
