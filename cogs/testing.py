import os
import random
import nextcord as discord
from nextcord.ext import commands

class Testing(commands.Cog):
    def __init__(self,client,baselogger):
        self.client = client

    class testvw(discord.ui.View):
        def __init__(self):
            self.msg = None
            super().__init__(timeout=0)

        @discord.ui.button(label="test")
        async def test(self,button,interaction):
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
            self.bottomtext = discord.ui.TextInput(label="Bottom Text",required=False)
            self.add_item(self.bottomtext)

        async def callback(self,interaction: discord.Interaction):
            await interaction.response.defer()
            await interaction.response.send_modal(self)

    @discord.slash_command(name="testing",description="testing")
    async def testing(self,ctx):
        viewObj = self.testvw()
        viewObj.msg = await ctx.send(view=viewObj)

    @discord.slash_command(name="modaltesting", description="testing")
    async def modaltesting(self, ctx):
        await ctx.response.send_modal(self.TextInputModal())

    @discord.slash_command(name="pick",description="pick",guild_ids=(860527626100015154,))
    async def fut(self,ctx):
        await ctx.response.defer()
        if ctx.user.id != 617840759466360842:
            return
        os.chdir(r"D:\Users\Peti.B\Pictures\microsoft\Windows\ft")
        sample = [file for file in os.listdir() if file.endswith(".jpg") or file.endswith(".png")]
        with ctx.channel.typing():
            await ctx.send(files=[discord.File(random.choice(sample))])


def setup(client,baselogger):
    client.add_cog(Testing(client,baselogger))