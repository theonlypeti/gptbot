import asyncio
import json
import nextcord as discord
from nextcord.ext import commands
import aiohttp
import platform

class ConverterCog(commands.Cog):
    def __init__(self, client, baselogger):
        self.client = client
        self.converterLogger = baselogger.getChild('converterLogger')
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(self.getCurrList()) #not preferred but works. Could use nextcord.ext.tasks and make a loop running once but ehh

    async def getCurrList(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://raw.githubusercontent.com/fawazahmed0/currency-api/1/latest/currencies.json') as req:
                txt = await req.text()
            self.currencylist = json.loads(txt)
            self.converterLogger.debug(self.currencylist)

    @discord.slash_command(name="convert", description="Convert from one currency to another")
    async def convert(self, interaction: discord.Interaction,
                      fromcurr: str = discord.SlashOption(name="from", description="Convert from"),
                      to: str = discord.SlashOption(description="Convert to"),
                      amount: float = discord.SlashOption(required=False,default=1)):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{fromcurr}/{to}.json') as req:
                rate = await req.json()
        rate = rate.get(to)
        self.converterLogger.debug(rate)
        converted = float(rate) * amount

        embedVar = discord.Embed(description=f"{amount} {self.currencylist[fromcurr]} = {converted} {self.currencylist[to]}", color=interaction.user.color)
        if amount != 1.0:
            embedVar.add_field(name="Current rate:",value=f"1 {fromcurr} = {rate} {to}")
        await interaction.send(embed=embedVar)

    @convert.on_autocomplete("fromcurr")
    @convert.on_autocomplete("to")
    async def currencyautocomplete(self, interaction: discord.Interaction, currency: str):
        if currency:
            currs = {item[0]: item[1] for item in tuple((v, k) for k, v in self.currencylist.items() if currency.casefold().strip() in f"{k.casefold()} {v.casefold()}")[:25]}
            await interaction.response.send_autocomplete(currs)

def setup(client,baselogger): #bot shit
    client.add_cog(ConverterCog(client, baselogger))
