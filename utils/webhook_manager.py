import nextcord as discord
from utils import embedutil


class WebhookManager:
    """Context manager for creating or accessing existing webhooks
        :param interaction: The interaction object
        :param channel: The channel to create the webhook in. Defaults to the interaction channel.
        :return: The webhook object

        Usage:

        async with WebhookManager(interaction) as wh:

        --->await wh.send("hello")"""

    def __init__(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        self.interaction = interaction
        self.channel = channel or interaction.channel

    async def __aenter__(self):
        try:
            whs = await self.channel.webhooks()
        except discord.errors.Forbidden as e:
            # self.logger.warning(e)
            await embedutil.error(self.interaction, "I don't have permissions to create webhooks in this channel")
            raise e
        else:
            wh = discord.utils.find(lambda wh: wh.name == f"emotehijack{self.channel.id}", whs)
            if not wh:
                wh = await self.channel.create_webhook(name=f"emotehijack{self.channel.id}")
        await self.interaction.send("done", ephemeral=True, delete_after=5)
        return wh

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
