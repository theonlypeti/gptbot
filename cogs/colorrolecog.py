from io import BytesIO
from numpy import zeros as npzeros
from imageio import imsave
import nextcord as discord
from colorthief import ColorThief
from nextcord.ext import commands, tasks
import emoji

# TODO set threshold for similar colors
# TODO add footers for dropdowns ?what
# TODO add help
# TODO add ratelimit check with timeout
# TODO add ratelimit emoji
# TODO maybe keep last used colors on server
# TODO add cooldown
# TODO nextcord.roleselect
# TODO make a color preview image instead of emojis
# TODO make buttons for nudging the colors by 1 or 5 or so for each RGB


class ColorRoleCog(commands.Cog):
    def __init__(self, client, baselogger):
        global logger
        logger = baselogger.getChild(f"{__name__}logger")
        self.colorstopick = 4
        self.client = client
        self.getemoteserver.start()  #funky workaround but works

    @tasks.loop(count=1)
    async def getemoteserver(self):
        await self.client.wait_until_ready()
        self.emoteserver: discord.Guild = self.client.get_guild(957469186798518282)

    @discord.slash_command(name="mycolor", guild_ids=[860527626100015154, 601381789096738863, 409081549645152256, 552498097528242197, 800196118570205216], dm_permission=False)
    async def mycolor(self, interaction):
        pass

    class HexModal(discord.ui.Modal):
        def __init__(self, cog):
            self.cog = cog
            super().__init__(title="Pick your role color")
            self.hextext = discord.ui.TextInput(label="#", style=discord.TextInputStyle.short, placeholder="aabbcc", min_length=6, max_length=6)
            self.add_item(self.hextext)

        async def callback(self, ctx):
            dccolor = discord.Color(int(self.hextext.value, 16))
            # dccolor = discord.Color.from_rgb(*[int(self.hextext.value[i:i + 2], 16) for i in range(0, 5, 2)])
            await self.cog.setcustomcolor(ctx, dccolor)
            await ctx.send(embed=discord.Embed(title="Color changed", color=dccolor), ephemeral=True)

    class RGBModal(discord.ui.Modal):
        def __init__(self, cog):
            self.cog = cog
            super().__init__(title="Pick your role color")
            self.rtext = discord.ui.TextInput(label="R", style=discord.TextInputStyle.short, placeholder="0-255", max_length=3)
            self.add_item(self.rtext)
            self.gtext = discord.ui.TextInput(label="G", style=discord.TextInputStyle.short, placeholder="0-255", max_length=3)
            self.add_item(self.gtext)
            self.btext = discord.ui.TextInput(label="B", style=discord.TextInputStyle.short, placeholder="0-255", max_length=3)
            self.add_item(self.btext)

        async def callback(self, ctx):
            try:
                dccolor = discord.Color.from_rgb(int(self.rtext.value), int(self.gtext.value), int(self.btext.value))
                await self.cog.setcustomcolor(ctx, dccolor)
                await ctx.send(embed=discord.Embed(title="Color changed", color=dccolor), ephemeral=True)
            except Exception as e:
                await ctx.send(embed=discord.Embed(title="Invalid color", description=str(e)), ephemeral=True)

    class MyColorSelect(discord.ui.Select):
        def __init__(self, palette, emojis, cog):
            self.palette = palette
            self.cog = cog
            self.opts = [discord.SelectOption(label=f"({i[0]}, {i[1]}, {i[2]})", value=n, emoji=emojie) for (n, i), emojie in zip(enumerate(palette), emojis)]
            self.opts.append(discord.SelectOption(label="Close", emoji=emoji.emojize(":cross_mark:"), value="-1"))
            # self.opts = [discord.SelectOption(label=f"({i[0]}, {i[1]}, {i[2]})", value=n) for n, i in enumerate(palette)]
            super().__init__(placeholder="Pick a color", options=self.opts)

        async def callback(self, interaction: discord.Interaction):
            if self.values[0] != "-1":
                color = self.palette[int(self.values[0])]
                dccolor = discord.Color.from_rgb(*color)
                await self.cog.setcustomcolor(interaction, dccolor)
                await interaction.edit(view=None, embed=discord.Embed(title="Color changed", color=dccolor), delete_after=60)
            else:
                await interaction.edit(view=None, embed=discord.Embed(title="Cancelled", color=interaction.user.color), delete_after=5)
            emotes = [e for e in self.cog.emoteserver.emojis if e.name in ["a".join(map(str, color)) for color in self.palette]]
            for emote in emotes: #todo maybe remove all emojis that match the naming scheme if sometime ago they werent deleted?
                logger.debug(f"removing {emote}")
                await self.cog.emoteserver.delete_emoji(emote)

    class MyColorView(discord.ui.View):
        def __init__(self, palette, cog, user):
            self.palette = palette
            self.cog = cog
            self.user = user
            super().__init__(timeout=30)

        async def on_timeout(self):
            emotes = [e for e in self.cog.emoteserver.emojis if e.name in ["+".join(map(str, color)) for color in self.palette]]
            for emote in emotes:
                await self.cog.emoteserver.delete_emoji(emote) #todo delete message too

        # async def interaction_check(self, interaction: discord.Interaction) -> bool:
        #     return interaction.user == self.user

    async def setcustomcolor(self, interaction: discord.Interaction, dccolor) -> bool:
        highest_role = interaction.user.roles[-1]
        if highest_role.name.startswith("* "):
            await highest_role.edit(color=dccolor)
        else:
            if len(interaction.guild.roles) > 249:
                await interaction.send(embed=discord.Embed(title="This server's role limit has been reached.", color=discord.Color.red()), delete_after=60)
                return False
            highest_index = interaction.guild.roles.index(highest_role)
            newRole = await interaction.guild.create_role(name=f"* {interaction.user.name}'s color", color=dccolor)
            newRole = await newRole.edit(position=highest_index + 1)
            await interaction.user.add_roles(newRole)
            return True

    async def resetcustomcolor(self, interaction: discord.Interaction):
        oldRole = [role for role in interaction.user.roles if role.name.startswith("* ")]
        if oldRole:
            oldRole = oldRole[0]
            await oldRole.delete()

    @mycolor.subcommand(name="reset", description="Removes your pfp role color")
    async def mycolorreset(self, interaction: discord.Interaction):
        if await self.resetcustomcolor(interaction):
            await interaction.send("Done", ephemeral=True)

    @mycolor.subcommand(name="rgb", description="Pick a color from RGB values")
    async def mycolorrgb(self, interaction):
        modal = self.RGBModal(self)
        await interaction.response.send_modal(modal)

    @mycolor.subcommand(name="hex", description="Pick a color with a hex code")
    async def mycolorhex(self, interaction):
        modal = self.HexModal(self)
        await interaction.response.send_modal(modal)

    async def pickColorFromPic(self, interaction: discord.Interaction, image: discord.File):
        try:
            color_thief = ColorThief(image.fp)
            palette = list(set(color_thief.get_palette(color_count=self.colorstopick)))
            emojis = []
            if not self.emoteserver:
                self.emoteserver = self.client.get_guild(957469186798518282)
            assert self.emoteserver.emoji_limit - len(self.emoteserver.emojis) > self.colorstopick #TODO add if, warning and make separate emojis
            for n, color in enumerate(palette):
                im1 = npzeros((100, 100, 3), dtype='uint8')
                im1[:, :] = color
                with BytesIO() as image_binary:
                    imsave(image_binary, im1, format="png")
                    image_binary.seek(0)
                    emojis.append(await self.emoteserver.create_custom_emoji(name="a".join(map(str, color)), image=discord.File(fp=image_binary)))
            viewObj = self.MyColorView(palette, self, interaction.user)
            viewObj.add_item(self.MyColorSelect(palette, emojis, self))
            await interaction.send(view=viewObj)
        except Exception as e:
            await interaction.send(embed=discord.Embed(title="Error", description=str(e), color=discord.Color.red()), delete_after=60)

    @mycolor.subcommand(description="Lets you pick your color from any uploaded picture.")
    async def image(self, interaction, uploaded: discord.Attachment = discord.SlashOption(name="image", description="The image from which the colors are picked from.", required=True)):
        await interaction.response.defer()
        uploaded = await uploaded.to_file()
        await self.pickColorFromPic(interaction, uploaded)

    @mycolor.subcommand(description="Lets you pick your color from your profile picture.")
    async def pfp(self, interaction: discord.Interaction):
        await interaction.response.defer()
        image = await interaction.user.display_avatar.to_file()
        await self.pickColorFromPic(interaction, image)

    @mycolor.subcommand(description="Export a role color for easy sharing and use on other roles or servers.")
    async def export(self, interaction, role: discord.Mentionable = discord.SlashOption(name="role", description="The role to export the color of.", required=False, default=None)):
        if role:
            color = role.color
        else:
            color = interaction.user.color
        hexcode = str(color)
        embedVar = discord.Embed(title="Color", color=color)
        embedVar.add_field(name="hex", value=hexcode, inline=False)
        colors = (emoji.emojize(i) for i in [":red_square:", ":green_square:", ":blue_square:"])
        for key, val in zip(colors, color.to_rgb()):
            embedVar.add_field(name=f"{key}", value=f"{val}", inline=True)
        embedVar.fields[1].inline = False
        embedVar.set_footer(text=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
        await interaction.send(embed=embedVar)

def setup(client, baselogger): #TODO maybe add some logging messages
    client.add_cog(ColorRoleCog(client, baselogger))
