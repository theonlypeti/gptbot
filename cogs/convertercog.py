import json
from datetime import datetime
import emoji
import nextcord as discord
from nextcord.ext import commands, tasks
import aiohttp
import pint

import utils.embedutil


class ConverterCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.converterLogger = client.logger.getChild(f"{__name__}logger")
        self.getCurrList.start()
        self.pu = pint.UnitRegistry()

    @tasks.loop(hours=24)
    async def getCurrList(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://raw.githubusercontent.com/fawazahmed0/currency-api/1/latest/currencies.json') as req:
                txt = await req.text()
            self.currencylist = json.loads(txt)
            self.converterLogger.debug(f"{len(self.currencylist)} currencies loaded.")

    @discord.slash_command(name="convert", description="Convert from one unit to another")
    async def convert(self, interaction: discord.Interaction):
        ...

    @convert.subcommand(name="currency", description="Convert from one currency to another")
    async def currency(self, interaction: discord.Interaction,
                      fromcurr: str = discord.SlashOption(name="from", description="Convert from"),
                      to: str = discord.SlashOption(description="Convert to"),
                      amount: float = discord.SlashOption(required=False, default=1)):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{fromcurr}/{to}.json') as req:
                rate = await req.json()
        rate = rate.get(to)
        converted = float(rate) * amount

        embedVar = discord.Embed(description=f"{amount} {self.currencylist[fromcurr]} = {converted} {self.currencylist[to]}", color=interaction.user.color, timestamp=datetime.now())
        utils.embedutil.setuser(embedVar, interaction.user)
        if fromcurr == to:
            embedVar.add_field(name="What", value=emoji.emojize(':face_with_raised_eyebrow:'))
        elif amount != 1.0:
            embedVar.add_field(name="Current rate:", value=f"1 {fromcurr} = {rate} {to}")
        await interaction.send(embed=embedVar)

    @currency.on_autocomplete("fromcurr")
    @currency.on_autocomplete("to")
    async def currencyautocomplete(self, interaction: discord.Interaction, currency: str):
        if currency:
            currs = {item[0] or item[1]: item[1] for item in tuple((v, k) for k, v in self.currencylist.items() if currency.casefold().strip() in f"{k.casefold()} {v.casefold()}")[:25]}
            await interaction.response.send_autocomplete(currs)

    @convert.subcommand(name="temperature", description="Convert from one temperature unit to another")
    async def temperature(self, interaction: discord.Interaction,
                       fromt: str = discord.SlashOption(name="from", description="Convert from", choices=["celsius", "fahrenheit", "kelvin"]),
                       to: str = discord.SlashOption(description="Convert to", choices=["celsius", "fahrenheit", "kelvin"]),
                       amount: float = discord.SlashOption(required=False, default=1)):
        await interaction.response.defer()
        fromu = self.pu.Quantity(amount, fromt)
        tou = fromu.to(to)

        embedVar = discord.Embed(
            description=f"{fromu:~P} = {tou:P~}",
            color=interaction.user.color, timestamp=datetime.now())
        utils.embedutil.setuser(embedVar, interaction.user)
        if fromu == to:
            embedVar.add_field(name="What", value=emoji.emojize(':face_with_raised_eyebrow:'))
        await interaction.send(embed=embedVar)

    @convert.subcommand(name="length", description="Convert from one length unit to another")
    async def length(self, interaction: discord.Interaction,
                          fromt: str = discord.SlashOption(name="from", description="Convert from",
                                                           choices=["kilometer", "meter", "centimeter", "millimeter", "micrometer", "nanometer", "mile", "yard", "foot", "inch", "nautical_mile"]),
                          to: str = discord.SlashOption(description="Convert to",
                                                        choices=["kilometer", "meter", "centimeter", "millimeter", "micrometer", "nanometer", "mile", "yard", "foot", "inch", "nautical_mile"]),
                          amount: float = discord.SlashOption(required=False, default=1)):
        await interaction.response.defer()
        fromu = self.pu.Quantity(amount, fromt)
        tou = fromu.to(to)

        embedVar = discord.Embed(
            description=f"{fromu:P} = {tou:P}",
            color=interaction.user.color, timestamp=datetime.now())
        utils.embedutil.setuser(embedVar, interaction.user)
        if fromt == to:
            embedVar.add_field(name="What", value=emoji.emojize(':face_with_raised_eyebrow:'))
        await interaction.send(embed=embedVar)

    @convert.subcommand(name="weight", description="Convert from one weight unit to another")
    async def weight(self, interaction: discord.Interaction,
                     fromt: str = discord.SlashOption(name="from", description="Convert from",
                                                      choices=["kilogram", "gram", "pound", "ounce", "tonne", "carat", "grain", "stone"]),
                     to: str = discord.SlashOption(description="Convert to",
                                                   choices=["kilogram", "gram", "pound", "ounce", "tonne", "carat", "grain", "stone"]),
                     amount: float = discord.SlashOption(required=False, default=1)):
        await interaction.response.defer()
        fromu = self.pu.Quantity(amount, fromt)
        tou = fromu.to(to)

        embedVar = discord.Embed(
            description=f"{fromu:P} = {tou:P}",
            color=interaction.user.color, timestamp=datetime.now())
        utils.embedutil.setuser(embedVar, interaction.user)
        if fromt == to:
            embedVar.add_field(name="What", value=emoji.emojize(':face_with_raised_eyebrow:'))
        await interaction.send(embed=embedVar)

    @convert.subcommand(name="data", description="Convert from one data size unit to another")
    async def data(self, interaction: discord.Interaction,
                   fromt: str = discord.SlashOption(name="from", description="Convert from",
                                                    choices=["bit", "kilobit", "megabit", "gigabit", "terabit", "petabit",
                                                        "byte", "kilobyte", "megabyte", "gigabyte", "terabyte", "petabyte",
                                                        "kibibit", "mebibit", "gibibit", "tebibit", "pebibit",
                                                        "kibibyte", "mebibyte", "gibibyte", "tebibyte", "pebibyte"]),
                   to: str = discord.SlashOption(description="Convert to",
                                                 choices=["bit", "kilobit", "megabit", "gigabit", "terabit", "petabit",
                                                          "byte", "kilobyte", "megabyte", "gigabyte", "terabyte", "petabyte",
                                                          "kibibit", "mebibit", "gibibit", "tebibit", "pebibit",
                                                          "kibibyte", "mebibyte", "gibibyte", "tebibyte", "pebibyte"]),
                   amount: float = discord.SlashOption(required=False, default=1)):
        await interaction.response.defer()
        fromu = self.pu.Quantity(amount, fromt)
        tou = fromu.to(to)

        embedVar = discord.Embed(
            description=f"{fromu:P} = {tou:P}",
            color=interaction.user.color, timestamp=datetime.now())
        utils.embedutil.setuser(embedVar, interaction.user)
        if fromt == to:
            embedVar.add_field(name="What", value=emoji.emojize(':face_with_raised_eyebrow:'))
        await interaction.send(embed=embedVar)


def setup(client):
    client.add_cog(ConverterCog(client))
