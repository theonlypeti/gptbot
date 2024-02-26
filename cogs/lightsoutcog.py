import itertools
import random
from typing import Literal
import nextcord as discord
from nextcord.ext import commands
from utils.mentionCommand import mentionCommand
from utils.embedutil import error


class LightsOutCog(commands.Cog):
    def __init__(self, client):
        self.logger = client.logger.getChild(f"{self.__module__}")
        self.client = client

    class LightsOutGame(discord.ui.View):
        def __init__(self, size: str, user: discord.User):
            super().__init__(timeout=900)
            self.message: discord.Message | None = None
            self.player = user
            self.moves = 0
            self.size = int(size[0])
            for i, j in itertools.product(range(self.size), range(self.size)):
                self.add_item(self.Light(i, j, self))

        async def on_timeout(self) -> None:
            for ch in self.children:
                ch.disabled = True
            await self.message.edit(view=self)

        class Light(discord.ui.Button):
            def __init__(self, x: int, y: int, game: "LightsOutCog.LightsOutGame"):
                super().__init__(label="😶", row=x)
                self.state = random.randint(0, 1)  # TODO make sure its not pre solved
                self.draw()
                self.x = x
                self.y = y
                self.game = game
                self.coords = (self.x, self.y)

            def draw(self):
                self.style = discord.ButtonStyle.grey if not self.state else discord.ButtonStyle.blurple
                self.label = "😐" if not self.state else "😀"

            async def callback(self, interaction: discord.Interaction):
                if interaction.user != self.game.player:
                    await error(interaction, f"This is not your game. Start yours with {mentionCommand(interaction.client, 'lightsout')}")
                    return
                print(self.view.id)
                buttons: list[LightsOutCog.LightsOutGame.Light] = self.game.children
                self.state = not self.state
                self.draw()
                others = [
                    (self.x - 1, self.y),
                    (self.x + 1, self.y),
                    (self.x, self.y - 1),
                    (self.x, self.y + 1),
                          ]
                for b in buttons:
                    if b.coords in others:
                        b.state = not b.state
                        b.draw()
                win = self.game.checkwin()
                self.game.moves += 1
                await self.game.message.edit(
                    view=self.game,
                    content=f"Finished in {self.game.moves} moves!" if win else ""
                )

        def checkwin(self):
            if all([b.state for b in self.children]):
                for b in self.children:
                    b.style = discord.ButtonStyle.green
                    b.label = "🤑"
                    b.disabled = True
                return True
            return False

    @discord.slash_command(name="lightsout", description="Start a game of Lights out.", guild_ids=(860527626100015154,))
    async def lightsout(self, interaction: discord.Interaction, size: Literal["3x3", "5x5"]):
        game = LightsOutCog.LightsOutGame(size, interaction.user)
        game.message = await interaction.send("Light up every square by clicking on them. Every square changes the state of their neighbouring ones too.", view=game)


def setup(client):
    client.add_cog(LightsOutCog(client))
