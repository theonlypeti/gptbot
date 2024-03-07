import os
import nextcord as discord
from nextcord.ext import commands

TESTSERVER = (860527626100015154,)
root = os.getcwd()


class Testing(commands.Cog):
    def __init__(self, client):
        self.logger = client.logger.getChild(f"{self.__module__}")
        self.selection = None
        self.client: discord.Client = client
        """dont mind me lol"""


def setup(client):
    client.add_cog(Testing(client))
