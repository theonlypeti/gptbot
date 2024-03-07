import discord
from nextcord import Object


def mentionCommand(client, command, guild: int = None, raw: bool = False) -> str:
    try:
        every: list[discord.SlashApplicationCommand] = client.get_all_application_commands()
        cmdname = command.split(" ")[0]
        for i in every:
            if i.name == cmdname:
                if guild:
                    guild = Object(guild)
                ment = i.get_mention(guild or None)
                ment = ment.partition(":")
                ment = "</" + command + "".join(ment[1:])
                return f"{'`' if raw else ''}{ment}{'`' if raw else ''}"
    except ValueError as e:
        return str(e)

