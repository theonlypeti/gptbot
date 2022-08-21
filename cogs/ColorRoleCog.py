from numpy import zeros as npzeros
from imageio import imsave
import nextcord as discord
from colorthief import ColorThief
from nextcord.ext import commands
import emoji
import os

# TODO set threshold for similar colors
# TODO check who is calling the command
# TODO add footers for dropdowns ?what
# TODO add help
# TODO add ratelimit check with future/promise
# TODO add ratelimit emoji
# TODO maybe keep last used colors on server
# TODO add cooldown

class ColorRoleCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.emoteserver = self.client.get_guild(957469186798518282)

    @discord.slash_command(name="mycolor", guild_ids=[860527626100015154, 601381789096738863, 409081549645152256, 552498097528242197],dm_permission=False)
    async def mycolor(self):
        pass

    class HexModal(discord.ui.Modal):
        def __init__(self,cog):
            self.cog = cog
            super().__init__(title="Pick your color")
            self.hextext = discord.ui.TextInput(label="#", style=discord.TextInputStyle.short, placeholder="aabbcc",min_length=6, max_length=6)
            self.add_item(self.hextext)

        async def callback(self, ctx):
            dccolor = discord.Color.from_rgb(*[int(self.hextext.value[i:i + 2], 16) for i in range(0, 5, 2)])
            # await resetcustomcolor(ctx)
            await self.cog.setcustomcolor(ctx, dccolor)
            await ctx.send(embed=discord.Embed(title="Color changed", color=dccolor), ephemeral=True)

    class RGBModal(discord.ui.Modal):
        def __init__(self,cog):
            self.cog = cog
            super().__init__(title="Pick your server name color")
            self.rtext = discord.ui.TextInput(label="R", style=discord.TextInputStyle.short, placeholder="0-255",max_length=3)
            self.add_item(self.rtext)
            self.gtext = discord.ui.TextInput(label="G", style=discord.TextInputStyle.short, placeholder="0-255",max_length=3)
            self.add_item(self.gtext)
            self.btext = discord.ui.TextInput(label="B", style=discord.TextInputStyle.short, placeholder="0-255",max_length=3)
            self.add_item(self.btext)

        async def callback(self, ctx):
            dccolor = discord.Color.from_rgb(int(self.rtext.value), int(self.gtext.value), int(self.btext.value))
            await self.cog.setcustomcolor(ctx, dccolor)
            await ctx.send(embed=discord.Embed(title="Color changed", color=dccolor), ephemeral=True)

    class MyColorModal(discord.ui.Select):
        def __init__(self, palette, emojis, cog):
            self.palette = palette
            self.cog = cog
            self.opts = [discord.SelectOption(label=f"({i[0]}, {i[1]}, {i[2]})", value=n, emoji=emojie) for (n, i), emojie in zip(enumerate(palette), emojis)]
            self.opts.append(discord.SelectOption(label="Cancel", emoji=emoji.emojize(":cross_mark:"), value="-1"))
            # self.opts = [discord.SelectOption(label=f"({i[0]}, {i[1]}, {i[2]})", value=n) for n, i in enumerate(palette)]
            super().__init__(placeholder="Pick a color", options=self.opts)

        async def callback(self, interaction: discord.Interaction):
            if self.values[0] != "-1":
                color = self.palette[int(self.values[0])]
                dccolor = discord.Color.from_rgb(*color)
                await self.cog.setcustomcolor(interaction, dccolor)
                await interaction.edit(view=None, embed=discord.Embed(title="Color changed", color=dccolor))
            else:
                await interaction.edit(view=None, embed=discord.Embed(title="Cancelled", color=interaction.user.color),delete_after=5)
            emotes = [e for e in self.cog.emoteserver.emojis if e.name in ["a".join(map(str, color)) for color in self.palette]]
            for emote in emotes:
                await self.cog.emoteserver.delete_emoji(emote)

    class MyColorView(discord.ui.View):
        def __init__(self, palette,cog):
            self.palette = palette
            self.cog = cog
            super().__init__(timeout=30)

        async def on_timeout(self):
            emotes = [e for e in self.cog.emoteserver.emojis if e.name in ["+".join(map(str, color)) for color in self.palette]]
            for emote in emotes:
                await self.cog.emoteserver.delete_emoji(emote)

    async def setcustomcolor(self,interaction, dccolor):
        highest_role = interaction.user.roles[-1]
        if highest_role.name.startswith("* "):
            await highest_role.edit(color=dccolor)
        else:
            highest_index = interaction.guild.roles.index(highest_role)
            newRole = await interaction.guild.create_role(name=f"* {interaction.user.name}'s color", color=dccolor)
            newRole = await newRole.edit(position=highest_index + 1)
            await interaction.user.add_roles(newRole)

    async def resetcustomcolor(self,interaction: discord.Interaction):
        oldRole = [role for role in interaction.user.roles if role.name.startswith("* ")]
        if oldRole:
            oldRole = oldRole[0]
            await oldRole.delete()

    @mycolor.subcommand(name="reset", description="Removes your pfp role color")
    async def mycolorreset(self,interaction):
        await self.resetcustomcolor(interaction)
        await interaction.send("Done", ephemeral=True)

    @mycolor.subcommand(name="rgb", description="Pick a color from RGB values")
    async def mycolorrgb(self,interaction):
        modal = self.RGBModal(self)
        await interaction.response.send_modal(modal)

    @mycolor.subcommand(name="hex", description="Pick a color with a hex code")
    async def mycolorhex(self,interaction):
        modal = self.HexModal(self)
        await interaction.response.send_modal(modal)

    async def pickColorFromPic(self,interaction):
        color_thief = ColorThief('temp.png')
        palette = list(set(color_thief.get_palette(color_count=4)))
        emojis = []
        if not self.emoteserver:
            self.emoteserver = self.client.get_guild(957469186798518282)
        for n, color in enumerate(palette):
            im1 = npzeros((100, 100, 3), dtype='uint8')
            im1[:, :] = color
            imsave("fname.png", im1) # TODO do with IO again
            with open("fname.png", "rb") as file:
                emojis.append(await self.emoteserver.create_custom_emoji(name="a".join(map(str, color)), image=file.read()))
            os.remove("fname.png")
        viewObj = self.MyColorView(palette,self)
        viewObj.add_item(self.MyColorModal(palette, emojis, self))
        await interaction.send(view=viewObj)

    @mycolor.subcommand(description="Lets you pick your color from any uploaded picture.")
    async def image(self,interaction, uploaded: discord.Attachment = discord.SlashOption(name="image",description="The image from which the colors are picked from.",required=True)):
        await interaction.response.defer()
        with open("temp.png", "wb") as file:
            await uploaded.save(file) #TODO learn how to do this with IO without downloading the whole file
        await self.pickColorFromPic(interaction)

    @mycolor.subcommand(description="Lets you pick your color from your profile picture.")
    async def pfp(self,interaction):
        await interaction.response.defer()
        with open("temp.png", "wb") as file:
            await interaction.user.display_avatar.save(file)
        await self.pickColorFromPic(interaction)

    @mycolor.subcommand(description="Export a role color for easy sharing and use on other roles or servers.")
    async def export(self, interaction, role: discord.Mentionable = discord.SlashOption(name="role", description="The role to export the color of.", required=False,default=None)):
        if role:
            color = role.color
        else:
            color = interaction.user.color
        hexcode = f"{hex(color.r)[2:].zfill(2)}{hex(color.g)[2:].zfill(2)}{hex(color.b)[2:].zfill(2)}".upper()
        embedVar = discord.Embed(title="Color", color=color)
        embedVar.add_field(name="#", value=hexcode,inline=False)
        colors = (emoji.emojize(i) for i in [":red_square:", ":green_square:", ":blue_square:"])
        for key,val in zip(colors,color.to_rgb()):
            embedVar.add_field(name=f"{key}", value=f"{val}", inline=True)
        embedVar.fields[1].inline = False
        embedVar.set_footer(text=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
        await interaction.send(embed=embedVar)

def setup(client,baselogger): #TODO maybe add some logging messages
    client.add_cog(ColorRoleCog(client))