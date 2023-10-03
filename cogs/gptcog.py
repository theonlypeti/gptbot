import asyncio
import os
import re
import EdgeGPT.EdgeGPT
import nextcord as discord
from BingImageCreator import ImageGenAsync
from EdgeGPT.EdgeGPT import Chatbot
from nextcord.ext import commands
from textwrap import TextWrapper

root = os.getcwd()


class GptCog(commands.Cog):
    def __init__(self, client):
        self.logger = client.logger.getChild(__name__)
        self.client: discord.Client = client

    class TextInputModal(discord.ui.Modal):
        def __init__(self, chat, model, cog, msg, view):
            super().__init__(title="Reply to the bot")
            self.q = discord.ui.TextInput(label="Your reply", required=True)
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
            async with interaction.channel.typing():
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
            await asyncio.sleep(60)  #in case someone has the modal open
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
            async with interaction.channel.typing():
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

    @chatgpt.subcommand(name="ask")
    async def query2(self, interaction: discord.Interaction,
                     query: str,
                     model: str = discord.SlashOption(name="model",
                                                      description="What model to use when responding",
                                                      choices=("Creative", "Balanced", "Precise"),
                                                      default="Balanced",
                                                      required=False)):
        from EdgeGPT.EdgeUtils import Cookie
        await interaction.response.defer()
        Cookie.dir_path = r"./data/cookies"
        Cookie.import_data()
        try:
            bot = await Chatbot.create(cookies=Cookie.current_data)
        except Exception as e:
            embed = discord.Embed(title=query, description=e, color=discord.Color.red())
            await interaction.send(embed=embed, delete_after=180)
            raise e
        await self.askbot(interaction, bot, model, query)

    async def askbot(self, interaction: discord.Interaction, bot: EdgeGPT.EdgeGPT.Chatbot, model:str, query:str):
        model = model.lower()
        try:
            response = await bot.ask(prompt=query, conversation_style=model, simplify_response=True)
            # self.logger.debug(response)
            # await bot.close()
        except Exception as e:
            embed = discord.Embed(title=query, description=e, color=discord.Color.red())
            await interaction.send(embed=embed, delete_after=180)
            raise e
        embeds = []
        # combined_text = response["text"] + "\n" + "\n [".join(response["sources_text"].split("["))
        if (response["sources_text"] in response["text"]) or (response["text"] in response["sources_text"]):
            combined_text = response["text"] #for when there are no sources to cite, sources_text is usually a carbon copy of text
        else:
            combined_text = response["text"] + "\n" + "\n\u200b[".join(response["sources_text"].split("["))
            matches = re.findall(r"\[\^\d+\^\]", combined_text)
            for match in matches:
                #extract the digits from the match
                toreplace = re.findall(r"\d+", match)[0]
                #make it a markdown hyperlink
                res = response['sources_text'].split("](https://")
                link = "https://" + res[int(toreplace)].split(") [")[0]
                replacewith = f"[ [{toreplace}]]({link})"
                combined_text = combined_text.replace(match, replacewith)
        # combined_text = response["text"] + "\n" + response["sources_text"]
        for text in TextWrapper(width=4000, break_long_words=False, replace_whitespace=False).wrap(combined_text):
            embed = discord.Embed(title=query[:253] + "..." if len(query)>256 else query, description=text, color=interaction.user.color)
            embeds.append(embed)
        viewObj = self.SuggestionsView(bot, None)
        if response["suggestions"]:
            for sugg in response["suggestions"]:
                viewObj.add_item(self.SuggestionButton(sugg[:77] + "..." if len(sugg)>80 else sugg, bot, model, self))
        viewObj.add_item(self.CustomButton(bot, model, self))
        for emb in embeds[:-1]:
            await interaction.send(embed=emb)
        maxnum = response["max_messages"]
        msgnum = maxnum - response["messages_left"]
        embeds[-1].set_footer(text=f"Message limit: {msgnum}/{maxnum}")
        msg = await interaction.send(embed=embeds[-1], view=viewObj)
        viewObj.msg = msg

    @chatgpt.subcommand(name="images")
    async def imgen(self, interaction: discord.Interaction, txt: str):
        await interaction.response.defer()
        from EdgeGPT.EdgeUtils import Query, Cookie
        Cookie.dir_path = r"./data/cookies"
        Cookie.import_data()
        Query.image_dir_path = r"./data/images"

        # embeds = []
        # Fetches image links
        # Add embed to list of embeds
        # [embeds.append(discord.Embed(url="https://www.bing.com/").set_image(url=image_link)) for image_link in images]
        # await interaction.send(txt, embeds=embeds, wait=True)

        async with ImageGenAsync(all_cookies=Cookie.current_data) as image_generator:
            # async with ImageGenAsync(Cookie.image_token) as image_generator:
            try:
                images = await image_generator.get_images(txt)
                await interaction.send(images[0])
                for i in images[1:]:
                    await interaction.channel.send(i)
            except Exception as e:
                await interaction.send(f"Error \n{e}")
                raise e
            # await image_generator.save_images(images, output_dir=Query.image_dir_path)


def setup(client):
    client.add_cog(GptCog(client))
