from datetime import datetime
import nextcord as discord
from nextcord.ext import commands
from utils.ps import Adress,broadcasty

#TODO broadcast calc does not always come up with unique adresses, also include the mask too

class PsCog(commands.Cog):
    def __init__(self,client,baselogger):
        global pslogger
        self.client = client
        pslogger = baselogger.getChild("PsLogger")

    class BroadcastCalcModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Broadcast kalkulačka")
            self.iplabel = discord.ui.TextInput(label="IP", default_value="192.168.1.", max_length=15, required=True)
            self.add_item(self.iplabel)

        async def callback(self, interaction: discord.Interaction):
            ip = self.iplabel.value
            try:
                gener = broadcasty(ip)
            except ValueError as e:
                pslogger.error(e)
                return interaction.send(f"Oopsie {e}")
            embedVar = discord.Embed(title="Broadcast kalkulačka", description=f"pre adresu {ip}", color=interaction.user.color,timestamp=datetime.now())
            broadcaststr,idstr = "",""
            for ip in gener:
                broadcaststr += f"{ip.broadcast}/{ip.mask}\n"
                idstr += f"{ip.ids}/{ip.mask}\n"
            embedVar.add_field(name="Možné broadcast adresy:", value=broadcaststr)
            embedVar.add_field(name="Možné ID adresy:", value=idstr)
            embedVar.set_footer(text=f"{interaction.user.name}#{interaction.user.discriminator}",icon_url=interaction.user.avatar.url)
            await interaction.send(embed=embedVar)

    class IpCalcModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="IP kalkulačka")

            self.iplabel = discord.ui.TextInput(label="IP", default_value="192.168.1.", max_length=15, required=True)
            self.add_item(self.iplabel)

            self.masklabel = discord.ui.TextInput(label="Maska (/)", placeholder="24-30", max_length=2, required=False)
            self.add_item(self.masklabel)
            self.adresslabel = discord.ui.TextInput(label="alebo Počet adries", placeholder="0-256", max_length=3, required=False)
            self.add_item(self.adresslabel)

            #self.adressselect = discord.ui.Select(placeholder="Počet adries | Maska",options=[discord.SelectOption(value=str(32-i),label=f"Počet adries: {2 ** i}/ Maska: {32-i}") for i in range(1,9)])
            #self.add_item(self.adressselect)

        async def callback(self, interaction: discord.Interaction):
            ip = self.iplabel.value
            if "/" in ip:
                ip,mask = ip.split("/")

            try:
                mask = int(self.masklabel.value) if self.masklabel.value else None
                adress = int(self.adresslabel.value) if self.adresslabel.value else None
            except ValueError as e:
                await interaction.send(f"{e.args[0]} musí byt čislo!")
                return

            if mask and adress:
               await interaction.send(f"Zadaj iba jedno z polí: \n__Maska__ ALEBO __Počet adries__")
            if not (mask or adress):
               await interaction.send(f"Zadaj aspoň jedno z polí: \n__Maska__ ALEBO __Počet adries__")
            if mask and not 24 <= mask <= 32:
               await interaction.send(f"Maska musí byť medzi 24 a 32")
            if adress and not 0 <= adress <= 256:
               await interaction.send(f"Počet adries musí byť medzi 0 a 256")

            #mask = int(self.adressselect.values[0])
            try:
                calc = Adress(ip, mask)
                #pslogger.debug(calc.__dict__)
            except ValueError as e:
                pslogger.error(e)
                await interaction.send(f"Oops {e.args[0]}")
                return
            embedVar = discord.Embed(title="Subnetwork calc",color=interaction.user.color,timestamp=datetime.now())
            embedVar.add_field(name="IP", value=calc.ip, inline=True)
            embedVar.add_field(name="Maska", value=f"/{calc.mask}", inline=True)
            embedVar.add_field(name="Bitová maska", value=calc.binary_mask, inline=True)
            embedVar.add_field(name="Počet adries", value=calc.adresses, inline=True)
            embedVar.add_field(name="Počet hostov", value=calc.hosts, inline=True)
            embedVar.add_field(name="ID", value=calc.ids, inline=True)
            embedVar.add_field(name="Prvý najmenší host", value=calc.first_host, inline=True)
            embedVar.add_field(name="Posledný najväčší host", value=calc.last_host, inline=True)
            embedVar.add_field(name="Broadcast", value=calc.broadcast, inline=True)
            embedVar.set_footer(text=f"{interaction.user.name}#{interaction.user.discriminator}",icon_url=interaction.user.avatar.url)
            await interaction.send(embed=embedVar)

    @discord.slash_command(name="ps", description="Kalkulačky IP pre predmet počítačové systémy",guild_ids=(860527626100015154,))
    async def psbase(self, ctx):
        pass

    @psbase.subcommand(name="ipcalc", description="Vypočíta základné vlastnosti networku")
    async def calc(self, interaction):
        modal = self.IpCalcModal()
        await interaction.response.send_modal(modal)

    @psbase.subcommand(name="broadcast", description="Vypočíta 4 broadcasty/idčka pre danú adresu")
    async def broadcast(self, ctx):
        modal = self.BroadcastCalcModal()
        await ctx.response.send_modal(modal)

    @psbase.subcommand(name="vysvetlivka", description="Ukáže animáciu ako funguje subnetting")
    async def vysvetlivka(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/892054308563091456/998385704117731418/Subnetting.mp4?size=4096")

def setup(client,baselogger):
    client.add_cog(PsCog(client,baselogger))
