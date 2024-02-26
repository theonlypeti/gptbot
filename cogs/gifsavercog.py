import os
import nextcord as discord
from nextcord.ext import commands
import json
import emoji
root = os.getcwd()  #client.root exists
#TODO i could use autocomplete to return the gifs from the folder quickly


class GifCog(commands.Cog):
    def __init__(self, client):
        self.gifLogger = client.logger.getChild(f"{self.__module__}")
        self.client = client
        self.db = self.loadGifs()

    def loadGifs(self):
        try:
            with open(root + r"/data/gifsaver_db.txt", "r") as file:
                self.gifLogger.debug("loading gifs from file")
                return json.load(file)
        except IOError:
            self.gifLogger.info("no gifs file found, creating new one")
            with open(root + r"/data/gifsaver_db.txt", "w") as file:
                json.dump({}, file, indent=4)
            return {}

    def saveGifs(self):
        with open(root + r"/data/gifsaver_db.txt", "w") as file:
            json.dump(self.db, file, indent=4)

    class GifSaveFolderSelect(discord.ui.Select): 
        def __init__(self, folders, gif, cog):
            self.folders = folders
            self.cog = cog
            self.gif = gif
            optionen = []
            for k, v in folders.items(): #populating the select component with options #TODO: "The label of the option. This is displayed to users. Can only be up to 100 characters."
                optionen.append(discord.SelectOption(label=emoji.emojize(k), description=f"{len(v)}/24 spaces"))
            if len(optionen) < 25:
                optionen.append(discord.SelectOption(label="New folder", value="-1", emoji=emoji.emojize(":open_file_folder:")))
            super().__init__(placeholder="Select a folder to save into", options=optionen) #TODO: embedize
            
        async def callback(self, ctx):
            chosen = self.values[0]
            if chosen == "-1":
                modal = self.FolderGifNameInput(len(self.folders), self.folders, self.gif, self.cog)
                await ctx.response.send_modal(modal)
                await ctx.edit(view=None)

            else:
                if len(self.folders[chosen]) == 24:
                    ctx.send("That folder is full!")
                else:
                    modal = self.GifNameInput(self.folders[chosen], self.gif, self.cog)
                    await ctx.response.send_modal(modal)
                    await ctx.edit(view=None)
                    #savegif

        class FolderGifNameInput(discord.ui.Modal): 
            def __init__(self, nthfolder, user, gif, cog):
                self.user = user
                self.gif = gif
                self.cog = cog
                super().__init__(title="Save your GIF")

                self.folder = discord.ui.TextInput(max_length=100, min_length=3, label="Folder name", default_value=f"folder_{nthfolder}")
                self.add_item(self.folder)

                self.gifname = discord.ui.TextInput(max_length=100, min_length=3, label="GIF Name", placeholder="Give your gif a descriptive name, you can use emojis too!")
                self.add_item(self.gifname)
                
            async def callback(self, ctx):
                self.user[emoji.demojize(self.folder.value)] = {emoji.demojize(self.gifname.value): self.gif}
                self.cog.saveGifs()
                await ctx.send("Saved", ephemeral=True, delete_after=5.0)

        class GifNameInput(discord.ui.Modal): 
            def __init__(self, folder, gif, cog):
                self.gif = gif
                self.cog = cog
                self.folder = folder
                super().__init__(title="Save your GIF")

                self.gifname = discord.ui.TextInput(max_length=100, min_length=3, label="Name", placeholder="Give your gif a descriptive name, you can use emojis too!")
                self.add_item(self.gifname)
                
            async def callback(self, ctx):
                self.folder[self.gifname.value] = self.gif
                self.cog.saveGifs()
                await ctx.send("Saved", ephemeral=True, delete_after=5.0)
    

    @discord.message_command(name="Save GIF",guild_ids=[860527626100015154, 601381789096738863, 800196118570205216])
    async def savegif(self, ctx, msg):
            #msg = msg.embeds[0].image.url
        #else:
        msg = msg.content
        viewObj = discord.ui.View()
        
        try:
            viewObj.add_item(self.GifSaveFolderSelect(self.db[str(ctx.user.id)], msg, self))
        except KeyError:
            self.db[str(ctx.user.id)] = {}
            viewObj.add_item(self.GifSaveFolderSelect(self.db[str(ctx.user.id)], msg, self))
        await ctx.send("select foldah", view=viewObj, ephemeral=True)

    class GifLoadFolderSelect(discord.ui.Select):
        def __init__(self, ctx, msg, giffolders):
            self.ogctx = ctx
            self.msg = msg
            self.giffolders = giffolders
            optionen = [discord.SelectOption(label=emoji.emojize(i), value=i) for i in list(self.giffolders.keys())]
            super().__init__(options=optionen, placeholder="Select a folder to pick a GIF from")

        async def callback(self, ctx):
            folder = self.values[0]
            viewObj = discord.ui.View()
            viewObj.add_item(self.GifLoadSelectDropdown(self.giffolders[folder],self.msg))
            await ctx.response.edit_message(view=viewObj)

        class GifLoadSelectDropdown(discord.ui.Select):
            def __init__(self, folder, msg):
                self.msg = msg
                self.folder = folder
                optionen = [discord.SelectOption(label=emoji.emojize(i), value=i) for i in list(folder.keys())]
                super().__init__(options=optionen, placeholder="Pick a GIF to send")

            async def callback(self, ctx):
                await ctx.edit(content="Done.", view=None, delete_after=5.0)
                #await self.msg.reply(content=self.folder[self.values[0]])
                embedVar = discord.Embed(title="GIF", type="rich")
                #embedVar.set_thumbnail(url=ctx.user.avatar.url)
                embedVar.set_image(url=self.folder[self.values[0]])
                embedVar.set_author(name=ctx.user.display_name, icon_url=ctx.user.avatar.url)
                await self.msg.reply(embed=embedVar)
                #await ctx.send(content=f"{ctx.user.display_name} says\n {self.folder[self.values[0]]}")

    # @discord.message_command(name="Reply with saved GIF",guild_ids=[860527626100015154,601381789096738863,800196118570205216])
    # async def replygif(self,ctx,msg):
    #     try:
    #         self.db[str(ctx.user.id)]
    #     except KeyError:
    #         #self.db[str(ctx.user.id)] = {} #do not make it here cuz next time they will try to reply with gif, it will find their key but with no folders
    #         await ctx.send("No saved gifs found.",ephemeral=True)
    #         return
    #     viewObj = discord.ui.View()
    #     viewObj.add_item(self.GifLoadFolderSelect(ctx,msg,self.db[str(ctx.user.id)]))
    #     await ctx.send(view=viewObj,ephemeral=True)


def setup(client):
    client.add_cog(GifCog(client))
