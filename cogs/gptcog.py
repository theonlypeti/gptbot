import asyncio
import json
import os
import re
import textwrap
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
import EdgeGPT.EdgeGPT
import nextcord as discord
from BingImageCreator import ImageGenAsync
from EdgeGPT.EdgeGPT import Chatbot
from nextcord.ext import commands
from textwrap import TextWrapper
from EdgeGPT.EdgeUtils import Query, Cookie
from profanity_check import profanity_check
from tabulate import tabulate
import utils.embedutil
from utils import embedutil
from utils.webhook_manager import WebhookManager
from utils.levenstein import levenshtein_distance

root = os.getcwd()


class GptCog(commands.Cog):
    def __init__(self, client):
        self.logger = client.logger.getChild(f"{self.__module__}")
        self.client: discord.Client = client

    class TextInputModal(discord.ui.Modal):
        def __init__(self, chat, model, cog, msg, view):
            super().__init__(title="Reply to the bot")
            self.q = discord.ui.TextInput(label="Your reply", required=True, style=discord.TextInputStyle.paragraph)
            self.add_item(self.q)
            self.chat: EdgeGPT.EdgeGPT.Chatbot = chat
            self.model: str = model
            self.cog: GptCog = cog
            self.msg: discord.Message = msg
            self.view = view

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            for ch in self.view.children:
                ch.disabled = True
            self.view.children[-1].style = discord.ButtonStyle.green
            await self.msg.edit(view=self.view)
            await self.cog.askbot(interaction, self.chat, self.model, self.q.value)

    class SuggestionsView(discord.ui.View):
        def __init__(self, chat: EdgeGPT.EdgeGPT.Chatbot, msg: discord.Message):
            super().__init__(timeout=300.0)
            self.chat = chat
            self.msg = msg

        async def on_timeout(self) -> None:
            for ch in self.children:
                ch.disabled = True
            await self.msg.edit(view=self)
            await asyncio.sleep(60)  # in case someone has the modal open
            await self.chat.close()

    class SuggestionButton(discord.ui.Button):
        def __init__(self, label: str, chat: EdgeGPT.EdgeGPT.Chatbot, model: str, cog):
            super().__init__(label=label)
            self.chat: EdgeGPT.EdgeGPT.Chatbot = chat
            self.q = label
            self.model = model
            self.cog: GptCog = cog

        async def callback(self, interaction):
            await interaction.response.defer()
            self.style = discord.ButtonStyle.green
            self.view.children[-1].style = discord.ButtonStyle.gray
            for child in self.view.children:
                child.disabled = True
            await interaction.edit(view=self.view)
            await self.cog.askbot(interaction, self.chat, self.model, self.q)

    class CustomButton(discord.ui.Button):
        def __init__(self, chat, model: str, cog):
            super().__init__(label="Custom reply", style=discord.ButtonStyle.blurple)
            self.chat: EdgeGPT.EdgeGPT.Chatbot = chat
            self.model = model
            self.cog: GptCog = cog

        async def callback(self, interaction):
            modal = self.cog.TextInputModal(self.chat, self.model, self.cog, interaction.message, self.view)
            await interaction.response.send_modal(modal)

    @discord.slash_command(name="chatgpt")
    async def chatgpt(self, interaction):
        pass

    @chatgpt.subcommand(name="ask", description="Uses the cutting edge GPT-4 chat model to start a conversation")
    async def query2(self, interaction: discord.Interaction,
                     query: str,
                     model: str = discord.SlashOption(name="model",
                                                      description="What model to use when responding",
                                                      choices=("Creative", "Balanced", "Precise"),
                                                      default="Balanced",
                                                      required=False)):
        await interaction.response.defer(ephemeral=True)
        Cookie.dir_path = r"./data/cookies"
        Cookie.import_data()
        try:
            bot = await Chatbot.create(cookies=Cookie.current_data)
            # bot = await Chatbot.create()
        except Exception as e:
            embed = discord.Embed(title=query, description=e, color=discord.Color.red())
            await interaction.send(embed=embed, delete_after=180)
            raise e
        await self.askbot(interaction, bot, model, query)

    async def askbot(self, interaction: discord.Interaction, bot: EdgeGPT.EdgeGPT.Chatbot, model: str, query: str):
        model = model.lower()
        if any(profanity_check.predict(query.split(" "))):
            await embedutil.error(interaction, "Please refrain from using profanity in your queries. It can get the bot shadowbanned.", delete=30, ephemeral=False)
        async with WebhookManager(interaction) as whm:
            quest = await whm.send(content=query, username=interaction.user.display_name, avatar_url=interaction.user.avatar.url, wait=True)
        async with interaction.channel.typing():
            try:
                response = await bot.ask(prompt=query, conversation_style=model, simplify_response=True)

            except Exception as e:
                embed = discord.Embed(description=f"{e.__class__}: {e}", color=discord.Color.red())
                await interaction.send(embed=embed, delete_after=180)
                raise e
            embeds = []
            # if (response["sources_text"] in response["text"]) or (response["text"] in response["sources_text"]):
            lvnstn = levenshtein_distance(response["text"], response["sources_text"])
            self.logger.debug(f"{lvnstn=}")
            max_length = max(len(response["text"]), len(response["sources_text"]))
            self.logger.debug(f"{1-(lvnstn/max_length)=}")
            if (1 - (lvnstn / max_length)) > 0.9:
                combined_text = response["text"] # for when there are no sources to cite, sources_text is usually a carbon copy of text, not a perfect check but sometimes works
            else:
                combined_text = response["text"] + "\n" + "\n\u200b[".join(response["sources_text"].split("["))

            sources = response['sources_text'].split("](https://")
            self.logger.debug(sources)
            matches = re.findall(r"\[\^\d+\^\]", combined_text)  # replace [1] with markdown

            self.logger.debug(matches)
            for match in matches:
                #extract the digits from the match
                toreplace = re.findall(r"\d+", match)[0]
                self.logger.debug(toreplace)

                #make it a markdown hyperlink
                link = "https://" + sources[int(toreplace)].split(") [")[0]
                replacewith = f"[ [{toreplace}]]({link})"
                combined_text = combined_text.replace(match, replacewith)

            matches = re.findall(r"\[([^\]]+)\]\(\^(\d)\^\)", combined_text)  # replace [text](1) with markdown
            self.logger.debug(matches)
            for match in matches:
                # extract the digits from the match
                self.logger.debug(match)
                text, toreplace = match
                # make it a markdown hyperlink

                link = "https://" + sources[int(toreplace)].split(") [")[0]
                replacewith = f"[ [{text}]]({link})"
                combined_text = combined_text.replace(match, replacewith)

            # find tables tabulate them
            tables = re.findall(r"(?:^(?:\|.+?\|)+$\n?)+", combined_text, re.MULTILINE)
            if tables:
                for table in tables:
                    cells = [[cell.strip().strip("-").strip("*") for cell in row.split("|") if cell] for row in table.split("\n")]
                    columns = max(len(row) for row in cells)
                    maxwidth = 60
                    colwidth = (maxwidth // columns) - 2
                    newtable = [["\n".join([text for text in TextWrapper(width=colwidth, break_long_words=False, replace_whitespace=False).wrap(cell)]) for cell in row] for row in cells]
                    newtable = tabulate(newtable[2:], newtable[0], tablefmt="fancy_grid")
                    combined_text = combined_text.replace(table, f"```md\n{newtable}```")

            for text in TextWrapper(width=4000, break_long_words=False, replace_whitespace=False).wrap(combined_text):
                embed = discord.Embed(description=text, color=interaction.user.color)
                embeds.append(embed)
            viewObj = self.SuggestionsView(bot, None)
            if response["suggestions"]:
                for sugg in response["suggestions"]:
                    viewObj.add_item(self.SuggestionButton(sugg[:77] + "..." if len(sugg)>80 else sugg, bot, model, self))
            viewObj.add_item(self.CustomButton(bot, model, self))

            if response.get("image", None):
                embeds[0].set_image(url=response["image"])

            for emb in embeds[:-1]:  # todo why reply with the last one instead of first??
                await interaction.send(embed=emb)
            maxnum = response["max_messages"]
            msgnum = maxnum - response["messages_left"]
            embeds[-1].set_footer(text=f"Message limit: {msgnum}/{maxnum-1} |  Try your own conversation with /chatgpt ask")
            msg = await quest.reply(embed=embeds[-1], view=viewObj)
            viewObj.msg = msg

    @staticmethod
    async def askbotraw(interaction: discord.Interaction, bot: EdgeGPT.EdgeGPT.Chatbot, model: str, query: str, title: str = None):
        model = model.lower()
        try:
            response = await bot.ask(prompt=query, conversation_style=model, simplify_response=True)
        except Exception as e:
            embed = discord.Embed(title=title or (query[:253] + "...") if len(query) > 255 else query, description=e, color=discord.Color.red())
            await interaction.send(embed=embed, delete_after=180)
            raise e
        embeds = []

        out = response["text"]

        tables = re.findall(r"(?:^(?:\|.+?\|)+$\n?)+", out, re.MULTILINE)
        if tables:
            for table in tables:
                out = out.replace(table, f"```md\n{table}```")

        for text in TextWrapper(width=4000, break_long_words=False, replace_whitespace=False).wrap(out):
            embed = discord.Embed(title=title or (query[:253] + "...") if len(query) > 255 else query, description=text, color=interaction.user.color)
            embeds.append(embed)

        for emb in embeds:
            await interaction.send(embed=emb)

    @chatgpt.subcommand(name="images", description="Uses the cutting edge DALL-E 3 model to generate 4 images based on your prompt")
    async def imgen(self, interaction: discord.Interaction, prompt: str):
        Cookie.dir_path = r"./data/cookies"
        Cookie.import_data()
        Query.image_dir_path = r"./data/images"

        # embeds = []
        # Fetches image links
        # Add embed to list of embeds
        # [embeds.append(discord.Embed(url="https://www.bing.com/").set_image(url=image_link)) for image_link in images]
        # await interaction.send(txt, embeds=embeds, wait=True)
        msg = await interaction.send(f"Generating: `{prompt}`\nThis may take a while, please be patient.")
        msg = await msg.fetch()
        async with interaction.channel.typing():
            async with ImageGenAsync(all_cookies=Cookie.current_data) as image_generator:
                # async with ImageGenAsync(Cookie.image_token) as image_generator:
                try:
                    images = await image_generator.get_images(prompt)
                    await msg.reply(images[0])
                    for i in images[1:]:
                        await interaction.channel.send(i)
                except Exception as e:
                    await interaction.send(f"Error \n{e}")
                    raise e
            # await image_generator.save_images(images, output_dir=Query.image_dir_path)

    @chatgpt.subcommand(description="Just a silly little experiment.")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from EdgeGPT.EdgeUtils import Query, Cookie
        Cookie.dir_path = r"./data/cookies"
        Cookie.import_data()
        Query.image_dir_path = r"./data/images"

        querystr = "make up a random new pg-rated meme picture or scenario that is not a cat in a kitchen in your head that will not get blocked by content filters. Describe it as an image generator prompt. Caption the image and return these two strings as json using the keywords: prompt and caption. Make sure it is in json format using curly braces too."

        try:
            query = Query(prompt=querystr, cookie_files={Cookie.dir_path + i for i in os.listdir(Cookie.dir_path)}, style="creative")
            await query.log_and_send_query(echo=False, echo_prompt=False)
        except Exception as e:
            await utils.embedutil.error(interaction, str(e))
            raise e
        self.logger.debug(query)
        if query.code is None or True:
            resp = query.output[query.output.index("{"):]
            self.logger.debug(resp)
            response = json.loads(resp.strip("`"))
        else:
            response = query.code #type: dict[str, str]
        self.logger.debug(response)
        prompt = response["prompt"]
        caption = response["caption"]

        caption = "\n".join(textwrap.wrap(caption, width=40, break_long_words=False, replace_whitespace=False))

        async with ImageGenAsync(all_cookies=Cookie.current_data) as image_generator:
            # async with ImageGenAsync(Cookie.image_token) as image_generator:
            try:
                images = await image_generator.get_images(prompt)
                # await interaction.send(images[0])
                # await image_generator.save_images(images, output_dir=Query.image_dir_path)
                img = Image.open(requests.get(images[0], stream=True).raw)
                d = ImageDraw.Draw(img)

                mult = ((100 - len(caption) * 2) / 100)
                textsize = (img.width // 10) * max(mult, 0.5)
                textsize = int(max(textsize, 20))  # todo devize an algorithm to determine optimal size
                fnt = ImageFont.truetype('impact.ttf', size=textsize)

                textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": img.width // 100,
                              "fill": (255, 255, 255), "anchor": "md"}
                d.multiline_text((img.width / 2, img.height - textsize), caption, **textconfig)

            except Exception as e:
                await utils.embedutil.error(interaction, str(e))
                raise e
            with BytesIO() as output:
                img.save(output, format="PNG")
                output.seek(0)
                await interaction.send(file=discord.File(output, "meme.png"))

    @discord.slash_command(name="summarize")
    async def summarize_convo(self, interaction: discord.Interaction, num_msgs: int = 25):
        await interaction.response.defer()
        ch: discord.TextChannel = interaction.channel
        prompt = "Summarize the following chat:\n"
        for message in reversed(await ch.history(limit=num_msgs+1, oldest_first=False).flatten()):
            prompt += f"{message.author.global_name or message.author.name}: {message.content}" + (f"({len(message.attachments)} attachments)" if message.attachments else "") + (f"({len(message.embeds)} embeds: {[i.title for i in message.embeds]})" if message.embeds else "") + "\n"

        self.logger.debug(f"Resulting prompt: {len(prompt)} chars/4000 long.")
        Cookie.dir_path = r"./data/cookies"
        Cookie.import_data()
        try:
            bot = await Chatbot.create(cookies=Cookie.current_data)
            # bot = await Chatbot.create()
        except Exception as e:
            embed = discord.Embed(title=prompt, description=e, color=discord.Color.red())
            await interaction.send(embed=embed, delete_after=180)
            raise e
        await self.askbotraw(interaction, bot, "Creative", prompt, "Summary")


def setup(client):
    client.add_cog(GptCog(client))
