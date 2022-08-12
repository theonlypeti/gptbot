import logging
import nextcord as discord
from nextcord.ext import commands,tasks
import aiohttp
import asyncio

class CurrencyCog(commands.Cog):
    def __init__(self,client,baselogger):
        self.client = client
        self.currencyLogger = baselogger.getChild('currencyLogger')
        self.printer.start()
        self.oldhuf = 0

    @tasks.loop(hours=24)
    async def printer(self):
        await asyncio.sleep(2) #not to send the message together with fujkin
        async with aiohttp.ClientSession() as session:
            async with session.get('https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/eur/huf.json') as req:
                huf = await req.json()
        huf = huf['huf']
        print(huf)

        if self.oldhuf > 0:
        #if True: #debug
            if huf != self.oldhuf:
                embedVar = discord.Embed(title="Current exchange rate", description=f"1 EUR = {huf} HUF", color=0x00ff00)
                embedVar.add_field(name="previous rate", value=f"1 EUR = {self.oldhuf} HUF")
                for channel in self.channels:
                    await channel.send(embed=embedVar)
        self.oldhuf = huf

    @printer.before_loop
    async def before_printer(self):
        self.currencyLogger.info('getting currency')
        await self.client.wait_until_ready()
        self.channels = (self.client.get_guild(601381789096738863).get_channel(607897146750140457), #rageon
                         )

def setup(client,baselogger): #bot shit
    client.add_cog(CurrencyCog(client, baselogger))
