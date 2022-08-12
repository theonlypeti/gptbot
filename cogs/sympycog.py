import re
import nextcord as discord
from nextcord.ext import commands
from nextcord.utils import escape_markdown
from sympy import limit, diff, integrate, latex
from math import inf

tt = {"oo":inf,"inf":inf,"infinity":inf,"∞":inf} | {"-oo":inf,"-inf":-inf,"-infinity":-inf,"-∞":-inf}

def correctmultiplication(expression: str) -> str:
    found = re.findall("[0-9][a-z]", expression)
    replaced = [f"{i[0]}*{i[1]}" for i in found]
    for i, j in zip(found, replaced):
        expression = expression.replace(i, j, 1)
    return expression

class SympyCog(commands.Cog):
    def __init__(self,client,baselogger):
        self.client = client

    class IntegralModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Integral calculator")
            self.expression = discord.ui.TextInput(label="Expression ∫[_] dx'",required=True)
            self.add_item(self.expression)

            self.symbol = discord.ui.TextInput(label="Integrate for ∫x d[_]",required=True,default_value="x")
            self.add_item(self.symbol)

            self.lower = discord.ui.TextInput(label="Lower bound (use -oo or -inf for -∞)", default_value="0",required=True)
            self.add_item(self.lower)

            self.upper = discord.ui.TextInput(label="Upper bound (use oo or inf for ∞)", default_value="x",required=True)
            self.add_item(self.upper)

        async def callback(self, ctx):
            expression = self.expression.value
            expression = correctmultiplication(expression)
            symbol = self.symbol.value
            try:
                lower = tt[self.lower.value]
            except KeyError:
                lower = self.lower.value
            try:
                upper = tt[self.upper.value]
            except KeyError:
                upper = self.upper.value
            try:
                print(expression,type(expression))
                result = integrate(expression,(symbol,lower,upper))
                embedVar = discord.Embed(title=f'Result of ∫{escape_markdown(expression)} d{symbol} from {lower} to {upper}', description=escape_markdown(str(result)),color=ctx.user.color)
                latexed = latex(result).replace(" ","%20")
                embedVar.set_image(url=f'https://latex.codecogs.com/png.image?{latexed}')
                await ctx.send(embed=embedVar)
            except Exception as e:
                print(e)
                await ctx.send(embed=discord.Embed(title="Error", description=e,color=ctx.user.color))

    class DiffModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Derivation calculator")
            self.expression = discord.ui.TextInput(label="Expression [_]'",required=True)
            self.add_item(self.expression)

            self.symbol = discord.ui.TextInput(label="Derivate for",required=True,default_value="x")
            self.add_item(self.symbol)

            self.nth = discord.ui.TextInput(label="Nth derivative", default_value="1",required=False)
            self.add_item(self.nth)

        async def callback(self, ctx):
            expression = self.expression.value
            expression = correctmultiplication(expression)
            try:
                ticks = int(self.nth.value)*"'"
                result = diff(expression, self.symbol.value,self.nth.value)
                embedVar = discord.Embed(title=f'Result of {escape_markdown(expression)}{ticks} for {self.symbol.value}', description=escape_markdown(str(result)),color=ctx.user.color)
                latexed = latex(result).replace(" ","%20")
                embedVar.set_image(url=f'https://latex.codecogs.com/png.image?{latexed}')
                await ctx.send(embed=embedVar)
            except Exception as e:
                print(e)
                await ctx.send(embed=discord.Embed(title="Error", description=e,color=ctx.user.color))

    class LimitModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Limit calculator")
            self.expression = discord.ui.TextInput(label="Expression lim(_)",required=True)
            self.add_item(self.expression)
            self.going_from = discord.ui.TextInput(label="Where [_]->_",required=True,placeholder="x")
            self.add_item(self.going_from)
            self.going_to = discord.ui.TextInput(label="is approaching _->[_]", placeholder="inf",required=True)
            self.add_item(self.going_to)

        async def callback(self, ctx):
            expression = self.expression.value
            expression = correctmultiplication(expression)
            try:
                going_from = tt[self.going_from.value.lower()]
            except KeyError:
                going_from = self.going_from.value

            try:
                going_to = tt[self.going_to.value]
            except KeyError:
                going_to = self.going_to.value

            try:
                result = limit(expression,going_from,going_to)
            except Exception as e:
                print(e)
                result = "Error"
            embedVar = discord.Embed(title=f"Result of lim({escape_markdown(expression)}) {going_from}->{going_to}", description=escape_markdown(str(result)),color=ctx.user.color)
            latexed = latex(result).replace(" ","%20")
            embedVar.set_image(url=f'https://latex.codecogs.com/png.image?{latexed}')
            await ctx.send(embed=embedVar)
            
    @discord.slash_command(name="mat",description="Kalkulačky pre predmet MAT")
    async def mat(self,ctx):
        pass

    @mat.subcommand(name="limit", description="Calculate limits")
    async def limit(self,ctx):
        modal = self.LimitModal()
        await ctx.response.send_modal(modal)

    @mat.subcommand(name="derivate", description="Calculate derivate")
    async def differencial(self, ctx):
        modal = self.DiffModal()
        await ctx.response.send_modal(modal)

    @mat.subcommand(name="integrate", description="Calculate integrals")
    async def integrating(self, ctx):
        modal = self.IntegralModal()
        await ctx.response.send_modal(modal)

def setup(client,baselogger):
    client.add_cog(SympyCog(client,baselogger))
