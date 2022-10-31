import asyncio
import logging
import random
from collections import defaultdict
from functools import partial
from typing import Union, List, Type, Iterable
import nextcord as discord
from nextcord.ext import commands
import numpy as np
import matplotlib.pyplot as plt
import emoji
from random import choices, choice, randint
from copy import deepcopy as new #very useful for equipping items
from funcy import print_durations
from numpy import Infinity
from utils.mapvalues import mapvalues

#manaicon = ':magic_wand:'
manaicon = ':comet:'
# manaicon = ':crystal_ball:'
roman_numerals = {1:"",2:"II",3:"III",4:"IV",5:"V",6:"VI",7:"VII",8:"VIII",9:"IX",10:"X"}


def chance(percent: Union[int, float]) ->bool:
    return choices((True, False), weights=(percent, 100-percent))[0]

class Noise(object):
    @staticmethod
    def perlin(x,y,seed=0):
        # permutation table
        np.random.seed(seed)
        p = np.arange(256,dtype=int)
        np.random.shuffle(p)
        p = np.stack([p,p]).flatten()
        # coordinates of the top-left
        xi = x.astype(int)
        yi = y.astype(int)
        # internal coordinates
        xf = x - xi
        yf = y - yi
        # fade factors
        u = Noise.fade(xf)
        v = Noise.fade(yf)
        # noise components
        n00 = Noise.gradient(p[p[xi]+yi],xf,yf)
        n01 = Noise.gradient(p[p[xi]+yi+1],xf,yf-1)
        n11 = Noise.gradient(p[p[xi+1]+yi+1],xf-1,yf-1)
        n10 = Noise.gradient(p[p[xi+1]+yi],xf-1,yf)
        # combine noises
        x1 = Noise.lerp(n00,n10,u)
        x2 = Noise.lerp(n01,n11,u) # FIX1: I was using n10 instead of n01
        return Noise.lerp(x1,x2,v) # FIX2: I also had to reverse x1 and x2 here

    @staticmethod
    def lerp(a,b,x):
        "linear interpolation"
        return a + x * (b-a)

    @staticmethod
    def fade(t):
        "6t^5 - 15t^4 + 10t^3"
        return 6 * t**5 - 15 * t**4 + 10 * t**3

    @staticmethod
    def gradient(h,x,y):
        "grad converts h to the right gradient vector and return the dot product with (x,y)"
        vectors = np.array([[0,1],[0,-1],[1,0],[-1,0]])
        g = vectors[h%4]
        return g[:,:,0] * x + g[:,:,1] * y

    @staticmethod
    #@print_durations
    def makeGrid(size, factor, seed2):
        lin = np.linspace(0, 1, size, endpoint=False)
        x,y = np.meshgrid(lin, lin) # FIX3: I thought I had to invert x and y here but it was a mistake
        a=Noise.perlin(x, y, seed=seed2)
        return a

    @staticmethod
    #@print_durations
    def makeMap(size, factor, seed2):
        a = Noise.makeGrid(size, factor, seed2)
        grid = [[]]
        biggest,smallest = 0,1
        for line in a:
            biggest = max(max(list(line)), biggest) #maybe use np.clip? no dont, thats different
            smallest = min(min(list(line)), smallest)

        for row in a:
            for i in row:
                grid[-1].append(RPGGame.Tile(mapvalues(i, smallest, biggest, 0, 1)))
            grid.append([])
        #plt.imshow(a, origin='upper')
        #plt.show()
        return grid

def addLoot(inventory,loot):
    if isinstance(loot, RPGGame.Item):
        loot: List[RPGGame.Item] = [loot]
    elif isinstance(loot, dict):
        loot: Iterable[RPGGame.Item] = loot.values()
    for item in loot:
        if item.amount > 0:
            if item.display_name in inventory.keys():
                inventory[item.display_name].amount += item.amount
            else:
                inventory.update({item.display_name: item})

def removeItem(inventory, item):
    if item.display_name in inventory.keys():
        inventory[item.display_name].amount -= item.amount
        if inventory[item.display_name].amount <= 0:
            del inventory[item.display_name]


class RPGGame:
    class LvlUpButtons(discord.ui.View):
        def __init__(self, player):
            self.player = player
            super().__init__()

        @discord.ui.button(emoji=emoji.emojize(":fist:", language="alias"), label="STR", style=discord.ButtonStyle.red)
        async def strbutton(self, button, ctx):
            await ctx.response.defer()
            self.player._base_strength += 1
            await self.finishlevelup(ctx)

        @discord.ui.button(emoji=emoji.emojize(manaicon, language="alias"), label="INT", style=discord.ButtonStyle.blurple)
        async def intbutton(self, button, ctx):
            self.player._base_intelligence += 1
            await self.finishlevelup(ctx)

        @discord.ui.button(emoji=emoji.emojize(":man_running:", language="alias"), label="AGI", style=discord.ButtonStyle.green)
        async def agibutton(self, button, ctx):
            self.player._base_agility += 1
            await self.finishlevelup(ctx)

        @discord.ui.button(emoji=emoji.emojize(":x:", language="alias"), label="Back", style=discord.ButtonStyle.grey)
        async def backbutton(self, button, ctx):
            await RPGCog.backToMap(ctx, self.player)

        async def finishlevelup(self, ctx):
            self.player.levelup()
            await RPGCog.backToMap(ctx, self.player)

    class TargetSelectView(discord.ui.Select):
        def __init__(self, targets, attack, attacker, battle, myview):
            self.attacker: RPGGame.Player = attacker
            self.targets = targets
            self.attack: RPGGame.Spell | RPGGame.Weapon = attack
            self.battle = battle
            self.myview = myview
            # self.returnView = returnView
            options = [discord.SelectOption(label=i.display_name, description=i.showStats(), value=str(n)) for n,i in enumerate(targets) if i.hp > 0]
            if isinstance(self.attack, RPGGame.Spell):
                placeholdertext = f"Cast {self.attack.display_name} on..."
            else:
                placeholdertext = f"Deal {self.attacker.atk + self.attack.damage} damage to..."
            super().__init__(options=options, placeholder=placeholdertext)

        async def callback(self, interaction: discord.Interaction):
            selected: RPGGame.Entity = self.targets[int(self.values[0])]
            self.attack.use(self.attacker, selected)
            self.myview.stop()
            # await interaction.edit(view=self.returnView)

    class HandEquippable:
        ...

    class Spell(HandEquippable):
        def __init__(self, name, manacost: str | int, effects, selfeffects=None, hpcost: str|int = 0, duration: str|int = 0, cooldown: str|int=0, lvl=1, maxlvl=10, description=''):
            self.name = name
            self._manacost = manacost
            self.effects: List[RPGGame.Effect] = effects or []
            self.selfeffects: List[RPGGame.Effect] = selfeffects or [] #effects that are applied to the user regardless of target, something like weakening, or siphoning
            self._hpcost = hpcost
            self._duration = duration
            self._max_cooldown = cooldown
            self.cooldown: int = 0
            self.description: str = description
            self.lvl: int = lvl
            self.maxlvl: int = maxlvl
            self.weight = 0 # this is for player carry capacity calculation, im just a lazy fuck instead of checking if equipped thing is Item i just gave the spell a zero weight
            self.lvlup(0) # setting up the effects levels this are you
            super().__init__()

        def lvlup(self, lvls):
            self.lvl = min(self.lvl + lvls, self.maxlvl)
            for ef in self.effects:
                ef.lvl = self.lvl

        @property
        def manacost(self) -> int: #you can do something like manacost = 10 + 2 * self.lvl
            return int(eval(str(self._manacost)))

        @property
        def hpcost(self) -> int:
            return int(eval(str(self._hpcost)))

        @property
        def max_cooldown(self) -> int:
            return int(eval(str(self._max_cooldown)))

        @property
        def duration(self) -> int:
            return int(eval(str(self._duration)))

        def tickCd(self):
            self.cooldown = max(self.cooldown-1, 0)

        @property
        def costtext(self) -> str:
            manacoststr = f"({self.manacost} {emoji.emojize(manaicon, language='alias')})" if self.manacost else ''
            hpcoststr = f"({self.hpcost} {emoji.emojize(':red_heart:', language='alias')})" if self.hpcost else ''
            return f"{manacoststr} {'and' if self.manacost and self.hpcost else ''} {hpcoststr}"

        @property
        def display_name(self) -> str:
            cooldowntext = f"({self.cooldown} turns)"
            return f"{self.name} {roman_numerals[self.lvl]} {self.costtext if not self.cooldown else cooldowntext}"

        @property
        def listEffects(self) -> str:
            return " |".join((i.shorteffect for i in self.effects))

        def showStats(self) -> str:
            return self.listEffects

        def toDropdown(self, index) -> discord.SelectOption:
            return discord.SelectOption(label=self.display_name, description=f"{self.listEffects}", value=f"{index}") #todo add emoji?

        def __repr__(self):
            return f"{__class__}({self.display_name=},{self.lvl=},{self.manacost=},{self.duration=},{self.cooldown=},{self.effects=})"

        def use(self, user, target):
            if self.cooldown:
                return
            if user.mana >= self.manacost:
                user.mana -= self.manacost
                if not isinstance(target, list):
                    target = [target]
                for t in target:
                    for e in self.effects:
                        efkt = new(e)
                        efkt.wherefrom = f"{user.display_name}'s {self.name}"
                        t.effects.append(efkt)
                        logger.debug(t.effects)
                        efkt.target = t
                for e in self.selfeffects:
                    efkt = new(e)
                    efkt.wherefrom = f"{user.display_name}'s {self.name}"
                    user.effects.append(efkt)
                    efkt.target = user
                self.cooldown = self.max_cooldown

    class DirectSpell(Spell):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class FriendlySpell(DirectSpell):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)

    class EnemySpell(DirectSpell):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)

    class AOESpell(Spell):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)

    class EnemyAOESpell(AOESpell):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)

    class FriendlyAOESpell(AOESpell):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)

    #------------------------------------------

    class Entity(object):
        def __init__(self, name, hp, atk):
            self.display_name: str = name
            self.hp: int = hp
            self.atk: int = atk
            self.effects: List[RPGGame.Effect] = []
            self.stunned: bool = False

        # def tickEffects(self):
        #     for effect in self.effects:
        #         effect.tickEffect()

    class Enemy(Entity):
        def __init__(self, name, hp, atk, exp, gold, loot):
            self.xp: int = exp
            self.gold: range = gold
            self.lootTable: dict[RPGGame.Item, float] = loot  # {item:chance}
            self.mana: int = Infinity
            super().__init__(name, hp, atk)

        def __str__(self):
            return f"{self.display_name}: {self.hp}hp, {self.atk}atk"

        def showStats(self):
            effstr = ", ".join(f"{effect.name} ({effect.duration} turns)" for effect in self.effects)
            return f"{self.hp} {emoji.emojize(':red_heart:')}, {self.atk} {emoji.emojize(':dagger:')} {'|' if effstr else ''} {effstr}"

        def __repr__(self):
            return f"Enemy({self.display_name=},{self.hp=},{self.atk=},{self.effects=})"

        def recalculateStats(self): #TODO use @property decorator instead maybe? might be too invested in this
            self.stunned = False
            for effect in self.effects:
                effect: RPGGame.Effect = effect
                if hasattr(effect, "hpeffect"):
                    self.hp += int(effect.hpeffect["flat"]())
                    self.hp += int(self.hp * float(effect.hpeffect["multiplier"]()))
                    if seth := int(effect.hpeffect["set"]()) >= 0:
                        self.hp = seth

                if hasattr(effect, "atkeffect"):
                    self.atk += int(effect.atkeffect["flat"]())
                    self.atk += self.atk * float(effect.atkeffect["multiplier"]())
                    if seta := int(effect.atkeffect["set"]()) >= 0:
                        self.atk = seta

                if hasattr(effect, "stunned"):
                    self.stunned = effect.stun

                effect.tickEffect()

        def attack(self, targets): #TODO to be rewritten for each type of enemy, e.g. frost golem deals freeze effect
            target: RPGGame.Player = random.choice(targets)
            target.hp -= self.atk
            return f"{self.display_name} hit {target.display_name} for {self.atk}" #barbarian archer snipes x, frost golem freezes x

    class Undead(Enemy):
        def __init__(self, *args):
            super().__init__(*args)

    class Bandit(Enemy):
        def __init__(self, *args):
            super().__init__(*args)

    class Animal(Enemy):
        def __init__(self, *args):
            super().__init__(*args)

    #------------------------------------------

    class Item(object):
        def __init__(self, weight: int | None = 1, price: int | None = 0, amount=1, display_name="", flags=None):
            self.weight = weight
            self.price = price
            self.amount = amount
            self.display_name = display_name
            self.flags = flags or ()
            super().__init__()

        def __add__(self, other):
            if isinstance(other, RPGGame.Item):
                self.amount += other.amount
            elif isinstance(other, int):
                self.amount += other
            else:
                raise NotImplementedError(f"Summation of Item and {type(other)}")

        def __sub__(self, other):
            if isinstance(other, RPGGame.Item):
                amount = other.amount
            elif isinstance(other, int):
                amount = other
            else:
                raise NotImplementedError(f"Substraction of Item and {type(other)}")
            if amount > self.amount:
                raise ValueError(f"Cannot remove {amount} from {self.amount}")
            self.amount -= amount

        def __repr__(self):
            return f"{self.__class__.__name__}({self.display_name=},{self.amount=},{self.price=},{self.weight=})"

        def stats(self):
            weight = self.amount * self.weight if self.weight and self.amount else "--"
            return f"x {self.amount or '---'}|{emoji.emojize(':moneybag:',language='alias')} {self.price or '---'}|{emoji.emojize(':muscle:',language='alias')} {self.weight or '---'}"

    class Equipment(Item): #TODO make this into equipment, subclass equippable and make spells also equippable
        def __init__(self, enchant=None, material="Default", price=0, weight=1, amount=1, stat=0, itemtype=None, display_name=None):
            self.echant = enchant
            self.material = material
            self.type = itemtype
            self.stat = stat
            if not display_name:
                self.display_name = f"{self.material} {self.type}"
            else:
                self.display_name = display_name
            super().__init__(weight=weight, price=price, amount=amount, display_name=display_name)

        def showStats(self) -> str:
            if isinstance(self, RPGGame.Weapon):
                _icon = emoji.emojize(":axe:")
                _stat = self.damage
            elif isinstance(self, RPGGame.Armor):
                _icon = emoji.emojize(":shield:")
                _stat = self.armor
            else:
                raise NotImplementedError(f"Unknown Equippable type {type(self)}") #should not happen
            #return f"{self.display_name} |{_icon} {_stat} |{emoji.emojize(':moneybag:',language='alias')}{self.price}|{emoji.emojize(':muscle:',language='alias')}{self.weight}"
            return f"{_icon} {_stat:>3} |{emoji.emojize(':moneybag:',language='alias')} {self.price or '---'}|{emoji.emojize(':muscle:',language='alias')} {self.weight or '---'}"  #TODO pad the values to 3 numeric spaces to avoid wiggle between lines ig?

        def __str__(self):
            return f"{self.display_name} {self.showStats()}"

        def toDropdown(self, index=0):
            return discord.SelectOption(label=self.display_name, description=self.showStats(), value=str(index))

    class Weapon(HandEquippable, Equipment):
        def __init__(self,price: int|None = 0, weight=1, amount=1, damage=0, enchant=None, wpntype="Weapon", material="Default", display_name=None):
            #self.basedamage = basedamage
            self.damage = damage
            super().__init__(weight=weight, price=price, amount=amount, enchant=enchant, material=material, itemtype=wpntype, stat=self.damage,
                             display_name=display_name)

        def use(self, attacker, target):
            logger.info(f"dealt {self.damage} dmg to {target}")
            target.hp -= self.damage + attacker.atk #todo make a method to calculate the player.atk here

    class Armor(Equipment):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,armortype="Armor",material="Default",display_name=None):
            self.armor = armor
            super().__init__(weight=weight, price=price, amount=amount, enchant=enchant, material=material, itemtype=armortype, stat=self.armor, display_name=display_name)

    class HeadArmor(Armor):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="head",armor = armor, display_name=display_name)

    class ChestArmor(Armor):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="chest",armor = armor,display_name=display_name)

    class HandsArmor(Armor):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="hands",armor = armor,display_name=display_name)

    class LegsArmor(Armor):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="legs",armor = armor,display_name=display_name)

    class FeetArmor(Armor):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="feet",armor = armor,display_name=display_name)

    class Shield(Armor, HandEquippable):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="shield",armor = armor,display_name=display_name)

    class Consumable(Item):
        def __init__(self, *args, **kwargs):
            self.effects = []
            super().__init__(*args, **kwargs)

    # ------------------------------------------

    class Effect(object): #might be a bad and terrible spaghetti
        def __repr__(self) -> str:
            return f"{__class__}({self.__dict__})"

        def __init__(self, name, duration: int|str = 0, target=None, **kwargs: dict[str, str|int|float]):
            self.wherefrom = "Unknown" #Where the effect came from potion or item or whatever
            self.name = name
            self.lvl = 1 #inherited from Spell, if applicable
            self._duration = duration  # turns
            self.target = target #Who the effect is applied to  #not unused, used in ticking down #not sure anymore

            #self.hpeffect = {"flat": 0, "multiplier": 0, "set": None} #beware, multiplier deals based on maxhealth
            #self.manaeffect = {"flat": 0, "multiplier": 0, "set": None} #beware, multiplier deals based on maxmana

            # #these up are applied forever, below are temporary
            # self.maxhpeffect = {"flat":0,"multiplier":0,"set":None}
            # self.maxmanaeffect = {"flat":0,"multiplier":0,"set":None}
            # self.damageeffect = {"flat":0,"multiplier":0,"set":None}
            # self.critchanceeffect = {"flat":0,"multiplier":0,"set":None}
            # self.armoreffect = {"flat":0,"multiplier":0,"set":None}
            # self.strengtheffect = {"flat":0,"multiplier":0,"set":None}
            # self.agilityeffect = {"flat":0,"multiplier":0,"set":None}
            # self.intelligenceeffect = {"flat":0,"multiplier":0,"set":None}
            # self.luckeffect = {"flat":0,"multiplier":0,"set":None}
            # self.visioneffect = {"flat":0,"multiplier":0,"set":None}

            self.stun = False

            self.__dict__.update({f"_{k}": {meth: str(val) for meth,val in v.items()} for k,v in kwargs.items()}) #this is a fucking terrible hack dont ever take inspiration from me
            self.__dict__.update({k: {meth: partial(eval, getattr(self, f"_{k}")[meth]) for meth,val in v.items()} for k,v in kwargs.items()})

            # for arg in kwargs:
            #     setattr(self, arg, kwargs[arg])

        @property
        def duration(self):
            return int(eval(str(self._duration)))

        @duration.setter
        def duration(self, val):
            self._duration = val

        @property
        def shorteffect(self):
            effstr = ""
            effect = self
            for k,v in self.__dict__.items():
                if k.endswith("effect") and not k.startswith("_"):
                    if fl := int(v["flat"]()):
                        amplitude = f"{abs(fl)}"
                    elif ml := float(v["multiplier"]):
                        amplitude = f"{int(ml*100)}%"
                    else:
                        amplitude = f"={int(v['set'])}"
                    effstr += f"{self.name}: {amplitude} {'('+str(self.duration)+'turns )' if self.duration > 1 else ''} " #todo make prettier lol
            return effstr

        def tickEffect(self):
            self.duration = self.duration - 1
            if self.duration <= 0:
                del self

    # ------------------------------------------

    class Tile(object):
        def __init__(self, parameter):
            #homes,beach,island,desert,mountain,mount_fuji,camping
            #water, beach, plains, desert, forest, swamp ,lush forest, mountain, peaks
            self.enemies = []
            self.type = "land"
            if parameter>0.95:
                self.icon = ":white_large_square:"
                self.enemyChance = 0.2
                self.name = "Snowy peaks"
            elif parameter>0.8:
                self.icon = ":brown_square:"
                self.enemyChance = 0.3
                self.name = "Mountains"
            elif parameter>0.4:
                self.icon = choices([":green_square:",":evergreen_tree:",":camping:"],weights=[0.84,0.14,0.02])[0]
                self.enemyChance = 0.35
                self.name = "Forest"
            elif parameter>0.2:
                self.icon = choices([":yellow_square:",":beach_umbrella:"],weights=[0.94,0.06])[0]
                self.enemyChance = 0.2
                self.name = "Sandy beaches"
            else:
                self.icon = choices([":blue_square:",":sailboat:",":ocean:",":beach:",":island:"],weights=[0.87,0.06,0.04,0.01,0.02])[0]
                self.enemyChance = 0.1
                self.name = "Ocean"
                self.type = "water"
            self.isDiscoverable = False
            self.isOnCooldown = False
            self.isPlayer = False

        def discoverEnemies(self):
            self.isDiscoverable = chance(self.enemyChance*100) if not self.isOnCooldown else self.isDiscoverable
            if self.isDiscoverable:
                self.enemies = [  #TODO remove lol
                    RPGGame.Enemy("Goblin",10,5,10,10,[new(RPGGame.starter_pants)]),
                    RPGGame.Enemy("Goblin",10,5,10,10,[new(RPGGame.starter_pants)])
                ]

        def __str__(self):
            return self.isPlayer or self.icon

    class Player(Entity):
        def __init__(self, user, terkep):
            self.id: int = user.id
            self.name: str = user.display_name
            #self.viewport
            self.AFK: bool = False
            gender: str = choice(("man", "woman", "person"))
            self.walkicon: str = f":{gender}_walking:"
            self.swimicon: str = f":{gender}_swimming:"
            self.surficon: str = f":{gender}_surfing:"
            self.position: List[int, int] = [randint(2, 10), randint(2, 10)] #has to be list
            self.terkep: RPGGame.Terkep = terkep                        #the map theyre playing on
            self.terkep.players.append(self) #add the player on the map itself, for if they re playing multiplayer
            self._base_view_distance: int = 5
            self.view_distance: int = self._base_view_distance                 #how many tiles to reveal, will be affected by equipment
            self.discovered_mask = [[False for i in range(self.terkep.mapsize)] for i in range(self.terkep.mapsize)] #generate full hidden mask
            self.inBattle: bool = False
            self.team: List[RPGGame.Player] = [self]

            self.lvl: int = 1
            self.xp: int = 1200
            self.xpreq: int = 100 #required xp to lvlup

            self.gold: int = 0

            self.equipment: dict[str, RPGGame.Equipment] = {
                    "Left hand": new(RPGGame.bare_hands),
                    "Right hand": new(RPGGame.bare_hands),
                    "Head": new(RPGGame.empty_armor),
                    "Chest": new(RPGGame.starter_shirt),
                    "Hands": new(RPGGame.empty_armor),
                    "Legs": new(RPGGame.starter_pants),
                    "Feet": new(RPGGame.starter_boots)
                }
            self.inventory: dict[str, RPGGame.Item] = {} #weapons, armor, potions, everything looted etc
            self.effects: List[RPGGame.Effect] = [] #effects like poison, stun, etc
            self.spells: list[RPGGame.Spell] = []

            self.defend = 0
            self.hp = 100; self.mana = 100 #starting hp and mana, will be overwritten as the game progresses
            self._base_critchance = 1 #percentage
            self.critchance = self._base_critchance
            self._base_luck = 1  # percentage
            self.luck = self._base_luck

            self._base_strength = 5  # health, maybe atkdmg #TODO revert
            self._base_intelligence = 0  # maxmana, manaregen
            self._base_agility = 0  # carry, parry, hitchance, escape

            #effects apply to below values
            self.strength = self._base_strength
            self.intelligence = self._base_intelligence
            self.agility = self._base_agility

            self.calculateTurn() #calculate all the stats

            logger.debug(self.terkep.__repr__())
            super().__init__(user.display_name, hp=self.hp, atk=self.atk) #default hp and atk to be rewritten

        def __repr__(self):
            return f"Player({self.id=},{self.lvl=},{self.xp=},{self.gold=},{self.position=},{self.strength=},{self.intelligence=},{self.agility=},{self.hp=},{self.mana=},inventory={self.inventory.items()},{self.equipment=})"

        def statEmbed(self, color) -> discord.Embed:
            #self.recalculateStats()
            nums = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten"}
            embedVar = discord.Embed(
                title=f"{self.name}{self.walkicon}",
                description=f"{emoji.emojize(':heartbeat:')}:{int(self.hp)}/{self.maxhp} {emoji.emojize(manaicon)}:{self.mana}/{self.maxmana} |{emoji.emojize(f':{nums[self.lvl]}:')}" + (f"** {self.xp}/{self.xpreq}** xp" if self.xp >= self.xpreq else f" {self.xp}/{self.xpreq} xp"),
                color=color)
            # embedVar.add_field(name="Debug", value=f"X,Y: {self.position}, Size: {self.terkep.mapsize}, Seed: {self.terkep.seed}")
            return embedVar

        def regenhealth(self):
            self.hp = min(round(self.hp+self.healthRegen, 1), self.maxhp)

        def regenmana(self):
            self.mana = min(self.mana+self.manaRegen, self.maxmana)

        @property
        def weight(self):
            return sum([i.weight * i.amount for i in self.inventory.values()]) + sum([i.weight for i in self.equipment.values()])

        def recalculateStats(self): #TODO take into account the armors and their enchants and stuffs maybe
                                    #TODO maybe redo to properties

            self.strength = self._base_strength
            self.intelligence = self._base_intelligence
            self.agility = self._base_agility

            for effect in self.effects:
                if hasattr(effect,"strengtheffect"): #nope getattring the player attributes wont work
                    self.strength += int(effect.strengtheffect["flat"]())
                    self.strength = float(effect.strengtheffect["multiplier"]())*self.strength
                    if se := int(effect.strengtheffect["set"]()) >= 0:
                        self.strength = se

                if hasattr(effect,"intelligenceeffect"):
                    self.intelligence += int(effect.intelligenceeffect["flat"]())
                    self.intelligence = float(effect.intelligenceeffect["multiplier"]())*self.intelligence
                    if ie := int(effect.intelligenceeffect["set"]()) >= 0:
                        self.intelligence = ie

                if hasattr(effect,"agilityeffect"):
                    self.agility += int(effect.agilityeffect["flat"]())
                    self.agility = float(effect.agilityeffect["multiplier"]())*self.agility
                    if ae := int(effect.agilityeffect["set"]()) >= 0:
                        self.agility = ae

            self.maxmana = 100 + 20*self.intelligence
            self.manaRegen = 5 * self.intelligence
            self.maxhp = 100 + 10*self.strength
            self.healthRegen = round(self.strength/3, 2)

            self.view_distance = self._base_view_distance #apply armors too
            self.carry = 300 + self.agility * 10
            self.critchance = self._base_critchance + self.agility

            self.atk = self.strength #todo add this to weapon damage and ofc effects
            #self.armor = todo add this to armor and ofc effects

            for effect in self.effects:
                if hasattr(effect, "hpeffect"):
                    self.healthRegen += int(effect.hpeffect["flat"]())
                    self.healthRegen += self.maxhp * float(effect.hpeffect["multiplier"]())
                    if (seth := int(effect.hpeffect["set"]())) >= 0:
                        self.healthRegen = seth

                if hasattr(effect, "maxhpeffect"):
                    self.maxhp += int(effect.maxhpeffect["flat"]())
                    self.maxhp = self.maxhp * float(effect.maxhpeffect["multiplier"]())
                    if setmh := int(effect.maxhpeffect["set"]()) >= 0:
                        self.maxhp = setmh

                if hasattr(effect, "maxmanaeffect"):
                    self.maxmana += int(effect.maxmanaeffect["flat"]())
                    self.maxmana = self.maxmana * float(effect.maxmanaeffect["multiplier"]())
                    if setmm := int(effect.maxmanaeffect["set"]()) >= 0:
                        self.maxmana = setmm

                if hasattr(effect, "manaeffect"):
                    self.manaRegen += int(effect.manaeffect["flat"]())
                    self.manaRegen += self.maxmana * float(effect.manaeffect["multiplier"]())
                    if setm := int(effect.manaeffect["set"]()) >= 0:
                        self.manaRegen = setm

                if hasattr(effect, "visioneffect"):
                    self.view_distance += int(effect.visioneffect["flat"]())
                    self.view_distance = self._base_view_distance * float(effect.visioneffect["multiplier"]())
                    if setv := int(effect.visioneffect["set"]()) >= 0:
                        self.view_distance = setv

                if hasattr(effect, "critchanceeffect"):
                    self.critchance += int(effect.critchanceeffect["flat"]())
                    self.critchance += self.critchance * float(effect.critchanceeffect["multiplier"]())
                    if setc := int(effect.critchanceeffect["set"]()) >= 0:
                        self.critchance = setc

                if hasattr(effect,"luckeffect"):
                    self.luck += int(effect.luckeffect["flat"]())
                    self.luck *= float(effect.luckeffect["multiplier"]())
                    if setl := int(effect.luckeffect["set"]()) >= 0:
                        self.luck = setl

                effect.tickEffect()

        def calculateTurn(self) -> None:
            self.recalculateStats()
            self.tickSpells()
            self.regenhealth()
            self.regenmana()

        def attemptFlee(self, enemies: list) -> bool:  # TODO slightly too hard to escape lol, maybe buff the agility by *10
            if self.agility >= random.randint(0, sum([i.atk for i in enemies])):
                logger.info("flee attempt success")
                return True
            else:
                logger.info("flee attempt failed")

        def getCurrentTile(self): # -> RPGGame.Tile:
            x, y = self.position
            return self.terkep.grid[x][y]

        def levelup(self) -> None:
            if self.xp >= self.xpreq:
                self.xp -= self.xpreq
                self.xpreq *= 2
                self.lvl += 1

        async def attack(self, battlefield, hand, ctx: discord.Interaction, myview):
            await asyncio.sleep(0.5)
            pchoice,targets = None,None
            if isinstance(hand, RPGGame.AOESpell):
                if isinstance(hand, RPGGame.FriendlyAOESpell):
                    targets = battlefield.players
                elif isinstance(hand, RPGGame.EnemyAOESpell):
                    targets = battlefield.enemies

            elif isinstance(hand, RPGGame.FriendlySpell):
                if len([p for p in battlefield.players if p.hp > 0]) > 1:
                    pchoice = battlefield.players
                else:
                    targets = battlefield.players
            else:
                if len([enemy for enemy in battlefield.enemies if enemy.hp > 0]) > 1:
                    pchoice = battlefield.enemies
                else:
                    targets = battlefield.enemies

            if pchoice:
                viewObj = discord.ui.View()
                viewObj.add_item(RPGGame.TargetSelectView(pchoice, hand, self, battlefield, myview))
                await ctx.edit(view=viewObj)
            else:
                for entity in targets:
                    hand.use(self, entity)
                    if isinstance(hand, RPGGame.Spell):
                        battlefield.atklog += f"{self.display_name} cast {hand.name} on {entity.display_name}\n"
                    else:
                        battlefield.atklog += f"{self.display_name} hit {entity.display_name} for {self.atk} damage.\n"
                myview.stop()
                return

        class EquipSlot(discord.ui.Select):
            def __init__(self, itemtype, itemslot, player, backembed, backview):
                self.itemtype = itemtype
                self.backembed = backembed
                self.backview = backview
                self.player = player
                self.itemslot = itemslot
                optionen = [discord.SelectOption(label="Cancel", emoji=emoji.emojize(":x:", language="alias"), value="-1")]
                for index, item in enumerate([*self.player.inventory.values(),*self.player.spells]):  # find each item/spell in inventory/spells
                    logger.debug(f"{self.itemtype=},{self.itemslot=},{item=},{index=}")
                    if isinstance(item, itemtype): #that has the right type
                        optionen.append(item.toDropdown(index))
                super().__init__(placeholder="Select an item to equip", options=optionen)

            async def callback(self, ctx):
                player: RPGGame.Player = self.player
                selected = int(self.values[0])
                if selected != -1:
                    #list(player.inventory.values())[selected],player.equipment[self.itemslot] = player.equipment[self.itemslot],list(player.inventory.values())[selected]
                    toSlot: RPGGame.Equipment|RPGGame.Spell = [*self.player.inventory.values(), *self.player.spells][selected] #item to slot, no the slot to use
                    if not isinstance(toSlot, RPGGame.Spell):
                        toSlot = new(toSlot)
                        toSlot.amount = 1
                    slotted = player.equipment[self.itemslot]
                    if not isinstance(slotted, RPGGame.Spell):
                        slotted: RPGGame.Equipment = new(slotted)
                        slotted.amount = min(1, slotted.amount) #to not slot empty hands or empty armor
                        addLoot(player.inventory, slotted)
                        removeItem(player.inventory, toSlot)
                    player.equipment[self.itemslot] = toSlot
                await ctx.edit(embed=self.player.showEqp(), view=self.player.EquipButtons(self.player, self.backembed, self.backview))

        def listInv(self):
            logger.debug(self.inventory)
            embedVar = discord.Embed(title=f"{self.name}'s inventory", description="")
            for n, item in enumerate(self.inventory.values(), start=1):
                embedVar.description += f"**[{n}]** = *{item.display_name} {item.stats()}*\n"
            embedVar.set_footer(text=f"Carry capacity: {self.weight}/{self.carry}")
            return embedVar

        def showEqp(self):
            logger.debug(self.equipment)
            embedVar = discord.Embed(title=f"{self.name}'s equipment")
            for slot, item in self.equipment.items():
                embedVar.add_field(name=f"**{slot}:** *{item.display_name}*", value=item.showStats(), inline=False)
                embedVar.set_footer(text="Use the buttons below to equip different items")
            return embedVar

        class EquipButtons(discord.ui.View): #TODO ability to slot in empty armor or empty hands?? as a default prefill option next to cancel
            def __init__(self, player, backembed, backview):
                self.player: RPGGame.Player = player
                self.backembed: discord.Embed = backembed
                self.backview: discord.ui.View = backview
                super().__init__()

            @discord.ui.button(emoji=emoji.emojize(':womans_hat:', language="alias"))
            async def headbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(
                    self.player.EquipSlot([RPGGame.HeadArmor], "Head", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":t-shirt:", language="alias"))
            async def chestbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(
                    self.player.EquipSlot(RPGGame.ChestArmor, "Chest", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":jeans:", language="alias"))
            async def legsbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(
                    self.player.EquipSlot(RPGGame.LegsArmor, "Legs", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":hiking_boot:", language="alias"))
            async def shoesbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(
                    self.player.EquipSlot(RPGGame.FeetArmor, "Feet", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":gloves:", language="alias"))
            async def glovesbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(
                    self.player.EquipSlot(RPGGame.HandsArmor, "Hands", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":left-facing_fist:", language="alias"))
            async def lefthandbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot(RPGGame.HandEquippable, "Left hand", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":right-facing_fist:", language="alias"))
            async def righthandbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot(RPGGame.HandEquippable, "Right hand", self.player, self.backembed, self.backview))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":x:", language="alias"))
            async def cancelbutton(self, button, ctx):
                #self.player.checkLvlUp(self.backview)
                if hasattr(self.backview, "toStop"):
                    self.backview.stop()
                else:
                    await ctx.edit(view=self.backview, embed=self.backembed)

        #@print_durations
        def discoverMap(self,sight_range):
            for row in self.discovered_mask[np.clip(self.position[0]-sight_range,0,self.terkep.mapsize):np.clip(self.position[0]+sight_range+1,0,self.terkep.mapsize)]:
                for col in range(np.clip(self.position[1]-sight_range,0,self.terkep.mapsize),np.clip(self.position[1]+sight_range+1,0,self.terkep.mapsize)):
                    row[col] = True

        #@print_durations

        def checkLvlUp(self, view: discord.ui.View):
            for item in view.children:
                if item.custom_id == "lvlupbtn":
                    lvlupbutton = item
                    break
            else:
                return # it is always present, it is here to ensure the IDE doesnt trip up

            if self.xp >= self.xpreq:
                # lvlupbutton.disabled = False
                lvlupbutton.style = discord.ButtonStyle.blurple
            else:
                # lvlupbutton.disabled = True
                lvlupbutton.style = discord.ButtonStyle.grey

        def move(self, direction, view):
            self.calculateTurn()
            self.checkLvlUp(view)
            if "left" in direction:
                self.position[1] = abs(self.position[1] - 1)
            if "up" in direction:
                self.position[0] = abs(self.position[0] - 1)
            if "right" in direction:
                self.position[1] = min(self.terkep.mapsize-1, self.position[1] + 1)
            if "down" in direction:
                self.position[0] = min(self.terkep.mapsize-1, self.position[0] + 1)

            self.handleTileDiscovery(view)
            self.discoverMap(self.view_distance)
            return self.terkep.render(self.terkep.window, self)

        def handleTileDiscovery(self, view):
            for btn in view.children:
                if btn.custom_id == "explorebtn":
                    explorebutton = btn
                    break
            currtile = self.getCurrentTile()
            currtile.discoverEnemies()
            currtile.isOnCooldown = True
            if currtile not in self.terkep.visitedTiles:
                self.terkep.visitedTiles.append(currtile)
                if len(self.terkep.visitedTiles) > self.terkep.tileRespawnTimer:
                    self.terkep.visitedTiles[0].isOnCooldown = False
                    self.terkep.visitedTiles.pop(0)
            if currtile.isDiscoverable:
                explorebutton.disabled = False
                explorebutton.style = discord.ButtonStyle.blurple
            else:
                explorebutton.disabled = True
                explorebutton.style = discord.ButtonStyle.grey

        def tickSpells(self):
            for spell in self.spells:
                spell.tickCd()

        def listSpells(self) -> discord.Embed:
            embedVar = discord.Embed(title=f"{self.display_name}'s known spells")
            for spell in self.spells:
                embedVar.add_field(name=spell.display_name,value=spell.listEffects,inline=False)
            return embedVar

    bare_hands = Weapon(weight=0,price=None,damage=3,amount=0,wpntype="blunt",material="Flesh",display_name="Fists")
    starter_shirt = ChestArmor(price=None,weight=1,amount=1,armor=0,material="Cloth",display_name="Torn shirt")
    starter_pants = LegsArmor(price=None,weight=1,amount=1,armor=0,material="Cloth",display_name="Plain pants")
    starter_boots = FeetArmor(price=None,weight=1,amount=1,armor=0,material="Cloth",display_name="Simple shoes")
    empty_armor = Armor(price=None,weight=0,amount=0,armor=0,material="Cloth",display_name="Empty")
    starter_shield = Shield(price=None,weight=5,amount=1,armor=5,material="Wooden",display_name="Wooden shield")

    class Terkep(object):
        #@print_durations
        def __init__(self, size, seed, window):
            self.mapsize = size
            self.grid: List[List[RPGGame.Tile]] = Noise.makeMap(size, 1.5, seed)
            self.seed: int = seed
            self.players: List[RPGGame.Player] = []
            self.window = window
            self.tileRespawnTimer: int = 10
            self.visitedTiles: List[RPGGame.Tile] = [] #these tiles are not to process for n amount of turns

        def __repr__(self):
            return f"Terkep(size={self.mapsize},seed={self.seed},players={self.players})"

        #@print_durations
        def render(self, size, as_player):
            if size % 2:
                raise ValueError("Render window size must be even") #why? is it easier to calc radii with even viewport?

            for player in self.players:
                if self.grid[player.position[0]][player.position[1]].type == "water":
                    self.grid[player.position[0]][player.position[1]].isPlayer = player.swimicon
                elif self.grid[player.position[0]][player.position[1]].icon == ":ocean:":
                    self.grid[player.position[0]][player.position[1]].isPlayer = player.surficon
                else:
                    self.grid[player.position[0]][player.position[1]].isPlayer = player.walkicon

            msg = ""
            xbegin = np.clip(as_player.position[0]-size//2, 0, self.mapsize-size)
            ybegin = np.clip(as_player.position[1]-size//2, 0, self.mapsize-size)
            for row, maskrow in zip(self.grid[xbegin:xbegin+size], as_player.discovered_mask[xbegin:xbegin+size]):
                for i, maskcol in zip(row[ybegin:ybegin+size], maskrow[ybegin:ybegin+size]):
                    msg += emoji.emojize(str(i)) if maskcol else emoji.emojize(":black_large_square:")
                msg+="\n"
            #msg+="\n"+str(as_player.position[0])+" "+str(as_player.position[1])
            for player in self.players:
                self.grid[player.position[0]][player.position[1]].isPlayer = False
            return msg

    class Battlefield(object):
        def __init__(self, players: list, enemies: list, player, interaction: discord.Interaction):
            self.players: List[RPGGame.Player] = players
            self.player: RPGGame.Player = player
            self.enemies: list[RPGGame.Enemy] = enemies
            self.interaction: discord.Interaction = interaction
            self.loot: dict[str, RPGGame.Item] = {}
            self.xp: int = 0
            self.gold: int = 0

        class TakeLootButtons(discord.ui.View):
            def __init__(self, loot, player):
                self.loot: List[RPGGame.Item] = loot
                self.player: RPGGame.Player = player
                super().__init__(timeout=100)

            @discord.ui.button(label="Leave loot", style=discord.ButtonStyle.red)
            async def leaveloot(self, button, ctx):
                self.loot = []
                await RPGCog.backToMap(ctx, self.player)


            @discord.ui.button(label="Select loot", style=discord.ButtonStyle.gray, disabled=True)
            async def pickloot(self, button, ctx):
                ...
                pass  # TODO

            @discord.ui.button(label="Take all", style=discord.ButtonStyle.green)
            async def takeloot(self, button, ctx):
                addLoot(self.player.inventory, self.loot)
                await RPGCog.backToMap(ctx, self.player)

        async def display_loot(self, interaction: discord.Interaction):
            embedVar = discord.Embed(description="You found", color=interaction.user.color)
            weight = 0
            for loot in self.loot.values():
                weight += (loot.weight if loot.weight else 0) * (loot.amount if loot.amount else 1)
                embedVar.add_field(name=loot.display_name, value=loot.stats())
            embedVar.set_footer(text=f"Total weight: {weight}| Your carry capacity: {self.player.weight}/{self.player.carry}")
            viewObj = self.TakeLootButtons(self.loot, self.player)
            if self.player.weight + weight > self.player.carry:
                viewObj.children[2].disabled = True
            if self.player.weight >= self.player.carry:
                viewObj.children[1].disabled = True
            await interaction.edit(content=None, embed=embedVar, view=viewObj)

        async def display_fight(self) -> discord.ui.View:
            viewObj = RPGGame.FightView(self.player, self)
            for button, hand in zip((viewObj.children[0], viewObj.children[1]),
                                    (self.player.equipment["Left hand"], self.player.equipment["Right hand"])):
                button.label = hand.display_name
                if isinstance(hand, RPGGame.Shield) or (isinstance(hand, RPGGame.Spell) and hand.cooldown):
                    logger.debug(hand)
                    logger.debug(hand.cooldown)
                    button.disabled = True  # maybe implement some functionality here, like chance to block? idk why
                    #TODO add maybe a do nothing button if both hands are disabled

            #embedVar = discord.Embed(title="Fight")
            #for enemy in self.player.getCurrentTile().enemies:
            #    embedVar.add_field(name=enemy.display_name, value=enemy.showStats())

            await self.interaction.edit(content="\n".join(f"**{enemy.display_name} | {enemy.showStats()}**" for enemy in self.enemies if enemy.hp > 0),
                                        embed=self.player.statEmbed(self.interaction.user.color),
                                        view=viewObj)
            return viewObj
            # await interaction.edit(embed=self.player.statEmbed(interaction.user.color),view=viewObj) #TODO put enemies in pic and use embed for players

        async def battle(self):
            while any(i.hp > 0 for i in self.players) and any(i.hp > 0 for i in self.enemies):
                self.atklog = ""
                logger.info(f"{self.players} vs {self.enemies}")
                for player in self.players:
                    if player.hp > 0:
                        player.tickSpells()
                        if not player.AFK:
                            if player.stunned:
                                self.atklog += f"{player.display_name} was stunned, no attack occured."
                                continue
                            viewObj = await self.display_fight() #attacking happens here
                            if await viewObj.wait():
                                logger.info("player has gone afk")
                                fled = player.attemptFlee(self.enemies)
                                if fled:
                                    player.inBattle = False
                                    self.players.remove(player)
                            else:
                                logger.info("view stopped")
                        else:
                            fled = player.attemptFlee(self.enemies)
                            if fled:
                                player.inBattle = False
                                self.atklog += f"{player.display_name} attempted to flee.. and succeeded!"
                                self.players.remove(player)
                            else:
                                self.atklog += f"{player.display_name} attempted to flee.. unsuccessfully"

                for entity in self.enemies:
                    entity.recalculateStats()
                await asyncio.sleep(1)

                if self.players:
                    for enemy in self.enemies:
                        if enemy.hp > 0:
                            if enemy.stunned:
                                self.atklog += f"{enemy.display_name} was stunned, no attack occured."
                            else:
                                atk = enemy.attack([player for player in self.players if player.hp > 0])
                                self.atklog += f"{atk}\n"
                    logger.info(self.atklog)
                for entity in self.players:
                    entity.recalculateStats()
            else:
                if any(i.hp > 0 for i in self.players):
                    logger.info("win")
                    for enemy in self.enemies:
                        addLoot(self.loot, enemy.lootTable) #TODO implement some randomizer here
                        self.player.xp += enemy.xp
                    await self.display_loot(self.interaction)
                else:
                    logger.info("lose")

    class FightView(discord.ui.View):
        def __init__(self, player, battlefield):
            super().__init__(timeout=60, auto_defer=False)
            self.player: RPGGame.Player = player
            self.toStop = True #used in equipment view
            self.battlefield = battlefield

        @discord.ui.button(label="self.player.equipment.weapon.display_name", style=discord.ButtonStyle.blurple, emoji=emoji.emojize(":left-facing_fist:", language="alias"))
        async def attackL(self, button, ctx):
            await self.player.attack(self.battlefield, self.player.equipment["Left hand"], ctx, myview=self)
             #self.stop() # cant stop here

        @discord.ui.button(label="self.player.equipment.weapon.display_name", style=discord.ButtonStyle.blurple, emoji=emoji.emojize(":right-facing_fist:", language="alias"))
        async def attackR(self, button, ctx):
            await self.player.attack(self.battlefield, self.player.equipment["Right hand"], ctx, myview=self)

        @discord.ui.button(emoji=emoji.emojize(":wine_glass:", language="alias"),disabled=True)
        async def potion(self, button, ctx):
            self.stop()
            pass

        @discord.ui.button(emoji=emoji.emojize(":t-shirt:", language="alias")) #TODO rethink if this should be posisble mid battle
        async def equipment(self, button, ctx):
            await ctx.edit(view=self.player.EquipButtons(self.player, ctx.message.embeds[0], self), embed=self.player.showEqp())

        @discord.ui.button(emoji=emoji.emojize(":person_running:", language="alias"))
        async def run(self, button, ctx):
            if self.player.attemptFlee(self.battlefield.enemies):
                await ctx.send("success")
                self.battlefield.players.remove(self.player)
            else:
                await ctx.send("fail")
            self.stop()

##bare_hands = RPGGame.Weapon(weight=0,price=None,damage=5,amount=None,wpntype="Melee",material=None,display_name="Fists")
##starter_shirt = RPGGame.Armor(price=None,weight=1,amount=None,armor=0,armortype="Chest",material=None,display_name="Torn shirt")
##starter_pants = RPGGame.Armor(price=None,weight=1,amount=None,armor=0,armortype="Legs",material=None,display_name="Plain pants")
##starter_boots = RPGGame.Armor(price=None,weight=1,amount=None,armor=0,armortype="Feet",material=None,display_name="Simple shoes")
##empty_armor = RPGGame.Armor(price=None,weight=None,amount=None,armor=0,armortype=None,material=None,display_name="Empty")

class RPGCog(commands.Cog):
    def __init__(self, client, baselogger: logging.Logger):
        global logger
        self.client = client
        self.worlds = {}
        self.players = {}
        logger = baselogger.getChild(f"{__name__}logger")

    @classmethod
    async def backToMap(cls, ctx, player):
        viewObj = cls.MapMoveButtons(player)
        player.handleTileDiscovery(viewObj)
        player.checkLvlUp(viewObj)
        await ctx.edit(content=player.terkep.render(player.terkep.window, player), embed=player.statEmbed(ctx.user.color), view=viewObj)

    class MapMoveButtons(discord.ui.View):
        def __init__(self, player, timeout=180):
            super().__init__(timeout=timeout)
            self.player: RPGGame.Player = player

        #async def interaction_check(self, interaction): #TODO include these everywhere or actually subclass a view and add an interaction check in telling ppl to start their own map
            #return self.ctx.author == interaction.user

        #---------------------------row0--------------------------------------------
        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_upper_left:", language="alias"))
        async def moveupleft(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("up left", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":up_arrow:"))
        async def moveup(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("up", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_upper_right:", language="alias"))
        async def moveupright(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("up right", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":shirt:", language="alias"))
        async def showeqpbut(self, button, interaction: discord.Interaction):
            await interaction.edit(embed=self.player.showEqp(), view=self.player.EquipButtons(self.player, interaction.message.embeds[0], self))

        #---------------------------row1--------------------------------------------

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":left_arrow:"), row=1)
        async def moveleft(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("left", self), embed=self.player.statEmbed(interaction.user.color), view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":magnifying_glass_tilted_left:", language="alias"), row=1, disabled=True, custom_id="explorebtn") #could be emoji.emojize(":mag:") as in magnifying glass to explore the place
        async def explore(self, button, interaction: discord.Interaction):
            tile = self.player.getCurrentTile()
            tile.isDiscoverable = False
            button.disabled = True
            await self.startfight(self.player.team, tile.enemies, self.player, interaction)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":right_arrow:"), row=1)
        async def moveright(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("right", self), embed=self.player.statEmbed(interaction.user.color), view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":package:", language="alias"), row=1)
        async def showinvbut(self, button, interaction):
            #await interaction.send(embed=self.player.showEqp(),view=self.player.EquipButtons())
            await interaction.edit(embed=self.player.listInv(), view=self.BackToMapButton(self.player))

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_lower_left:", language="alias"), row=2)
        async def moveleftdown(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("left down", self), embed=self.player.statEmbed(interaction.user.color), view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":down_arrow:"), row=2)
        async def movedown(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("down",self), embed=self.player.statEmbed(interaction.user.color), view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_lower_right:", language="alias"), row=2)
        async def moverightdown(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("right down", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.grey, emoji=emoji.emojize(":star:", language="alias"),disabled=False,custom_id="lvlupbtn",row=3)  # TODO show text and buttons depending if actually levelled up or not
        async def showlvlupbut(self, button, interaction):
            embedVar = discord.Embed(title="You have levelled up!", description=f"You have reached level **{self.player.lvl}**! You are now able to upgrade one of your attributes.", color=interaction.user.color)
            embedVar.add_field(
                name=f"Strength {self.player.strength} {emoji.emojize(':right_arrow:')} {self.player.strength + 1}",
                value="Strength increases your **maximum health**, **health regeneration** and **weapon attack power**")
            embedVar.add_field(
                name=f"Intelligence {self.player.intelligence} {emoji.emojize(':right_arrow:')} {self.player.intelligence + 1}",
                value="Intelligence increases your **maximum mana**, **mana regeneration** and **spell effectivity**")
            embedVar.add_field(
                name=f"Agility {self.player.agility} {emoji.emojize(':right_arrow:')} {self.player.agility + 1}",
                value="Agility increases your **inventory capacity**, **parry** and **hit chances** and also increases your chance of **escaping** tough fights.")
            await interaction.edit(embed=embedVar, view=RPGGame.LvlUpButtons(self.player))

        @discord.ui.button(style=discord.ButtonStyle.grey, emoji=emoji.emojize(manaicon), row=3)
        async def listspellsbut(self, button, interaction: discord.Interaction):
            await interaction.edit(embed=self.player.listSpells(), view=self.BackToMapButton(self.player))
            pass

        @discord.ui.button(style=discord.ButtonStyle.red, emoji=emoji.emojize(":x:", language="alias"), row=4)
        async def hidemapbutton(self, button, interaction):
            await interaction.response.edit_message(
                content="Map removed to improve the the Discord app's performance with their poor emoji rendering",
                view=None, embed=None)

        class BackToMapButton(discord.ui.View):
            def __init__(self, player):
                self.player = player
                super().__init__()

            @discord.ui.button(emoji=emoji.emojize(":left_arrow:"))
            async def backbutton(self, button, ctx):
                await RPGCog.backToMap(ctx, self.player)

        async def startfight(self, players, enemies, player, interaction: discord.Interaction):
            battle = RPGGame.Battlefield(players, enemies, player, interaction)
            #await battle.display_fight()
            await battle.battle()

    @discord.slash_command(name="map", description="testing", guild_ids=[860527626100015154, 601381789096738863])
    async def makemap(self, ctx,
                      mapsize: int = discord.SlashOption(name="mapsize", description="map x and y diameter in tiles", required=False, min_value=14, max_value=1400, default=56),
                      seed: int = discord.SlashOption(name="seed", description="map generator seed", required=False, min_value=0, max_value=100, default=randint(0, 100))):
        await ctx.response.defer()
        #print(seed) #67 stripey, 51 quadrants,71 horizontal stripes, 34 veritcal stripes 56 seed, 51 circular quadrants
        terkep = RPGGame.Terkep(mapsize, seed, 14)
        player: RPGGame.Player = RPGGame.Player(ctx.user, terkep)
        pant2 = new(RPGGame.starter_pants)
        addLoot(player.inventory, new(pant2))
        pant2.armor += 5
        pant2.display_name = "Super awesome shorts"
        addLoot(player.inventory, pant2)
        shield = new(RPGGame.starter_shield)
        addLoot(player.inventory, [shield])
        spell = new(RPGGame.Spell("Fireball", manacost="5+5*self.lvl", cooldown="2+self.lvl", effects=[ #self.lvl refers to the spell level
            RPGGame.Effect("Fire", duration=1, hpeffect={"flat": -5, "multiplier": 0, "set": -1}),
            RPGGame.Effect("Burning", duration="2+self.lvl", hpeffect={"flat": "-effect.lvl", "multiplier": 0, "set": -1})
        ]))
        spell2 = new(spell)
        spell2.lvlup(2)
        logger.info(spell)
        player.spells.append(spell)
        player.spells.append(spell2)
        player.equipment["Right hand"] = player.spells[0]
        viewObj = self.MapMoveButtons(player)
        await ctx.send(player.move("down", viewObj), view=viewObj, embed=player.statEmbed(ctx.user.color))


def setup(client, baselogger):
    client.add_cog(RPGCog(client, baselogger))

