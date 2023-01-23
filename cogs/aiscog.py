import logging
import os
from datetime import datetime
import json
import bs4
import nextcord as discord
from nextcord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup as html
import emoji
from dotenv import load_dotenv
root = os.getcwd()
load_dotenv(r"./credentials/ais.env")


class Tema(object):
    def __init__(self, tema: bs4.Tag):
        rows = tema.find_all('td')
        self.num = int(rows[0].text[:-1])
        self.name = rows[2].text
        self.rawlink = rows[10]
        temaid = f"https://is.stuba.sk{rows[10].find('a').get('href')}"  # why do I do it like this
        temaid = temaid[temaid.find("detail="):]
        temaid = temaid[:temaid.find(";")]
        self.link = f"https://is.stuba.sk/auth/student/zp_temata.pl?seznam=1;{temaid}"

    def __str__(self):
        return f"{self.num} = {self.name}"

    def makeLink(self):
        return f'{self.num} = [__{self.name}__]({self.link}\n"Nestiahne nič, je to len bug")'

    def makeShortLink(self):
        return f'{self.num} = [__{self.name}__]({self.link})'


class AisCog(commands.Cog):
    def __init__(self, client, baselogger):
        self.client = client
        self.aisLogger = baselogger.getChild('aisLogger')
        self.printer.start()
        self.temy = []
        with open(root+r'/data/ais_notif_channels.txt') as f:
            self.channels = json.load(f)

    @tasks.loop(minutes=30)
    async def printer(self):
        headers = {
            'enctype': 'application/x-www-form-urlencoded',
            'Content-Language': 'sk'
        }
        payload = {
            'credential_0': os.getenv("AIS_NAME"),
            'credential_1': os.getenv("AIS_PWD"),
            'login_hidden': 1,
            #'destination': '/auth/student/zp_temata.pl?studium=163040;obdobi=605;seznam=1;lang=sk',
            'destination': '/auth/student/zp_temata.pl?seznam=1;lang=sk',
            'auth_id_hidden': 0,
            'auth_2fa_type': 'no',
            "seznam": "1",
            #"studium": "163040",
            #"obdobi": "605"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post('https://is.stuba.sk/system/login.pl?studium=163040;obdobi=605;seznam=1;lang=sk', headers=headers, data=payload) as req:
                soup = html(await req.text(), 'html.parser')
        try:
            a = soup.find(attrs={"id": "table_1"})
            b = a.find("tbody")
            c = b.find_all("tr")
            temy = list(map(Tema, c))
        except AttributeError:
            self.aisLogger.info("No temy found")
            return
        self.aisLogger.info(f"Checking for témy, {len(temy)} found.")

        if len(self.temy) > 0:
        #if True: #debug
            if len(self.temy) != len(c):
                os.makedirs(root+r"/temyLogs", exist_ok=True)
                with open(root+r"/temyLogs/"+f"temy_{datetime.now().strftime('%m-%d-%H-%M')}.txt", "w", encoding="UTF-8") as file:
                    temyJson = [{"poradie": tema.num, "nazov": tema.name} for tema in temy]
                    json.dump(temyJson, file, indent=4)

                try:
                    newDict = {tema.name: tema for tema in temy}
                    oldDict = {tema.name: tema for tema in self.temy}
                    newNames: list[str] = list(newDict.keys())
                    oldNames: list[str] = list(oldDict.keys()) #[tema.name for tema in self.temy]
                    if len(temy) > len(self.temy):
                        diff = set(newNames).difference(oldNames)
                        diffTemy: list[Tema] = [newDict[name] for name in diff]
                    else:
                        diff = set(oldNames).difference(newNames)
                        diffTemy: list[Tema] = [oldDict[name] for name in diff]
                    text = "" if diffTemy else f"Zdá sa nie sú žiadne témy."
                    temanums = [tema.num for tema in diffTemy]
                    for tema in diffTemy:
                        andmoretext = f"a ešte {', '.join(map(str,temanums))}"
                        if len(text) + len(tema.makeShortLink()) + len(andmoretext) < 2000:
                            text += f"{tema.makeShortLink()}\n"
                            temanums.remove(tema.num)
                        else:
                            text += f"{andmoretext}"
                            break
                    embedVar = discord.Embed(title="Počet tém bakalárskych prác sa zmenil!", description=text, color=(discord.Color.red(), discord.Color.green())[len(self.temy) < len(c)])
                    #embedVar = discord.Embed(title="Just testing :*")
                except Exception as e:
                    logging.error(e)
                    embedVar = discord.Embed(title="Počet tém bakalárskych prác sa zmenil!")
                embedVar.add_field(name="Starý počet tém", value=len(self.temy))
                embedVar.add_field(name="Nový počet tém", value=len(temy))
                embedVar.set_footer(text="Ak sa pýta stiahnuť súbor, je to len bug, nestiahne nič, otvorí stránku normálne.")
                viewObj = AisCog.NotificationButton()

                for channelid in self.channels:
                    channel = self.client.get_channel(channelid)
                    if len(self.temy) < len(temy):
                        role = discord.utils.find(lambda m: m.name == 'Bakalarka notifications', channel.guild.roles)
                        await channel.send(role.mention if role is not None else "", embed=embedVar, view=viewObj)
                    else:
                        await channel.send(embed=embedVar, view=viewObj)
        self.temy = temy

    @printer.before_loop #i could comment this out but then it would look not pretty how my bootup time shot up by 5s haha
    async def before_printer(self):
        self.aisLogger.debug('getting temy')
        await self.client.wait_until_ready()

    class NotificationButton(discord.ui.View):
        @discord.ui.button(emoji=emoji.emojize(':no_bell:', language="alias"), label="Don't notify me")
        async def unsub(self, button, ctx: discord.Interaction):
            try:
                await ctx.user.remove_roles(discord.utils.find(lambda m: m.name == 'Bakalarka notifications', ctx.user.roles))
            except Exception as e:
                logging.error(e)
            await ctx.send(embed=discord.Embed(description="Odteraz nebudeš dostávať pingy ak pribudnú nové témy.", color=discord.Color.red()), ephemeral=True)

        @discord.ui.button(emoji=emoji.emojize(':bell:', language="alias"), label="Notify me")
        async def sub(self, button, ctx):
            try:
                await ctx.user.add_roles([i for i in ctx.guild.roles if i.name == "Bakalarka notifications"][0])
            except Exception as e:
                logging.error(e)
            await ctx.send(embed=discord.Embed(description="Odteraz budeš dostávať pingy ak pribudnú nové témy.", color=discord.Color.green()), ephemeral=True)

        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(discord.ui.Button(label="Zobraz temy", url="https://is.stuba.sk/auth/student/zp_temata.pl?seznam=1", style=discord.ButtonStyle.url, emoji=emoji.emojize(":globe_with_meridians:")))

    @discord.slash_command(description="Commands for STU bakalarka témy")
    async def bakalarka(self, interaction):
        pass

    @bakalarka.subcommand(name="debug", description="Print current témy")
    async def debugprint(self, interaction: discord.Interaction):
        await interaction.response.defer()
        text = ""
        temanums = [tema.num for tema in self.temy]
        andmoretext = f"Zdá sa nie sú žiadne témy."
        for tema in self.temy:
            andmoretext = f"a ešte {', '.join(map(str, temanums))}"
            if len(text) + len(tema.makeShortLink()) + len(andmoretext) < 2000:
                text += f"{tema.makeShortLink()}\n"
                temanums.remove(tema.num)
            else:
                break
        text += f"{andmoretext}"
        embedVar = discord.Embed(title="Zoznam tém", description=text)
        embedVar.set_footer(text="Ak sa pýta stiahnuť súbor, je to ok, ais je starý bugnutý, nestiahne nič, otvorí stránku normálne.")
        await interaction.send(embed=embedVar, view=self.NotificationButton())

    @bakalarka.subcommand(name="enable", description="Set this channel as notification channel")
    async def setupchannel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.channel.id in self.channels:
            await interaction.send(embed=discord.Embed(description="Tento channel už má setupované notifikácie.",color=discord.Color.red()), ephemeral=True)
            return
        self.channels.append(interaction.channel.id)
        with open(root+r"/data/ais_notif_channels.txt", "w", encoding="UTF-8") as file:
            json.dump(self.channels, file, indent=4)
        if (role:=(discord.utils.find(lambda m: m.name == 'Bakalarka notifications', interaction.guild.roles))) is None:
            role = await interaction.guild.create_role(name="Bakalarka notifications",mentionable=True,color=discord.Color.dark_red())
        await interaction.send(embed=discord.Embed(description=f"Notifikácie pre témy bakalárskych prác boli nastavené v tomto kanáli.\nPridajte si rolu {role.mention} gombíkmi, aby ste dostávali pingy.", color=discord.Color.dark_red()), view=self.NotificationButton())

    @bakalarka.subcommand(name="disable", description="Remove this channel as notification channel")
    async def removechannel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.channel.id not in self.channels:
            await interaction.send(embed=discord.Embed(description="Tento channel nemá nastavené notifikácie.", color=discord.Color.red()),ephemeral=True)
            return
        self.channels.remove(interaction.channel.id)
        with open(root+r"/data/ais_notif_channels.txt", "w", encoding="UTF-8") as file:
            json.dump(self.channels, file, indent=4)
        viewObj = self.RemoveRoleView(interaction.user)
        await interaction.send(embed=discord.Embed(description="Notifikácie pre témy bakalárskych prác boli odstránené v tomto kanáli.",color=discord.Color.dark_red()),view=viewObj)

    class RemoveRoleView(discord.ui.View):
        def __init__(self, user: discord.User):
            self.original_user = user
            super().__init__(timeout=None)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user == self.original_user

        @discord.ui.button(emoji=emoji.emojize(':wastebasket:', language="alias"), label="Vymaž aj rolu", style=discord.ButtonStyle.danger)
        async def deleterole(self, button, interaction: discord.Interaction):
            try:
                if (role := discord.utils.find(lambda m: m.name == 'Bakalarka notifications', interaction.guild.roles)) is not None:
                    await role.delete(reason=f"{interaction.user.name}#{interaction.user.discriminator} disabled notification channel {interaction.channel.name} for bakalarka temy")
                await interaction.message.edit(view=None)
            except Exception as e:
                logging.error(e)
                await interaction.send(str(e))

        @discord.ui.button(emoji=emoji.emojize(':check_mark_button:', language="alias"), label="Iba presúvam channel")
        async def keeprole(self, button, interaction: discord.Interaction):
            await interaction.message.edit(view=None)


def setup(client, baselogger): #bot shit
    client.add_cog(AisCog(client, baselogger))
