import re
from datetime import datetime
from io import BytesIO
from math import inf
from typing import List
import imageio
import nextcord as discord
from PIL import Image, ImageDraw, ImageFont
from nextcord.ext import commands
from nextcord.utils import escape_markdown
from sympy import latex, Integral, Limit, Derivative, Rational, Symbol, Sum
import sympy.logic.boolalg as alg
from sympy.stats import Die, Bernoulli, P, density, FiniteRV
from utils.azasolver import piautomat

#TODO more translation tables for == and stuff
#TODO probabilita za predpoklad P subfix A (B), či su suvisle

tt = {"oo":inf,"inf":inf,"infinity":inf,"∞":inf} | {"-oo":inf,"-inf":-inf,"-infinity":-inf,"-∞":-inf}

def correctmultiplication(expression: str) -> str:
    found = re.findall("[0-9][a-z]", expression)
    replaced = [f"{i[0]}*{i[1]}" for i in found]
    for i, j in zip(found, replaced):
        expression = expression.replace(i, j, 1)
    return expression

def correctboolean(expr):
    return expr.replace("!", "~").replace("||","|").replace("&&", "&")

def addbackground(url: str):
    img = imageio.imread_v2(url)
    img[:, :, 3] = 255
    return img


async def sendmsg(ctx, embedVar, img: List[imageio.core.Array]):
    with BytesIO() as image_binary:
        imageio.imsave(image_binary, img[0], "png")
        image_binary.seek(0)
        with BytesIO() as another_image:
            imageio.imsave(another_image, img[1], "png")
            another_image.seek(0)
            await ctx.send("Result of:", embed=embedVar, files=[discord.File(fp=image_binary, filename='question.png'),
                                                  discord.File(fp=another_image, filename="result.png")])


class SympyCog(commands.Cog):
    def __init__(self, client, baselogger):
        self.client = client
        global sympylogger
        sympylogger = baselogger.getChild("SympyLogger")

    class SimplifyModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Simplify boolean expression")
            self.expression = discord.ui.TextInput(label="Expression", required=True, placeholder="(a & b) | (!a & !b)")
            self.add_item(self.expression)

        async def callback(self, ctx):
            await ctx.response.defer()
            expression = self.expression.value
            myexpression = correctboolean(expression)
            try:
                result = str(alg.simplify_logic(myexpression)).replace("~", "!")
                embedVar = discord.Embed(title=f'Result of {escape_markdown(expression)}', description=escape_markdown(str(result)), color=ctx.user.color)
                await ctx.send(embed=embedVar)
            except Exception as e:
                sympylogger.error(e)
                await ctx.send(embed=discord.Embed(title="Error", description=e, color=ctx.user.color))

    class SubsModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Solve boolean expression")
            self.expression = discord.ui.TextInput(label="Expression", required=True, placeholder="(a & b) | (!a & !b)")
            self.add_item(self.expression)

            self.subs = discord.ui.TextInput(label="Values", required=True, placeholder="a=1,b=0")
            self.add_item(self.subs)

        async def callback(self, ctx):
            await ctx.response.defer()
            expression = self.expression.value
            myexpression = correctboolean(expression)
            subs = self.subs.value
            try:
                subs = {a[0]: int(a[1]) for a in [a.strip(" ").split("=") for a in subs.split(",")]}
                result = str(alg.simplify_logic(myexpression).subs(subs)).replace("~", "!")
                embedVar = discord.Embed(title=f'Result of {escape_markdown(expression)}', description=escape_markdown(str(result)), color=ctx.user.color)
                await ctx.send(embed=embedVar)
            except Exception as e:
                sympylogger.error(e)
                await ctx.send(embed=discord.Embed(title="Error", description=e, color=ctx.user.color))

    class IntegralModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Integral calculator")
            self.expression = discord.ui.TextInput(label="Expression ∫[_] dx'", required=True)
            self.add_item(self.expression)

            self.symbol = discord.ui.TextInput(label="Integrate for ∫x d[_]", required=True, default_value="x")
            self.add_item(self.symbol)

            self.lower = discord.ui.TextInput(label="Lower bound (use -oo or -inf for -∞)", default_value="0", required=True)
            self.add_item(self.lower)

            self.upper = discord.ui.TextInput(label="Upper bound (use oo or inf for ∞)", default_value="x", required=True)
            self.add_item(self.upper)

        async def callback(self, ctx):
            await ctx.response.defer()
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
                integr = Integral(expression, (symbol, lower, upper))
                result = integr.doit()
                #result = integrate(expression, (symbol, lower, upper))
                embedVar = discord.Embed(title=f'Result of ∫{escape_markdown(expression)} d{symbol} from {lower} to {upper}', description=escape_markdown(str(result)), color=ctx.user.color)
                latexed = latex(result).replace(" ", "%20")
                question = addbackground(f'https://latex.codecogs.com/png.image?{latex(integr).replace(" ","%20")}')
                img = addbackground(f'https://latex.codecogs.com/png.image?{latexed}')
                await sendmsg(ctx, embedVar, [question, img])
            except Exception as e:
                sympylogger.error(e)
                await ctx.send(embed=discord.Embed(title="Error", description=e, color=ctx.user.color))

    class DiffModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Derivation calculator")
            self.expression = discord.ui.TextInput(label="Expression [_]'", required=True)
            self.add_item(self.expression)

            self.symbol = discord.ui.TextInput(label="Derivate for", required=True, default_value="x")
            self.add_item(self.symbol)

            self.nth = discord.ui.TextInput(label="Nth derivative", default_value="1", required=False)
            self.add_item(self.nth)

        async def callback(self, ctx):
            await ctx.response.defer()
            expression = self.expression.value
            expression = correctmultiplication(expression)
            try:
                ticks = int(self.nth.value)*"'"
                der = Derivative(expression, self.symbol.value, self.nth.value)
                result = der.doit()
                embedVar = discord.Embed(title=f'Result of {escape_markdown(expression)}{ticks} for {self.symbol.value}', description=escape_markdown(str(result)), color=ctx.user.color)
                latexed = latex(result).replace(" ", "%20")
                #questionimg = addbackground(f"https://latex.codecogs.com/png.image?Result\medspace%20of%20\medspace%20{latex(der).replace(' ', '%20')}")
                questionimg = addbackground(f"https://latex.codecogs.com/png.image?{latex(der).replace(' ', '%20')}")
                img = addbackground(f'https://latex.codecogs.com/png.image?{latexed}')
                await sendmsg(ctx, embedVar, [questionimg, img])
            except Exception as e:
                sympylogger.error(e)
                await ctx.send(embed=discord.Embed(title="Error", description=e, color=ctx.user.color))

    class LimitModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Limit calculator")
            self.expression = discord.ui.TextInput(label="Expression lim(_)", required=True)
            self.add_item(self.expression)
            self.going_from = discord.ui.TextInput(label="Where [_]->_", required=True, placeholder="x")
            self.add_item(self.going_from)
            self.going_to = discord.ui.TextInput(label="is approaching _->[_]", placeholder="inf", required=True)
            self.add_item(self.going_to)

        async def callback(self, ctx):
            await ctx.response.defer()
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
            question = ""
            try:
                lim = Limit(expression, going_from, going_to)
                question = latex(lim).replace(" ", "%20") or "Error"
                result = lim.doit()
            except Exception as e:
                sympylogger.error(e)
                result = "Error"
            embedVar = discord.Embed(title=f"Result of lim({escape_markdown(expression)}) {going_from}->{going_to}", description=escape_markdown(str(result)),color=ctx.user.color)
            latexed = latex(result).replace(" ", "%20")
            questionpic = addbackground(f"https://latex.codecogs.com/png.image?{question if question else 'Error'}")
            img = addbackground(f'https://latex.codecogs.com/png.image?{latexed}')
            await sendmsg(ctx, embedVar, [questionpic, img])

    class ProbModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Probabilty calculator")
            self.chances = discord.ui.TextInput(label="Objekt s probabilitou", required=True, placeholder="kocka / minca / d20 alebo d(n) / {1:1/4,2:3/4}")
            self.add_item(self.chances)
            self.count = discord.ui.TextInput(label="Počet objektov (n)", required=True)
            self.add_item(self.count)
            self.expression = discord.ui.TextInput(label="Výhodný pokus", placeholder="sum(hod) > max(hod)/2 and sum(hod)%2", required=True)
            self.add_item(self.expression)
            self.zapravd = discord.ui.TextInput(label="Za pravdepodobnosti", placeholder="hod[0]%2", required=False)
            self.add_item(self.zapravd)

        def makedict(self, string: str) -> dict:
            #TODO make = and : both usable
            lis = string.strip("{}").split(",")
            dic = {Symbol(i[0]) if not i[0].isnumeric() else i[0]: Rational(r[0], r[1]) if (r := i[1].split("/")) else i[1] for i in [o.split(":") for o in lis]}
            return FiniteRV(Symbol(f"{datetime.now()}"), dic)

        async def callback(self, ctx):
            await ctx.response.defer()
            try:
                n = int(self.count.value)
            except ValueError:
                n = 1
            kocka = Die("default")
            minca = Bernoulli("minca", 1/2)
            obj = self.chances.value.lower() #todo regex this d20
            hod = [Die(str(i)) if obj == "kocka" else Bernoulli(str(i), 1/2) if obj == "minca" else Die(str(i), sides=int(obj[1:])) if obj.startswith("d") else self.makedict(obj) for i in range(n)]
            expression = self.expression.value
            expression = expression.replace("max(hod)", "max(density(sum(hod)).dict.keys())")
            expression = expression.replace("min(hod)", "min(density(sum(hod)).dict.keys())")
            expression = eval(expression)
            sympylogger.debug(expression)

            zapravd = self.zapravd.value
            zapravd = zapravd.replace("max(hod)", "max(density(sum(hod)).dict.keys())")
            zapravd = zapravd.replace("min(hod)", "min(density(sum(hod)).dict.keys())")
            #zapravd = eval(zapravd) if zapravd else None
            sympylogger.debug(zapravd)
            try:
                result = P(expression, given_condition=eval(zapravd) if zapravd else None)
            except Exception as e:
                sympylogger.debug(e)
                try:
                    result = density(expression, condition=eval(zapravd) if zapravd else None)
                    sympylogger.debug(result)
                    result = {j: Rational(i.p * (max([j.q for j in result.values()]) / i.q), max([j.q for j in result.values()]), gcd=1) for j, i in result.items()}
                    result = "\n".join((f"{k}={v}" for k, v in result.items()))
                except Exception as f:
                    sympylogger.error(e)
                    result = f"{e}\n{f}"
            embedVar = discord.Embed(description=escape_markdown(f"Result of {n} * {obj} where {self.expression.value} {'if' if zapravd else ''} {self.zapravd.value}:\n----------\n{result} ") , color=ctx.user.color)
            await ctx.send(embed=embedVar)

    class AzaModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Automat calculator")
            self.pstring = discord.ui.TextInput(label="P string", required=True)
            self.add_item(self.pstring)
            # self.tofind = discord.ui.TextInput(label="Hladany string", required=True)
            # self.add_item(self.tofind)

        async def callback(self, ctx: discord.Interaction):
            await ctx.response.defer()
            pstring = self.pstring.value
            tab = piautomat(pstring)
            rows = tab.split("\n")
            width = len(rows[0])
            height = len(rows)
            ni = Image.new("RGB", (width * 10, height * 20), (0, 0, 0, 255))
            d = ImageDraw.Draw(ni)
            textsize = 18
            fnt = ImageFont.truetype('consola.ttf', size=textsize)
            textconfig = {"font": fnt, "stroke_fill": (0, 0, 0), "stroke_width": 0,
                          "fill": (255, 255, 255), "anchor": "mm"}
            d.multiline_text((ni.width // 2, ni.height // 2), tab, **textconfig)
            embedVar = discord.Embed(title=pstring)
            embedVar.set_footer(text=ctx.user.name, icon_url=ctx.user.avatar.url)
            embedVar.timestamp = datetime.now()
            with BytesIO() as image_binary:
                ni.save(image_binary, "png")
                image_binary.seek(0)
                await ctx.send(embed=embedVar, file=discord.File(fp=image_binary, filename=f'table.png'))
            
    @discord.slash_command(name="mat", description="Kalkulačky pre predmet MAT")
    async def mat(self, ctx):
        pass

    @mat.subcommand(name="limit", description="Calculate limits")
    async def limit(self, ctx):
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

    @discord.slash_command(name="bool", description="Kalkulačky pre predmet LSI / (AS)")
    async def booltools(self, ctx: discord.Interaction):
        pass

    @booltools.subcommand(name="simplify", description="Simplify boolean expressions")
    async def simplyfybool(self, ctx: discord.Interaction):
        modal = self.SimplifyModal()
        await ctx.response.send_modal(modal)

    @booltools.subcommand(name="solve", description="Solve boolean expressions by substituting variables with 1/0 values.")
    async def solvebool(self, ctx):
        modal = self.SubsModal()
        await ctx.response.send_modal(modal)

    @discord.slash_command(name="matstat", description="Kalkulačky pre predmet MATSTAT")
    async def matstattools(self, ctx: discord.Interaction):
        pass

    @matstattools.subcommand(name="probablity", description="P(x) alebo Mn(x,n), šanca hodu n počet x kde sa splní zadaná podmienka")
    async def probability(self,ctx: discord.Interaction):
        modal = self.ProbModal()
        await ctx.response.send_modal(modal)

    @discord.slash_command(name="aza", description="Kalkulačky pre predmet AZA")
    async def azatools(self, ctx: discord.Interaction):
        pass

    @azatools.subcommand(name="automat", description="tabulka konecneho automatu spolu s pi tabulkou")
    async def azapitable(self, ctx: discord.Interaction):
        modal = self.AzaModal()
        await ctx.response.send_modal(modal)

def setup(client, baselogger):
    client.add_cog(SympyCog(client, baselogger))
