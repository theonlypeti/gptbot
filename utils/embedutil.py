from nextcord import Embed, Interaction, TextChannel, Color, Message, Member


async def error(interaction: Interaction|TextChannel, txt: str, delete = 5.0, ephemeral=True) -> Message:
    if isinstance(interaction, Interaction):
        return await interaction.send(embed=Embed(description=txt, color=Color.red()), ephemeral=ephemeral, delete_after=delete)
    else:
        return await interaction.send(embed=Embed(description=txt, color=Color.red()), delete_after=delete)


async def success(interaction: Interaction | TextChannel, txt: str, delete=5.0, ephemeral=True) -> Message:
    if isinstance(interaction, Interaction):
        return await interaction.send(embed=Embed(description=txt, color=Color.green()), ephemeral=ephemeral, delete_after=delete)
    else:
        return await interaction.send(embed=Embed(description=txt, color=Color.green()), delete_after=delete)


def setuser(embed: Embed, user: Member) -> Embed:
    embed.set_footer(text=f"{user.name}", icon_url=user.avatar.url)
    embed.colour = user.color
    return embed
