"""A simple example of using Mafic."""

from __future__ import annotations
import traceback
from typing import TYPE_CHECKING, Any
from mafic import NodePool, Player, Playlist, Track, TrackEndEvent
import nextcord as discord
from nextcord.ext import commands
from nextcord.ext import tasks

if TYPE_CHECKING:
    from nextcord.abc import Connectable


class MyPlayer(Player[discord.Client]):
    def __init__(self, client: discord.Client, channel: Connectable) -> None:
        super().__init__(client, channel)

        # Mafic does not provide a queue system right now, low priority.
        self.queue: list[Track] = []


class LavaLinkCog(commands.Cog):
    def __init__(self, client) -> None:
        self.client: discord.Client = client
        self.ready_ran = False
        self.pool = NodePool(self.client)
        self.logger = client.logger.getChild(__name__)
        self.on_ready.start()

    @tasks.loop(count=1)
    async def on_ready(self):
        if self.ready_ran:
            return

        await self.pool.create_node(
            host="127.0.0.1",
            port=2333,
            label="MAIN",
            password="haha",
        )
        self.logger.info("Created lavalink node.")

        self.ready_ran = True

    @discord.slash_command(name="yt", dm_permission=False)
    async def ytgroup(self, interaction):
        pass

    @ytgroup.subcommand()
    async def join(self, inter: discord.Interaction[discord.Client]):
        """Join your voice channel."""
        assert isinstance(inter.user, discord.Member)

        if not inter.user.voice or not inter.user.voice.channel:
            return await inter.response.send_message("You are not in a voice channel.")

        channel = inter.user.voice.channel

        # This apparently **must** only be `Client`.
        await channel.connect(cls=MyPlayer)  # pyright: ignore[reportGeneralTypeIssues]
        await inter.send(f"Joined {channel.mention}.")

    @ytgroup.subcommand()
    async def play(self, inter: discord.Interaction[discord.Client], query: str):
        """Play a song.

        query:
            The song to search or play.
        """
        assert inter.guild is not None

        if not inter.guild.voice_client:
            await self.join(inter)

        player: MyPlayer = (
            inter.guild.voice_client
        )  # pyright: ignore[reportGeneralTypeIssues]

        tracks = await player.fetch_tracks(query)

        if not tracks:
            return await inter.send("No tracks found.")

        if isinstance(tracks, Playlist):
            tracks = tracks.tracks
            if len(tracks) > 1:
                player.queue.extend(tracks[1:])

        track = tracks[0]

        await player.play(track)

        await inter.send(f"Playing {track.uri}")

    @commands.Cog.listener()
    async def on_track_end(self, event: TrackEndEvent):
        assert isinstance(event.player, MyPlayer)

        if event.player.queue:
            await event.player.play(event.player.queue.pop(0))

    @commands.Cog.listener()
    async def on_application_command_error(self, inter: discord.Interaction[discord.Client], error: Exception):
        traceback.print_exception(type(error), error, error.__traceback__)
        await inter.send(f"An error occurred: {error}")


STATS = """```
Uptime: {uptime}
Memory: {used:.0f}MiB : {free:.0f}MiB / {allocated:.0f}MiB -- {reservable:.0f}MiB
CPU: {system_load:.2f}% : {lavalink_load:.2f}%
Players: {player_count}
Playing Players: {playing_player_count}
```"""


def setup(client):
    client.add_cog(LavaLinkCog(client))
