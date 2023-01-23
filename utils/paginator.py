from math import ceil
from typing import Callable, Sequence
import emoji
import nextcord as discord


class Paginator(discord.ui.View):
    """A paginator for embeds, with a back and forward button, and a definable select.
    :ivar page: The current page.
    :ivar maxpages: The maximum number of pages.
    :ivar inv: The inventory of items to paginate.
    :ivar itemsOnPage: The number of items to display on a page.
    :ivar mykwargs: The kwargs to pass to the embed and select factory function.
    :ivar msg: The message that the paginator is displayed in.

    :param func: The function that returns the embed to be displayed. It must take the paginator object as a parameter, which contains all the above attributes.
    :param select: The function that returns the select to be displayed. It must take the paginator object as a parameter, which contains all the above attributes.
    :param timeout: The timeout for the paginator. Seconds until it is automatically disabled.
    :param inv: See above.
    :param itemsOnPage: See above.
    :param kwargs: See above.

    Add a back button manually with View.add_item, appropriate to the situation you are in."""
    def __init__(self, func, select, inv, itemsOnPage: int = 25, timeout: int = 180, kwargs=None):
        self.mykwargs = kwargs or set()
        self.page: int = 0
        self.maxpages: int = 0  # to be rewritten on update
        self.func: Callable[..., discord.Embed] | None = func
        self.select: Callable[..., discord.ui.Select] | None = select
        self.itemsOnPage: int = itemsOnPage
        self.inv: Sequence = inv
        self.msg: discord.Message | None = None
        super().__init__(timeout=timeout)
        self.update()
        if self.select:
            self.add_item(select(pagi=self))

    @discord.ui.button(emoji=emoji.emojize(':last_track_button:'), row=1, custom_id=f"leftbutton")
    async def back(self, button, interaction: discord.Interaction):
        """The previous page button."""
        self.page = (self.page - 1) % self.maxpages
        await self.render(interaction)

    @discord.ui.button(emoji=emoji.emojize(':next_track_button:'), row=1, custom_id=f"rightbutton")
    async def forw(self, button, interaction: discord.Interaction):
        """The next page button."""
        self.page = (self.page + 1) % self.maxpages
        await self.render(interaction)

    async def on_timeout(self) -> None:
        """Called when the paginator times out."""
        for ch in self.children:
            ch.disabled = True
        await self.msg.edit(view=self)

    def update(self) -> None:
        """Updates the paginator.
        This is called automatically when the buttons are pressed and the paginator is rendered.
        Disables the paginator buttons if there is only one page."""
        self.maxpages = ceil(len(self.inv) / self.itemsOnPage)  # in case the inventory changes
        self.page = min(self.page, self.maxpages-1)
        if len(self.inv) <= self.itemsOnPage:
            for ch in self.children:
                if ch.custom_id in ("leftbutton", "rightbutton"):
                    ch.disabled = True

    # Add a back button manually with View.add_item, appropriate to the situation you are in

    async def render(self, interaction: discord.Interaction, ephemeral: bool = False) -> None:
        """Renders the paginator.
        :param interaction: The interaction that triggered the paginator. Can be an interaction or a message.
        :param ephemeral: Whether to send the paginator as an ephemeral message."""
        self.update()
        if self.select:
            for n, child in enumerate(self.children):
                if child.custom_id == "select":
                    self.children[n] = self.select(self)
                    break
        if interaction.message:  # if it's an interaction, ergo it is sent for the first time
            if self.func:
                await interaction.edit(embed=self.func(self), view=self)
            else:
                await interaction.edit(view=self)
        else:  # if it's a message, ergo it is to be edited
            if self.func:
                self.msg = await interaction.send(embed=self.func(self), view=self, ephemeral=ephemeral)
            else:
                self.msg = await interaction.send(view=self, ephemeral=ephemeral)
