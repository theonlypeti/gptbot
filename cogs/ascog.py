from datetime import datetime
import nextcord as discord
from nextcord.ext import commands
from utils.assolver import *


class AsFunc:
    def __init__(self, func=None, title=None, label=None, placeholder=None):
        self.func = func
        self.title = title
        self.label = label
        self.placeholder = placeholder


permut = AsFunc(title="Permutácie", label="Permutacie", placeholder="(1,2)(3,4)o(5,6)o(7,8,9)", func=solver)
zobraz = AsFunc(title="Zobrazenie", label="Zobrazenie", placeholder="(a,b,c,d)o(b,c,d,a)", func=solver2)
rady = AsFunc(title="Rády", label="Permutácia s rádom", placeholder="(1,2,3)^3", func=solver3)


class AsCog(commands.Cog):
    def __init__(self, client, baselogger):
        pass

    class AsModal(discord.ui.Modal):
        def __init__(self, func: AsFunc):
            super().__init__(title=func.title)
            self.inputlabel = discord.ui.TextInput(label=func.label, placeholder=func.placeholder, required=True)
            self.add_item(self.inputlabel)
            self.func = func.func

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            vstup = self.inputlabel.value
            embedVar = discord.Embed(description=vstup, color=interaction.user.color, timestamp=datetime.now())
            try:
                embedVar.add_field(name="Výsledok", value=self.func(vstup))
            except Exception as e:
                embedVar.add_field(name="Chyba", value=e)
            embedVar.set_footer(text=f"{interaction.user.name}#{interaction.user.discriminator}",
                                icon_url=interaction.user.avatar.url)
            await interaction.send(embed=embedVar)

    @discord.slash_command(name="as", description="Kalkulačky pre predmet Algebraické štruktúry",
                           guild_ids=(601381789096738863, 860527626100015154, 800196118570205216))
    async def asbase(self, interaction):
        pass

    @asbase.subcommand(name="permutacie", description="Permutácie")
    async def permutacie(self, interaction):
        modal = self.AsModal(permut)
        await interaction.response.send_modal(modal)

    @asbase.subcommand(name="zobrazenie", description="Zobrazenie")
    async def zobraz(self, interaction):
        modal = self.AsModal(zobraz)
        await interaction.response.send_modal(modal)

    @asbase.subcommand(name="rady_permutacie", description="Rády permutácie")
    async def rady(self, interaction):
        modal = self.AsModal(rady)
        await interaction.response.send_modal(modal)


def setup(client, baselogger):
    client.add_cog(AsCog(client, baselogger))
