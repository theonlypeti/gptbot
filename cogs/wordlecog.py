import random
import nextcord as discord
from nextcord.ext import commands

class Wordlecog(commands.Cog):
    def __init__(self,client,baselogger):
        self.client = client
        with open("./data/wordlewords.txt","r") as file:
            self.words = file.readlines()
        self.games = []

    class WordleGame(discord.ui.View):
        def __init__(self, correct: str ,guess:str):
            self.word = correct
            super().__init__(timeout=1800)
            self.verifyGuess(guess)
            self.message = None
            self.embed = None

        def verifyGuess(self,guess:str): #this hurts
            if guess.lower() == self.word:
                self.embed = discord.Embed(title="Good job!",description=f"You guessed correctly, it was {self.word.upper()}",color=discord.Color.green())
                for child in self.children:
                    child.disabled = True
                return
            if len(self.children) == 25:
                self.embed = discord.Embed(title="Too bad!",description=f"You guessed {guess.upper()}. \nThe word was {self.word.upper()}",color=discord.Color.red())
                for child in self.children:
                    child.disabled = True
            else:
                letters = [None]*5
                rightletters = list(self.word)
                for i,(guessletter,rightletter) in enumerate(zip(guess.lower(),self.word)):
                    if guessletter == rightletter:
                        color = discord.ButtonStyle.green
                        rightletters.remove(guessletter)
                        letters[i] = self.Gomb(guessletter.upper(), color, False, self)
                locked = False
                for i,guessletter in enumerate(guess):
                    if guessletter in rightletters:
                        color = discord.ButtonStyle.red
                        rightletters.remove(guessletter)
                    else:
                        color = discord.ButtonStyle.gray
                    letters[i] = letters[i] or self.Gomb(guessletter.upper(), color, locked, self)
                [self.add_item(i) for i in letters]

        async def render(self):
            await self.message.edit(view=self,embed=self.embed)

        class Gomb(discord.ui.Button):
            def __init__(self,letter,color,locked,game):
                self.game = game
                super().__init__(style=color,label=letter,disabled=locked)

            async def callback(self,interaction):
                modal = self.game.WordGuessModal(self.game)
                await interaction.response.send_modal(modal)

        class WordGuessModal(discord.ui.Modal):
            def __init__(self,game):
                self.game = game
                super().__init__(title="Guess a word",auto_defer=True)

                self.guess = discord.ui.TextInput(max_length=5, min_length=5, label="Guess a word")
                self.add_item(self.guess)

            async def callback(self, ctx):
                guess = self.guess.value
                self.game.verifyGuess(guess)
                await self.game.render()

    @discord.slash_command(name="wordle",description="Start a game of wordle. Input a word to start guessing.")
    async def wordle(self,ctx,guess: str = discord.SlashOption(name="first_guess",required=True)):
        if len(guess) != 5:
            await ctx.send("Guess must be a 5 letter word.",delete_after=5)
            return
        game = Wordlecog.WordleGame(random.choice(self.words).strip(),guess)
        self.games.append(game)
        game.message = await ctx.send("Click on any of the letters to continue guessing.",view=game)

def setup(client,baselogger):
    client.add_cog(Wordlecog(client,baselogger))