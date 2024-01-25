import asyncio
import os
import re
from copy import deepcopy
from datetime import datetime, timedelta
from moviepy.video.io.VideoFileClip import VideoFileClip, VideoClip
from moviepy.video.fx.resize import resize
from moviepy.video.fx.speedx import speedx
from multiprocessing import cpu_count
import concurrent.futures
from io import BytesIO
import aiohttp
import emoji
import nextcord as discord
from nextcord import Interaction
from nextcord.ext import commands
import utils.embedutil
# from rembg import remove
import tempfile
import time as time_module


def writevid(mov: str, filename: str, target_filesize: int = 25000, info: dict = None):
    if info is None:
        info = {}
    start = info.get("start", None)
    end = info.get("end", None)
    speed = info.get("speed", None)
    size: tuple[int, int] | None = info.get("size", None)
    mute = info.get("mute", False)

    print(f"{start=}")
    print(f"{end=}")
    print(f"{speed=}")
    print(f"{size=}")

    with VideoFileClip(mov) as subclip:

        if start or end:
            subclip: VideoClip = subclip.subclip(start, end)
        dur = subclip.duration

        if speed and speed != 1:
            subclip = subclip.fx(speedx, speed)
        params: list = "-c:v h264_nvenc".split(" ")
        if size:
            params.extend(['-s', f"{size[0]}x{size[1]}"])

        if mute:
            params.extend(['-an'])
        # subclip.resize(width=size[0], height=size[1])
        # subclip = subclip.fx(resize, width=size[0], height=size[1])
        print(subclip.size)
        # if 0.5 < asp < 0.6:
        #     self.logger.debug("9:16 aspect ratio")
        #     params.extend(['-aspect', '9:16']) # i dont know what about this
        orig_bitrate = ((os.path.getsize(mov) / dur) * 8) // 1000
        bitrate_kbps = (target_filesize // dur) * 8


        print(f"orig bitrate: {orig_bitrate} kbps")
        print(f"target filesize: {target_filesize} kbps")
        print(f"target bitrate: {bitrate_kbps} kbps")

        bitrate: int | None = info.get("bitrate", bitrate_kbps)
        bitrate_kbps = min(bitrate, bitrate_kbps, orig_bitrate)

        subclip.write_videofile(filename, fps=subclip.fps, bitrate=f"{bitrate_kbps}k",
                                audio_bitrate="64k",
                                threads=cpu_count()-1, ffmpeg_params=params, codec='h264_nvenc')
        return "done"




THUMBNAIL_SIZE = (720, 480)


class VideoCog(commands.Cog):
    def __init__(self, client):
        global logger
        self.client = client
        logger = client.logger.getChild(f"{__name__}logger")
        self.files = []

    class EditorView(discord.ui.View):
        def __init__(self, cog, message: discord.Message, filename: str, filetype: str, info: dict):
            self.filetype = filetype
            self.cog: VideoCog = cog
            self.message = message
            self.vid: str = filename
            # self.selection = None
            self.info = info
            super().__init__(timeout=3600)

        @discord.ui.button(label="Add Text", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":memo:"), disabled=True)
        async def texteditorbutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.TextInputModal(self))
            pass #edit text button modal, okbuttn, edit size select, edit font select, edit color select?, edit outline select?

        @discord.ui.button(label="Mute", style=discord.ButtonStyle.gray, emoji=emoji.emojize(":loud_sound:", language="alias"), disabled=False)
        async def mutebutton(self, button: discord.ui.Button, interaction):
            self.info["mute"] = not self.info.get("mute", False)
            button.emoji = emoji.emojize(":mute:", language="alias") if self.info.get("mute", False) else emoji.emojize(":loud_sound:", language="alias")
            await self.showinfo()
            await self.message.edit(view=self)

        @discord.ui.button(label="Trim video", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':scissors:'))
        async def selectionbutton(self, button, interaction):
            await interaction.response.defer()
            viewObj = self.cog.TrimView(self)
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Rotate/Flip", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':right_arrow_curving_left:'), disabled=True)
        async def rotatebutton(self, button, interaction):
            viewObj = self.cog.TransformView(self)
            await self.message.edit(view=viewObj)

        @discord.ui.button(label="Bitrate", style=discord.ButtonStyle.gray, emoji=None, disabled=False)
        async def bitratebutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.BitrateModal(self))

        @discord.ui.button(label="Corrections", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':level_slider:'), disabled=True)
        async def slidersbutton(self, button, interaction: discord.Interaction):
            # await interaction.response.defer()
            viewObj = self.cog.CorrectionsView(self)
            await self.message.edit(view=viewObj)  # contrast, saturation, brightness, hue?, gamma?

        @discord.ui.button(label="Crop", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':white_square_button:'), disabled=True, custom_id="cropbutton")
        async def cropbutton(self, button, interaction):
            await interaction.response.defer()
            if self.selection is not None:
                self.img = self.selection.image
                self.selection = None
                thumbnail = self.cog.makeThumbnail(self)
                await self.cog.show(interaction.message, thumbnail, self.filetype, view=self)
            else:
                await interaction.send(embed=discord.Embed(description="Define a selection first using the **Make selection** button", color=discord.Color.red()), ephemeral=True)

        @discord.ui.button(label="Rescale", style=discord.ButtonStyle.gray, emoji=emoji.emojize(':pinching_hand:'), disabled=False)
        async def resizebutton(self, button, interaction):
            await interaction.response.send_modal(self.cog.ResizeModal(returnView=self))
            #TODO modal buttons for height and width aspect ratio? but in pixels? and a select for common aspect ratios

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, emoji=emoji.emojize(":check_mark_button:"))
        async def finishbutton(self, button, interaction: discord.Interaction):
            await interaction.response.defer()
            await self.sendmovie(interaction, self.message, self.vid, filesize_lim=interaction.guild.filesize_limit // 1000 - 500)

        async def sendmovie(self, interaction: discord.Interaction,msg: discord.Message, vid: str, filesize_lim: int = None):
            newfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir="./tempdata")
            newfile.close()

            start = time_module.perf_counter()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                try:
                    size_kb = filesize_lim or interaction.guild.filesize_limit // 1000 - 500
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(pool, writevid, vid, newfile.name, size_kb, self.info),
                        timeout=3600)
                except TimeoutError:
                    await utils.embedutil.error(interaction, "Timeout error, try again!")

            logger.debug(f"{time_module.perf_counter() - start}s nvenc run time")

            await utils.embedutil.success(interaction, "Your video is being sent! This may take some time!", delete=30)
            start = time_module.perf_counter()

            logger.warning(f"filesize: {os.path.getsize(newfile.name) // 1024} kB")
            logger.warning(f"filesize: {os.path.getsize(newfile.name) // 1024 / 1024} MB")

            try:
                if os.path.getsize(newfile.name) > interaction.guild.filesize_limit:
                    raise ValueError("too big")
                await self.cog.show(msg, newfile.name, "mp4")
            except (asyncio.TimeoutError, ValueError) as e:
                logger.warning(e)
                await utils.embedutil.error(interaction, "Shucks, the filesize is too big! Let me try again!")
                await self.sendmovie(interaction, msg, vid, filesize_lim=size_kb - 250)
            logger.debug(f"{time_module.perf_counter() - start}s send time")

            # subclip.close()
            # os.close(vid.fileno())
            os.remove(newfile.name)
            return "done"

        async def on_timeout(self) -> None:
            """Called when the paginator times out."""
            for ch in self.children:
                ch.disabled = True
            await self.message.edit(view=self)
            os.unlink(self.vid)
            self.cog.files.remove(self.vid)

        async def showinfo(self, info: dict = None): #TODO make normal info embed
            if not info:
                info = self.info
            await self.message.edit(
                embed=discord.Embed(
                    title="Video editor",
                    description=f"""
                                **Start:** {timedelta(seconds=info['start'])}
                                **End:** {timedelta(seconds=info['end'])}
                                **Duration:** {timedelta(seconds=info['duration'])}
                                **Size:** {info['size'][0]}x{info['size'][1]}
                                **Filesize:** {info['filesize']}
                                **Bitrate:** {info['bitrate']} kbps
                                **Speed:** {info['speed']}x
                                **Mute:** {info['mute']}
                                """,
                    color=discord.Color.green()),
            )

    class AttachmentSelectDropdown(discord.ui.Select):
        def __init__(self, attachments: list[discord.Attachment] | dict[str, BytesIO], cog):
            self.cog: VideoCog = cog
            if isinstance(attachments, dict):
                self.attachments = attachments.values()
                opts = [discord.SelectOption(label=i[:100], value=str(n)) for n, i in enumerate(attachments.keys())]
            else:
                self.attachments = attachments
                opts = [discord.SelectOption(label=i.filename, value=str(n)) for n, i in enumerate(attachments)]
            super().__init__(options=opts, placeholder="Select a video to edit")

        async def callback(self, interaction: discord.Interaction):
            val = int(self.values[0])
            await self.cog.makeEditor(interaction.message, (val, self.attachments[val]))

    async def filter_images(self, urls: list[str]) -> dict[str, BytesIO]:
        imgs = dict()
        async with aiohttp.ClientSession() as session:
            for url in urls:
                async with session.head(url) as response:
                    content_type = response.headers['Content-Type']
                    if content_type.startswith('video/'):
                        async with session.get(url) as res:
                            imgs[url] = BytesIO(await res.read())
        return imgs

    @discord.message_command(name="Video editor")
    async def videditor(self, interaction: discord.Interaction, msg: discord.Message):
        await interaction.response.defer()
        if not msg.attachments:
            url_regex = 'http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            # Find matches
            vidlinks: list[str] = re.findall(url_regex, msg.content)
            vids = await self.filter_images(vidlinks)
            if not vids:
                await utils.embedutil.error(interaction, "No links found in this message.")
                return
        else:
            vids = msg.attachments
        logger.debug(vids)
        if len(vids) > 1:
            viewObj = discord.ui.View()
            viewObj.add_item(self.AttachmentSelectDropdown(attachments=vids, cog=self))
            await interaction.send(view=viewObj)
        else:
            if isinstance(vids, dict):
                vid = list(vids.items())[0]
            else:
                vid = vids[0]
            await self.makeEditor(interaction, vid)

    @discord.slash_command(name="videoeditor", description="Video editor in development")
    async def videoeditorcommand(self, interaction: discord.Interaction, img: discord.Attachment = discord.SlashOption(name="image", description="The image to edit.", required=True)):
        await interaction.response.defer()
        await self.makeEditor(interaction, img)

    async def makeEditor(self, interaction: discord.Interaction | discord.Message, vid: discord.Attachment | tuple[str, BytesIO]):
        if isinstance(vid, discord.Attachment):
            vidf = BytesIO(await vid.read())
            url = vid.url
        else:
            vidf = vid[1]
            url = vid[0]
            ...
        os.makedirs("./tempdata", exist_ok=True)
        file = tempfile.NamedTemporaryFile(delete=False, dir="./tempdata", suffix=".mp4")
        file.write(vidf.read())
        file.close()
        logger.debug(file.name)
        self.files.append(file.name)
        with VideoFileClip(file.name) as vidf:
            duration = vidf.duration
            size = vidf.size
            filesize = os.path.getsize(file.name)
            info = {
                "start": 0,
                "end": duration,
                "duration": duration,
                "size": size,
                "filesize": f"{filesize // 1024} kB",
                "speed": 1,
                "mute": False,
                "bitrate": ((filesize // 1024) // duration) * 8
            }
        filetype = "mp4" #TODO uh?
        msg = interaction.message if isinstance(interaction, discord.Interaction) else interaction
        # logger.info(f"{filetype=}")
        viewObj = self.EditorView(self, msg, file.name, filetype, info)
        # th = self.makeThumbnail(viewObj)
        message = await self.show(interaction, url, filetype, viewObj)
        viewObj.message = message
        await viewObj.showinfo()

    async def returnMenu(self, view: EditorView):
        await self.show(view.message, filename=view.vid, filetype=view.filetype, view=view)

    async def show(self, interface: discord.Interaction | discord.Message, filename: str, filetype: str, view: discord.ui.View = None) -> discord.Message:

        if filename.startswith("https://"):
            content = filename
        else:
            content = None
        if isinstance(interface, discord.Interaction):
            msg = await interface.send(content=content, view=view)
            # msg = await interface.send(content=content, file=discord.File(fp=filename, filename=f'video.{filetype}') if not content else None, view=view)

        elif isinstance(interface, discord.Message):
            msg = await interface.edit(content=content, file=discord.File(fp=filename, filename=f'video.{filetype}') if not content else None, view=view)
        else:
            raise NotImplementedError("interface must be either discord.Interaction or discord.Message")
        logger.debug("shown")
        return msg

    class TrimView(discord.ui.View):
        def __init__(self, view: "VideoCog.EditorView"):
            super().__init__(timeout=float(view.timeout))
            self.view = view
            self.info = deepcopy(view.info)

        @discord.ui.button(label="Edit start/end", style=discord.ButtonStyle.gray)
        async def editbutton(self, button, interaction):
            await interaction.response.send_modal(self.view.cog.EditModal(self.view))

        @discord.ui.button(label="Finish", style=discord.ButtonStyle.green)
        async def finishbutton(self, button, interaction):
            # self.view.info
            logger.info(self.view.info)
            logger.info(self.info)
            # self.view.info = self.info
            logger.info(self.view.info)
            await self.view.showinfo() #TODO make return embed
            await self.view.message.edit(view=self.view)
            self.view.cog.files.remove(self.view.vid)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancelbutton(self, button, interaction):
            await self.view.showinfo()
            await self.view.message.edit(view=self.view)

    class ResizeModal(discord.ui.Modal):
        def __init__(self, returnView: "VideoCog.EditorView"):
            self.returnView = returnView
            self.w = returnView.info["size"][0]
            self.h = returnView.info["size"][1]

            super().__init__(title="Resize the video")
            self.widthbox = discord.ui.TextInput(label="Width (leave one dimension blank)", required=False, style=discord.TextInputStyle.short, placeholder=self.w)
            self.add_item(self.widthbox)
            self.heightbox = discord.ui.TextInput(label="Height (to retain aspect ratio)", required=False, placeholder=self.h)
            self.add_item(self.heightbox)

        async def callback(self, interaction: discord.Interaction):
            if not self.widthbox.value and not self.heightbox.value:
                return
            try:
                if self.widthbox.value:
                    assert int(self.widthbox.value) > 0
                if self.heightbox.value:
                    assert int(self.heightbox.value) > 0
            except AssertionError:
                await utils.embedutil.error(interaction, "Input numbers only!")
                return
            await interaction.response.defer()

            aspectratio = self.h/self.w
            if self.widthbox.value:
                neww = int(self.widthbox.value)
            else:
                neww = int(int(self.heightbox.value)*(1/aspectratio))

            if self.heightbox.value:
                newh = int(self.heightbox.value)
            else:
                newh = int(self.widthbox.value)*aspectratio
            logger.info(self.returnView.info)
            self.returnView.info["size"] = [neww, newh]

            await self.returnView.showinfo()
            await self.returnView.message.edit(view=self.returnView)

    class EditModal(discord.ui.Modal):
        def __init__(self, view: "VideoCog.EditorView"):
            super().__init__(timeout=float(view.timeout), title="Edit video start/end")
            self.view = view
            self.info = deepcopy(view.info)
            self.start = self.info.get("start", 0)
            self.end = self.info.get("end", self.info.get("duration", 0))
            self.speed = self.info.get("speed", 1)

            self.intime = discord.ui.TextInput(label="Start time", placeholder="hh:mm:ss", default_value=str(timedelta(seconds=self.start)))
            self.outtime = discord.ui.TextInput(label="End time", placeholder="hh:mm:ss", default_value=str(timedelta(seconds=self.end)))
            self.speedin = discord.ui.TextInput(label="Clip speed", placeholder="number", default_value=str(self.speed))
            self.add_item(self.intime)
            self.add_item(self.outtime)
            self.add_item(self.speedin)

        async def callback(self, interaction: Interaction) -> None:
            start = self.intime.value
            end = self.outtime.value
            speed = self.speedin.value

            try:
                start = datetime.strptime(start, "%H:%M:%S")
            except ValueError:
                start = datetime.strptime(start, "%H:%M:%S:%f")
            self.start = timedelta(hours=start.hour, minutes=start.minute, seconds=start.second).total_seconds()

            try:
                end = datetime.strptime(end, "%H:%M:%S")
            except ValueError:
                end = datetime.strptime(end, "%H:%M:%S:%f")
            self.end = timedelta(hours=end.hour, minutes=end.minute, seconds=end.second).total_seconds()

            self.speed = float(speed)

            self.info["start"] = self.start
            self.info["end"] = self.end
            self.info["speed"] = self.speed
            self.info["duration"] = (self.end - self.start) / self.speed
            self.info["filesize"] = f"~{(self.info['bitrate'] * self.info['duration']) / 8} kB"
            logger.info(self.info)
            logger.info(self.view.info)
            self.view.info = self.info
            logger.info(self.view.info)
            await self.view.showinfo(self.info)

    class BitrateModal(discord.ui.Modal):
        def __init__(self, view):
            super().__init__(title="Edit video bitrate")
            self.view = view

            self.bitrate = view.info.get("bitrate", 0)
            self.bitratein = discord.ui.TextInput(label="Bitrate", placeholder="kbps", default_value=str(self.bitrate))
            self.add_item(self.bitratein)

        async def callback(self, interaction: Interaction) -> None:
            bitrate = self.bitratein.value
            try:
                bitrate = int(bitrate)
            except ValueError:
                await utils.embedutil.error(interaction, "Input numbers only!")
                return
            self.bitrate = bitrate
            self.view.info["bitrate"] = self.bitrate
            self.view.info["filesize"] = f"~{(self.bitrate * self.view.info['duration']) / 8} kB"
            await self.view.showinfo()
            await self.view.message.edit(view=self.view)

    def cog_unload(self):
        logger.info("Removing any leftover videoeditor files..")
        for f in os.listdir("./tempdata"):
            try:
                os.unlink(rf"./tempdata/{f}")
            except Exception as e:
                logger.warning(e.__class__.__name__)
                logger.warning(e)


def setup(client):
    client.add_cog(VideoCog(client))
