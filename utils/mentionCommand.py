def mentionCommand(client, command, guild: int = None, raw: bool = False) -> str:
    try:
        every = client.get_application_commands()
        cmdname = command.split(" ")[0]
        for i in every:
            if i.name == cmdname:
                return f"{'`' if raw else ''}{i.get_mention(guild or None)}{'`' if raw else ''}"
    except ValueError as e:
        return str(e)

