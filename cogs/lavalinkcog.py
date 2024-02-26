"""A simple example of using Mafic."""
from __future__ import annotations
import subprocess
import asyncio
import os
import time
import traceback
from datetime import timedelta, datetime
from typing import TYPE_CHECKING, Any
from mafic import NodePool, Player, Playlist, Track, TrackEndEvent
import nextcord as discord
from nextcord.ext import commands
from nextcord.ext import tasks

import utils.embedutil

if TYPE_CHECKING:
    from nextcord.abc import Connectable


class MyPlayer(Player[discord.Client]):
    def __init__(self, client: discord.Client, channel: Connectable) -> None:
        super().__init__(client, channel)

        # Mafic does not provide a queue system right now, low priority.
        self.queue: list[tuple[discord.User, Track]] = []
        self.addedby: discord.User|None = None


class LavaLinkCog(commands.Cog):
    def __init__(self, client) -> None:
        self.client: discord.Client = client
        self.ready_ran = False
        self.pool = NodePool(self.client)
        self.logger = client.logger.getChild(f"{self.__module__}")
        self.on_ready.start()
        self.players: dict[int, MyPlayer] = {}

    @tasks.loop(count=1)
    async def on_ready(self):
        self.logger.debug("Creating lavalink node.")
        if self.ready_ran:
            self.logger.info("Lavalink node on.")
            return
        await self.pool.create_node(
            host="127.0.0.1",
            port=2333,
            # port=8080,
            label="MAIN",
            password="haha",
        )
        self.logger.info("Created lavalink node.")
        self.ready_ran = True

    @on_ready.before_loop
    async def start_lavalink(self):
        self.logger.info("Starting lavalink.")
        self.client.lavalink = subprocess.Popen(['java', '-jar', 'Lavalink.jar'], cwd=r'./lavalink')
        await asyncio.sleep(10)
        self.logger.info("Lavalink started.")

    @discord.slash_command(name="yt", dm_permission=False)
    async def ytgroup(self, interaction):
        pass

    @ytgroup.subcommand()
    async def join(self, inter: discord.Interaction[discord.Client]):
        """Join your voice channel."""
        assert isinstance(inter.user, discord.Member)

        if not inter.user.voice or not inter.user.voice.channel:
            await utils.embedutil.error(inter, "You are not in a voice channel.")
            return

        channel = inter.user.voice.channel

        # This apparently **must** only be `Client`.
        vc = await channel.connect(cls=MyPlayer)  # pyright: ignore[reportGeneralTypeIssues]
        try:
            await vc.guild.change_voice_state(self_deaf=True, channel=vc.channel)
        except TypeError:
            pass
        self.players.update({inter.guild.id: inter.guild.voice_client})
        await inter.send(f"Joined {channel.mention}.")

    @ytgroup.subcommand()
    async def play(self, inter: discord.Interaction[discord.Client], query: str):
        """Play a song.

        query:
            The song to search or play.
        """
        assert inter.guild is not None

        if not inter.user.voice or not inter.user.voice.channel:
            await utils.embedutil.error(inter, "You are not in a voice channel.")
            return

        if not inter.guild.voice_client:
            await self.join(inter)

        player: MyPlayer = (
            inter.guild.voice_client
        )  # pyright: ignore[reportGeneralTypeIssues]

        self.logger.debug(f"{inter.user} searched {query}")
        tracks = await player.fetch_tracks(query)

        if not tracks:
            return await inter.send("No tracks found.")

        if isinstance(tracks, Playlist):
            tracks = tracks.tracks
            if len(tracks) > 1:
                player.queue.extend([(inter.user, track) for track in tracks[1:]])

        track: Track = tracks[0]

        if player.current:
            player.queue.append((inter.user, track))
        else:
            await player.play(track)
            player.addedby = inter.user
        await inter.send(f"Playing {track.uri}")

    @ytgroup.subcommand()
    async def skip(self, inter: discord.Interaction[discord.Client]):
        """Skips the currently playing song."""
        player: MyPlayer = (
            inter.guild.voice_client
        )  # pyright: ignore[reportGeneralTypeIssues]
        if not player:
            player = self.players[inter.guild.id] #TODO apparently this should not be needed but in the real world it doesnt work
        # if player.queue:
        if player.current:
            await player.seek(player.current.length) #cant skip to next track as it will trigger the on_end listener, so just skip to end of current one
            await inter.send(embed=discord.Embed(title=f"Skipped the current track by {inter.user}"), delete_after=60)

    @ytgroup.subcommand()
    async def pause(self, inter: discord.Interaction[discord.Client]):
        """Pauses or resumes the currently playing song."""
        player: MyPlayer = (
            inter.guild.voice_client
        )  # pyright: ignore[reportGeneralTypeIssues]
        if not player:
            player = self.players[inter.guild.id]
        await player.pause(not player.paused)
        await inter.send(embed=discord.Embed(title=("Paused" if player.paused else "Resumed") + f" {player.current.title} by {inter.user}"), delete_after=60)


    @ytgroup.subcommand()
    async def seek(self, inter: discord.Interaction[discord.Client], seek: str = discord.SlashOption(name="time", description="usage (m: can be omitted) -> +m:ss / -m:ss / m:ss (seeks to that time)", required=True)):
        """Seeks to a certain time in the song. You can use + or - to seek relative to the current position."""
        await inter.response.defer()  #TODO make sure the user can only seek when in channel, also skip etc
        player: MyPlayer = (
            inter.guild.voice_client
        )  # pyright: ignore[reportGeneralTypeIssues]
        if not player:
            player = self.players[inter.guild.id]

        if seek[0] == "+":
            seek = seek.strip("+")
            seekbool = 1
        elif seek[0] == "-":
            seek = seek.strip("-")
            seekbool = -1
        else:
            seekbool = 0
        if ":" in seek:  # if date and time is given
            try:
                timestr = datetime.strptime(seek, "%H:%M:%S")
            except ValueError:
                timestr = datetime.strptime(seek, "%M:%S")
            seconds = timestr.second + timestr.minute*60 + timestr.hour*3600
        else:
            seconds = int(seek)

        if seekbool == 1:
            seconds = (player.current.position // 1000) + seconds
        elif seekbool == -1:
            seconds = (player.current.position // 1000) - seconds
        self.logger.debug(seconds)
        await player.seek(seconds*1000)
        time.sleep(0.5)

        curr = timedelta(seconds=player.current.position//1000)
        tot = timedelta(seconds=player.current.length//1000)
        # format timedelta to mm:ss

        self.logger.debug(curr)
        self.logger.debug(tot)
        await inter.send(embed=discord.Embed(title=f"Seeking to {str(curr)} / {str(tot)} by {inter.user}"), delete_after=60)

    @ytgroup.subcommand()
    async def queue(self, inter: discord.Interaction[discord.Client]):
        """Shows the current queue."""
        player: MyPlayer = (
            inter.guild.voice_client
        )
        if not player:
            player = self.players[inter.guild.id]
        if not player.queue and not player.current:
            return await inter.send("No tracks in queue.")

        q = [(player.addedby, player.current)] + player.queue  # TODO paginator
        embed = discord.Embed(title="Queue", description="\n".join([f"{i+1}. {track.title} *({timedelta(seconds=track.length//1000)}) added by* **{user.display_name}**" for i, (user, track) in enumerate(q)][:4000]))
        embed.set_footer(text=f"Total queue length: {timedelta(seconds=sum([track.length//1000 for user, track in q]))}")
        await inter.send(embed=embed)

    @commands.Cog.listener()
    async def on_track_end(self, event: TrackEndEvent):
        assert isinstance(event.player, MyPlayer)
        if event.player.queue:
            event.player.addedby = event.player.queue[0][0]
            await event.player.play(event.player.queue.pop(0)[1])

    # @commands.Cog.listener() #TODO good error printing way
    # async def on_application_command_error(self, inter: discord.Interaction[discord.Client], error: Exception):
    #     traceback.print_exception(type(error), error, error.__traceback__)
    #     await inter.send(f"An error occurred: {error}")

    def cog_unload(self):
        self.logger.info("Deconstructing lavalink..")
        self.client.lavalink.terminate()


def setup(client):
    client.add_cog(LavaLinkCog(client))
