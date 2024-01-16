import textwrap
from math import ceil
from typing import List
import nextcord as discord


class ColorGroup:
    def __init__(self, dccolor: discord.Colour, name: str = None, cmdcolor: str = None,
                 emote_s: str = None, emote_r: str = None, emote_h: str = None):
        self.dccolor = dccolor
        self.hex = str(dccolor)
        self.rgb = dccolor.to_rgb()
        self.emoji_round = emote_r
        self.emoji_square = emote_s
        self.emoji_heart = emote_h
        self.name = name
        self.cmdcolor = cmdcolor

    def string(self, input_string: str) -> str:
        return f"{self.cmdcolor}{input_string}\033[0m"

    def text(self, input_string: str) -> str:
        return f"```ansi\n{self.string(input_string)}\033[0m\n```"


class Rainbow(ColorGroup):
    def __init__(self, name: str = "Rainbow", emote_s: str = None, emote_r: str = None, emote_h: str = None):
        super().__init__(discord.Color.red(), name, None, emote_s, emote_r, emote_h)

    @classmethod
    def string(cls, text: str) -> str:
            colors = [Colored.red, Colored.yellow, Colored.green, Colored.blue, Colored.purple]
            texts = textwrap.wrap(text, round(len(text) / len(colors)))
            texts[4] = "".join(texts[4:])
            return "".join([f"{color.string(txt)}" for txt, color in zip(texts, colors)]) + "\033[0m"

    @classmethod
    def text(self, input_string: str) -> str:
        return f"```ansi\n{self.string(input_string)}\033[0m\n```"


class Colored:
    red = ColorGroup(discord.Colour.red(), "Red", "\033[31m", "🟥", "🔴", "❤️")
    blue = ColorGroup(discord.Colour.dark_blue(), "Blue", "\033[34m", "🟦", "🔵", "💙")
    green = ColorGroup(discord.Colour.green(), "Green", "\033[32m", "🟩", "🟢", "💚")
    yellow = ColorGroup(discord.Colour.gold(), "Yellow", "\033[33m", "🟨", "🟡", "💛")
    orange = ColorGroup(discord.Colour.orange(), "Orange", "\033[41m\033[37m", "🟧", "🟠", "🧡")
    purple = ColorGroup(discord.Colour.purple(), "Purple", "\033[35m", "🟪", "🟣", "💜")
    # pink = Color(discord.Colour.magenta(), "Pink", "pink", "??", "", "🩷")
    # aqua = Color(discord.Colour.blue(), "Aqua", "\033[36m", "??", "", "🩵")
    # grey = Color(discord.Colour.light_grey(), "Grey", "grey", "??", "", "🩶")
    white = ColorGroup(discord.Colour.from_rgb(240, 240, 240), "White", "\033[37m", "⬜", "⚪", "🤍")
    black = ColorGroup(discord.Colour.from_rgb(20, 20, 20), "Black", "\033[30m", "⬛", "⚫", "🖤")
    brown = ColorGroup(discord.Colour.dark_gold(), "Brown", "\033[41m\033[30m", "🟫", "🟤", "🤎")
    rainbow = Rainbow("Rainbow", "🌈", "🌈", "🌈")

    @classmethod
    def list(cls) -> dict[str, ColorGroup]:
        return {att: getattr(cls, att) for att in dir(cls) if not att.startswith("_") and att not in ("list", "get_color", "text", "rainbowstring")}
        # return {att: getattr(cls, att) for att in dir(cls) if not att.startswith("_") and not callable(att)}

    @classmethod
    def get_color(cls, name: str) -> ColorGroup:
        return getattr(cls, name)

    @classmethod
    def text(cls, texts: List[tuple[str, 'ColorGroup']]) -> str:
        combined = " ".join([clr.string(txt) if clr in Colored.list().values() else txt for txt, clr in texts])
        return f"```ansi\n{combined}\033[0m\n```"


