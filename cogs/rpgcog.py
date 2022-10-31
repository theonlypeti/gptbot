import logging
import random
from typing import Union, List, Type
import nextcord as discord
from nextcord.ext import commands
import numpy as np
import matplotlib.pyplot as plt
import emoji
from random import choices, choice, randint
from copy import deepcopy as new #maybe useful for equipping items
from funcy import print_durations
from numpy import Infinity
from utils.mapvalues import mapvalues

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
        grid=[[]]
        biggest,smallest = 0,1
        for line in a:
            biggest = max(max(list(line)), biggest) #TODO maybe use np.clip?
            smallest = min(min(list(line)), smallest)

        for row in a:
            for i in row:
                grid[-1].append(RPGGame.Tile(mapvalues(i, smallest, biggest, 0, 1)))
            grid.append([])
        #plt.imshow(a, origin='upper')
        #plt.show()
        return grid



class RPGGame:

    class TargetSelectView(discord.ui.Select):
        def __init__(self, targets, attack, attacker, battle):
            self.attacker: RPGGame.Entity = attacker
            self.targets = targets
            self.attack: RPGGame.Spell | RPGGame.Weapon = attack
            self.battle = battle
            #self.returnView = returnView
            options = [discord.SelectOption(label=i.display_name, description=i.showStats(), value=str(n)) for n,i in enumerate(targets)]
            super().__init__(options=options)

        async def callback(self, interaction: discord.Interaction):
            selected: RPGGame.Entity = self.targets[int(self.values[0])]
            self.attack.use(self.attacker, selected)
            self.battle.advance()
            #await interaction.edit(view=self.returnView)


    class Spell(object):
        def __init__(self,name,manacost,effects,selfeffects,hpcost=0,mpcost=0,duration=0,cooldown=0,lvl=1,description=''):
            self.name = name
            self.manacost = manacost
            self.effects = effects or []
            self.selfeffects = selfeffects or [] #effects that are applied to the user regardless of target, something like weakening, or siphoning
            self.hpcost = hpcost
            self.mpcost = mpcost
            self.duration = duration
            self.cooldown = cooldown
            self.description = description
            self.lvl = lvl

        def use(self, user, target):
            if user.mana >= self.manacost:
                user.mana -= self.manacost
            if not isinstance(target, list):
                target = [target]
            for t in target:
                for e in self.effects:
                    t.effects.append(e)
            for e in self.selfeffects:
                user.effects.append(e)

    class DirectSpell(Spell):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)

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
            self.display_name = name
            self.hp = hp
            self.atk = atk
            self.effects = []
            self.stunned = False

        def affect(self, effects):
            pass

    class Enemy(Entity):
        def __init__(self, name, hp, atk, exp, gold, loot):
            self.exp = exp
            self.gold = gold
            self.lootTable = loot  # {item:chance}
            self.mana = Infinity
            super().__init__(name, hp, atk)

        def __str__(self):
            return f"{self.display_name}: {self.hp}hp, {self.atk}atk"

        def showStats(self):
            return f"{self.hp} hp, {self.atk} atk" #TODO replace with emojis

        def __repr__(self):
            return f"Enemy(display_name={self.display_name},hp={self.hp},atk={self.atk})"

        def recalculateStats(self): #TODO use @property decorator instead maybe? might be too invested in this
            self.stunned = False
            for effect in self.effects:
                if effect.hasattr("hpeffect"):
                    self.hp += effect.hpeffect["flat"]
                    self.hp += self.hp * effect.hpeffect["multiplier"]
                    if effect.hpeffect["set"] is not None:
                        self.hp = effect.hpeffect["set"]

                if effect.hasattr("atkeffect"):
                    self.atk += effect.atkeffect["flat"]
                    self.atk += self.atk * effect.atkeffect["multiplier"]
                    if effect.atkeffect["set"] is not None:
                        self.atk = effect.atkeffect["set"]

                if effect.hasattr("stunned"):
                    self.stunned = effect.stun

                effect.tickEffect()

        def attack(self, targets): #TODO to be rewritten for each type of enemy
            target: RPGGame.Player = random.choice(targets)
            target.hp -= self.atk
            return f"{self.display_name} hit {target.display_name} for {self.atk}"

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
            super().__init__() #TODO how to do items in inventory :(

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
            price = self.amount * self.price if self.price and self.amount else "--"
            weight = self.amount * self.weight if self.weight and self.amount else "--"
            return f"Amnt:{self.amount}|Wght:{weight}|Gold:{price}"

    class Equippable(Item):
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

        def showName(self) -> str:
            return self.display_name

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
            return self.showName() + " " + self.showStats()

        def toDropdown(self, index=0):
            return discord.SelectOption(label=self.showName(), description=self.showStats(), value=str(index))

    class HandEquippable(Equippable):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    class Weapon(HandEquippable):
        def __init__(self,price=0,weight=1,amount=1,damage=0,enchant=None,wpntype="Weapon",material="Default",display_name=None):
            #self.basedamage = basedamage
            self.damage = damage
            super().__init__(weight=weight, price=price, amount=amount, enchant=enchant, material=material, itemtype=wpntype, stat=self.damage,
                             display_name=display_name)

        def use(self, attacker, target):
            logger.info(f"dealt {self.damage} dmg to {target}")
            target.hp -= self.damage #todo make a method to calculate the player.atk here

    class Armor(Equippable):
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

    class Shield(Armor):
        def __init__(self,price=0,weight=1,amount=1,armor=0,enchant=None,material="Default",display_name=None):
            super().__init__(weight=weight,price=price,amount=amount,enchant=enchant,material=material,armortype="shield",armor = armor,display_name=display_name)

    class Consumable(Item):
        def __init__(self, *args, **kwargs):
            self.effects = []
            super().__init__(*args, **kwargs)

    # ------------------------------------------

    class Effect(object): #might be a bad and weak and rigid implementation
        def __init__(self,name,duration,target,**kwargs):
            self.wherefrom = "Unknown" #Where the effect came from potion or item or whatever
            self.name = name
            self.duration = duration  # turns
            self.target = target #Who the effect is applied to  #not unused, used in ticking down

            self.hpeffect = {"flat": 0,"multiplier": 1,"set": None} #beware, multiplier deals based on maxhealth
            self.manaeffect = {"flat": 0,"multiplier": 1,"set": None} #beware, multiplier deals based on maxmana

            # #these up are applied forever, below are temporary
            # self.maxhpeffect = {"flat":0,"multiplier":1,"set":None}
            # self.maxmanaeffect = {"flat":0,"multiplier":1,"set":None}
            # self.damageeffect = {"flat":0,"multiplier":1,"set":None}
            # self.critchanceeffect = {"flat":0,"multiplier":1,"set":None}
            # self.armoreffect = {"flat":0,"multiplier":1,"set":None}
            # self.strengtheffect = {"flat":0,"multiplier":1,"set":None}
            # self.agilityeffect = {"flat":0,"multiplier":1,"set":None}
            # self.intelligenceeffect = {"flat":0,"multiplier":1,"set":None}
            # self.luckeffect = {"flat":0,"multiplier":1,"set":None}
            # self.visioneffect = {"flat":0,"multiplier":1,"set":None}

            self.stun = False
            self.__dict__.update(kwargs)
            # for arg in kwargs:
            #     setattr(self, arg, kwargs[arg])

        def tickEffect(self):
            self.duration -= 1
            if self.duration <= 0:
                self.target.effects.remove(self)

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
                self.enemies = [RPGGame.Enemy("Goblin",10,5,10,10,[new(RPGGame.starter_pants)])]

        def __str__(self):
            return self.isPlayer or self.icon

    class Player(Entity):
        def __init__(self, user, terkep):
            self.id = user.id
            self.name = user.display_name
            #self.viewport
            self.AFK = False
            gender = choice(("man", "woman", "person"))
            self.walkicon = f":{gender}_walking:"
            self.swimicon = f":{gender}_swimming:"
            self.surficon = f":{gender}_surfing:"
            self.position = [randint(2, 10), randint(2, 10)]
            self.terkep = terkep                        #the map theyre playing on
            self.terkep.players.append(self) #add the player on the map itself, for if they re playing multiplayer
            self._base_view_distance = 5
            self.view_distance = self._base_view_distance                 #how many tiles to reveal, will be affected by equipment
            self.discovered_mask = [[False for i in range(self.terkep.mapsize)] for i in range(self.terkep.mapsize)] #generate full hidden mask
            self.inBattle = False
            self.team = [self]

            self.lvl = 1
            self.xp = 0
            self.xpreq = 100 #required xp to lvlup

            self.gold = 0

            self.equipment = {
                    "Left hand": new(RPGGame.bare_hands),
                    "Right hand": new(RPGGame.bare_hands),
                    "Head": new(RPGGame.empty_armor),
                    "Chest": new(RPGGame.starter_shirt),
                    "Hands": new(RPGGame.empty_armor),
                    "Legs": new(RPGGame.starter_pants),
                    "Feet": new(RPGGame.starter_boots)
                }
            self.inventory = {} #weapons, armor, potions, everything looted etc
            self.effects = [] #effects like poison, stun, etc

            self.defend = 0
            self.hp = 0; self.mana = 0 #initialize, to be overwritten
            self._base_critchance = 1 #percentage
            self.critchance = self._base_critchance
            self._base_luck = 1  # percentage
            self.luck = self._base_luck

            self._base_strength = 0  # health, maybe atkdmg
            self._base_intelligence = 0  # maxmana, manaregen
            self._base_agility = 0  # carry, parry, hitchance, escape

            #effects apply to below values
            self.strength = self._base_strength
            self.intelligence = self._base_intelligence
            self.agility = self._base_agility

            self.calculateTurn() #calculate all the stats

            print(self.terkep.__repr__())
            super().__init__(user.display_name, hp=1, atk=1) #default hp and atk to be rewritten

        def __repr__(self):
            return f"Player({self.id=},{self.lvl=},{self.xp=},{self.gold=},{self.position=},{self.strength=},{self.intelligence=},{self.agility=},{self.hp=},{self.mana=},inventory={self.inventory.items()},{self.equipment=})"

        def statEmbed(self, color) -> discord.Embed:
            self.recalculateStats()
            nums = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten"}
            embedVar = discord.Embed(
                title=f"{self.name}{self.walkicon}",
                description=f"{emoji.emojize(':heartbeat:')}:{int(self.hp)}/{self.maxhp} {emoji.emojize(':magic_wand:')}:{self.mana}/{self.maxmana} |{emoji.emojize(f':{nums[self.lvl]}:')}" + (f"** {self.xp}/{self.xpreq}** xp" if self.xp >= self.xpreq else f" {self.xp}/{self.xpreq} xp"),
                color=color)
            embedVar.add_field(name="Debug",value=f"X,Y: {self.position}, Size: {self.terkep.mapsize}, Seed: {self.terkep.seed}")
            return embedVar

        def regenhealth(self):
            self.hp = min(round(self.hp+self.healthRegen, 1), self.maxhp)

        def regenmana(self):
            self.mana = min(self.mana+self.manaRegen, self.maxmana)

        def recalculateStats(self): #TODO take into account the armors and their enchants and stuffs maybe

            self.strength = self._base_strength
            self.intelligence = self._base_intelligence
            self.agility = self._base_agility

            for effect in self.effects:
                if effect.hasattr("strengtheffect"):
                    self.strength += effect.strengtheffect["flat"]
                    self.strength = effect.strengtheffect["multiplier"]*self.strength
                    if effect.strengtheffect["set"] is not None:
                        self.strength = effect.strengtheffect["set"]

                if effect.hasattr("intelligenceeffect"):
                    self.intelligence += effect.intelligenceeffect["flat"]
                    self.intelligence = effect.intelligenceeffect["multiplier"]*self.intelligence
                    if effect.intelligenceeffect["set"] is not None:
                        self.intelligence = effect.intelligenceeffect["set"]

                if effect.hasattr("agilityeffect"):
                    self.agility += effect.agilityeffect["flat"]
                    self.agility = effect.agilityeffect["multiplier"]*self.agility
                    if effect.agilityeffect["set"] is not None:
                        self.agility = effect.agilityeffect["set"]


            self.maxmana = 100 + 20*self.intelligence
            self.manaRegen = 5 * self.intelligence
            self.maxhp = 100 + 10*self.strength
            self.healthRegen = round(self.strength/3,2)

            self.view_distance = self._base_view_distance #apply armors too
            self.carry = 300 + self.agility * 10
            self.critchance = self._base_critchance + self.agility

            self.atk = self.strength #todo add this to weapon damage and ofc effects
            #self.armor = todo add this to armor and ofc effects

            for effect in self.effects:
                if effect.hasattr("hpeffect"):
                    self.healthRegen += effect.hpeffect["flat"]
                    self.healthRegen += self.maxhp * effect.hpeffect["multiplier"]
                    if effect.hpeffect["set"] is not None:
                        self.healthRegen = effect.hpeffect["set"]

                if effect.hasattr("maxhpeffect"):
                    self.maxhp += effect.maxhpeffect["flat"]
                    self.maxhp = self.maxhp * effect.maxhpeffect["multiplier"]
                    if effect.maxhpeffect["set"] is not None:
                        self.maxhp = effect.maxhpeffect["set"]

                if effect.hasattr("maxmanaeffect"):
                    self.maxmana += effect.maxmanaeffect["flat"]
                    self.maxmana = self.maxmana * effect.maxmanaeffect["multiplier"]
                    if effect.maxmanaeffect["set"] is not None:
                        self.maxmana = effect.maxmanaeffect["set"]

                if effect.hasattr("manaeffect"):
                    self.manaRegen += effect.manaeffect["flat"]
                    self.manaRegen += self.maxmana * effect.manaeffect["multiplier"]
                    if effect.manaeffect["set"] is not None:
                        self.manaRegen = effect.manaeffect["set"]

                if effect.hasattr("visioneffect"):
                    self.view_distance += effect.visioneffect["flat"]
                    self.view_distance = self._base_view_distance * effect.visioneffect["multiplier"]
                    if effect.visioneffect["set"] is not None:
                        self.view_distance = effect.visioneffect["set"]

                if effect.hasattr("critchanceeffect"):
                    self.critchance += effect.critchanceeffect["flat"]
                    self.critchance += self.critchance * effect.critchanceeffect["multiplier"]
                    if effect.critchanceeffect["set"] is not None:
                        self.critchance = effect.critchanceeffect["set"]

                if effect.hasattr("luckeffect"):
                    self.luck += effect.luckeffect["flat"]
                    self.luck *= effect.luckeffect["multiplier"]
                    if effect.luckeffect["set"] is not None:
                        self.luck = effect.luckeffect["set"]

                effect.tickEffect()

        def calculateTurn(self) -> None:
            self.recalculateStats()
            self.regenhealth()
            self.regenmana()

        def attemptFlee(self, enemies: list) -> bool: # slightly too hard to escape lol, maybe buff the agility by *10
            if self.agility >= random.randint(0, sum([i.atk for i in enemies])):
                return True

        def getCurrentTile(self):# -> RPGGame.Tile:
            x, y = self.position
            return self.terkep.grid[x][y]

        def levelup(self) -> None:
            if self.xp >= self.xpreq:
                self.xp -= self.xpreq
                self.xpreq *= 2
                self.lvl += 1

        async def attack(self, battlefield, hand, ctx: discord.Interaction):
            pchoice,target = None,None
            if isinstance(hand, RPGGame.AOESpell):
                if isinstance(hand, RPGGame.FriendlyAOESpell):
                    targets = battlefield.players
                elif isinstance(hand, RPGGame.EnemyAOESpell):
                    targets = battlefield.enemies
                else:
                    targets = battlefield.enemies #just so the ide doesnt trip up
                    print("impossible")  #TODO replace with logger call
                for entity in targets:
                    hand.use(self, entity)
                return

            elif isinstance(hand, RPGGame.FriendlySpell):
                if len([p for p in battlefield.players if p.hp > 0]) > 1:
                    pchoice = battlefield.players
                else:
                    target = battlefield.players[0]
            else:
                if len([enemy for enemy in battlefield.enemies if enemy.hp > 0]) > 1:
                    pchoice = battlefield.enemies
                else:
                    target = battlefield.enemies[0]

            if pchoice:
                viewObj = discord.ui.View()
                viewObj.add_item(RPGGame.TargetSelectView(choice, hand, self, battlefield))
                await ctx.edit(view=viewObj)
            else:
                hand.use(self, target)


        class LvlUpButtons(discord.ui.View):
            def __init__(self, player, ctx):
                self.player = player
                super().__init__()

            @discord.ui.button(emoji=emoji.emojize(":fist:", language="alias"), label="STR", style=discord.ButtonStyle.red)
            async def strbutton(self, button, ctx):
                self.player._base_strength += 1
                await self.finishlevelup(ctx)

            @discord.ui.button(emoji=emoji.emojize(":magic_wand:", language="alias"), label="INT", style=discord.ButtonStyle.blurple)
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

        class EquipSlot(discord.ui.Select):
            def __init__(self, itemtype: list, itemslot, player, backview, backembed):
                if not isinstance(itemtype, list):
                    itemtype = [itemtype]
                    logger.info(itemtype)
                self.itemtype = itemtype
                self.backview = backview
                self.backembed = backembed
                self.player = player
                self.itemslot = itemslot
                optionen = [discord.SelectOption(label="Cancel", emoji=emoji.emojize(":x:", language="alias"), value="-1")]
                for index,item in enumerate(self.player.inventory.values()): # find each item in inventory
                    logger.info(item)
                    if any((isinstance(item,i) for i in itemtype)): #that has the right type
                        optionen.append(item.toDropdown(index))
                super().__init__(placeholder="Select an item to equip", options=optionen)

            async def callback(self, ctx):
                player: RPGGame.Player = self.player
                selected = int(self.values[0])
                if selected != -1:
                    toSlot = list(player.inventory.values())[selected] #item to slot, no the slot to use
                    slotted = player.equipment[self.itemslot]
                    player.addLoot(slotted)  # TODO unless its empty
                    player.equipment[self.itemslot] = toSlot
                    player.removeItem(toSlot)
                await ctx.edit(embed=self.player.showEqp(), view=self.player.EquipButtons(self.player, self.backview, self.backembed))

        def listInv(self):
            embedVar = discord.Embed(title=f"{self.name}'s inventory", description="")
            for n, item in enumerate(self.inventory.values(), start=1):
                embedVar.description += f"**[{n}]** = *{str(item)}*\n"
            weight = sum([i.weight*i.amount for i in self.inventory.values()]) + sum([i.weight for i in self.equipment.values()])
            embedVar.set_footer(text=f"Carry capacity: {weight}/{self.carry}")
            return embedVar

        def showEqp(self):
            embedVar = discord.Embed(title=f"{self.name}'s equipment")
            for slot, item in self.equipment.items():
                embedVar.add_field(name=f"**{slot}:** *{item.showName()}*", value=item.showStats(), inline=False)
                embedVar.set_footer(text="Use the buttons below to equip different items")
            return embedVar

        class EquipButtons(discord.ui.View):
            def __init__(self, player, backview, backembed):
                self.player: RPGGame.Player = player
                self.backview: discord.ui.View = backview
                self.backembed: discord.Embed = backembed
                print("Sanika", self.player)
                super().__init__()

            @discord.ui.button(emoji=emoji.emojize(':womans_hat:',language="alias"))
            async def headbutton(self, button, ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot([RPGGame.HeadArmor],"Head",self.player,self.backview,self.backembed))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":t-shirt:",language="alias"))
            async def chestbutton(self,button,ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot(RPGGame.ChestArmor,"Chest",self.player,self.backview,self.backembed))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":jeans:",language="alias"))
            async def legsbutton(self,button,ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot(RPGGame.LegsArmor,"Legs",self.player,self.backview,self.backembed))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":hiking_boot:",language="alias"))
            async def shoesbutton(self,button,ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot(RPGGame.FeetArmor,"Feet",self.player,self.backview,self.backembed))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":gloves:",language="alias"))
            async def glovesbutton(self,button,ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot(RPGGame.HandsArmor,"Hands",self.player,self.backview,self.backembed))
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":left-facing_fist:",language="alias"))
            async def lefthandbutton(self,button,ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot([RPGGame.HandEquippable,RPGGame.Shield],"Left hand",self.player,self.backview,self.backembed))  #TODO add list of spells or waepons or shield to equip
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":right-facing_fist:",language="alias"))
            async def righthandbutton(self,button,ctx):
                viewObj = discord.ui.View()
                viewObj.add_item(self.player.EquipSlot([RPGGame.Weapon,RPGGame.Shield],"Right hand",self.player,self.backview,self.backembed)) #Here too
                await ctx.edit(view=viewObj)

            @discord.ui.button(emoji=emoji.emojize(":x:",language="alias"))
            async def cancelbutton(self,button,ctx):
                #self.player.checkLvlUp(self.backview)
                await ctx.edit(view=self.backview,embed=self.backembed)

        #@print_durations
        def discoverMap(self,sight_range):
            for row in self.discovered_mask[np.clip(self.position[0]-sight_range,0,self.terkep.mapsize):np.clip(self.position[0]+sight_range+1,0,self.terkep.mapsize)]:
                for col in range(np.clip(self.position[1]-sight_range,0,self.terkep.mapsize),np.clip(self.position[1]+sight_range+1,0,self.terkep.mapsize)):
                    row[col] = True

        #@print_durations

        def checkLvlUp(self,view):
            lvlupbutton = 4#th button in the view dont forget to change when poking around the UI
            if self.xp >= self.xpreq:
                #view.children[lvlupbutton].disabled = False
                view.children[lvlupbutton].style = discord.ButtonStyle.blurple
            else:
                #view.children[lvlupbutton].disabled = True
                view.children[lvlupbutton].style = discord.ButtonStyle.grey

        def move(self, direction, view):
            self.regenhealth()
            self.regenmana()
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
            return self.terkep.render(self.terkep.window,self)

        def handleTileDiscovery(self, view):
            currtile = self.getCurrentTile()
            currtile.discoverEnemies()
            currtile.isOnCooldown = True
            if currtile not in self.terkep.visitedTiles:
                self.terkep.visitedTiles.append(currtile)
                if len(self.terkep.visitedTiles) > self.terkep.tileRespawnTimer:
                    self.terkep.visitedTiles[0].isOnCooldown = False
                    self.terkep.visitedTiles.pop(0)
            if currtile.isDiscoverable:
                view.children[6].disabled = False
                view.children[6].style = discord.ButtonStyle.blurple
            else:
                view.children[6].disabled = True
                view.children[6].style = discord.ButtonStyle.grey

        def addLoot(self, loot):
            logger.info(self.inventory)
            logger.info(loot)
            if not isinstance(loot, list):
                loot: List[RPGGame.Item] = [loot]
            for item in loot:
                logger.info(item)
                if item.display_name in self.inventory.keys():
                    self.inventory[item.display_name].amount += item.amount
                else:
                    self.inventory.update({item.display_name: item})
            logger.info(self.inventory)

        def removeItem(self, item):
            logger.info(item)
            logger.info(self.inventory)
            if item.display_name in self.inventory.keys():
                logger.info(self.inventory[item.display_name])
                self.inventory[item.display_name].amount -= item.amount
                logger.info(self.inventory)
                if self.inventory[item.display_name].amount <= 0:
                    del self.inventory[item.display_name]


    bare_hands = Weapon(weight=0,price=None,damage=3,amount=None,wpntype="blunt",material=None,display_name="Fists")
    starter_shirt = ChestArmor(price=None,weight=1,amount=1,armor=0,material="Cloth",display_name="Torn shirt")
    starter_pants = LegsArmor(price=None,weight=1,amount=1,armor=0,material="Cloth",display_name="Plain pants")
    starter_boots = FeetArmor(price=None,weight=1,amount=1,armor=0,material="Cloth",display_name="Simple shoes")
    empty_armor = Armor(price=None,weight=0,amount=None,armor=0,material="Cloth",display_name="Empty")
    starter_shield = Shield(price=None,weight=5,amount=1,armor=5,material="Wooden",display_name="Wooden shield")

    class Terkep(object):
        #@print_durations
        def __init__(self, size, seed, window):
            self.mapsize = size
            self.grid: List[List] = Noise.makeMap(size, 1.5, seed)
            self.seed = seed
            self.players = []
            self.window = window
            self.tileRespawnTimer = 10
            self.visitedTiles = [] #these tiles are not to process for n amount of turns

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
            self.players = players
            self.player = player
            self.enemies = enemies
            self.interaction = interaction
            self.loot: List[RPGGame.Item] = []
            self.xp = 0
            self.gold = 0

        class TakeLootButtons(discord.ui.View):
            def __init__(self, loot, player):
                self.loot: List[RPGGame.Item] = loot
                self.player: RPGGame.Player = player
                super().__init__(timeout=100)

            @discord.ui.button(label="Leave loot", style=discord.ButtonStyle.red)
            async def leaveloot(self, button, ctx):
                self.loot = []
                await RPGCog.backToMap(ctx,self.player)


            @discord.ui.button(label="Select loot", style=discord.ButtonStyle.gray, disabled=True)
            async def pickloot(self, button, ctx):
                pass# TODO

            @discord.ui.button(label="Take all", style=discord.ButtonStyle.green)
            async def takeloot(self, button, ctx):
                self.player.addLoot(self.loot)
                await RPGCog.backToMap(ctx, self.player)

        async def display_loot(self, interaction: discord.Interaction):
            embedVar = discord.Embed(description="You found", color=interaction.user.color)
            for loot in self.loot:
                embedVar.add_field(name=loot.display_name, value=loot.stats())
            viewObj = self.TakeLootButtons(self.loot, self.player)
            await interaction.edit(content=None,embed=embedVar,view=viewObj)

        async def display_fight(self) -> discord.ui.View:
            viewObj = RPGGame.FightView(self.player, self)  # put enemies from tile here
            for button, hand in zip((viewObj.children[0], viewObj.children[1]),
                                    (self.player.equipment["Left hand"], self.player.equipment["Right hand"])):
                button.label = hand.display_name
                if isinstance(hand, RPGGame.Shield):
                    button.disabled = True  # maybe implement some functionality here, like chance to block? idk why

            #embedVar = discord.Embed(title="Fight")
            #for enemy in self.player.getCurrentTile().enemies:
            #    embedVar.add_field(name=enemy.display_name, value=enemy.showStats())

            await self.interaction.edit(content="\n".join(f"**{enemy}**" for enemy in self.enemies if enemy.hp > 0),
                                        embed=self.player.statEmbed(self.interaction.user.color),
                                        view=viewObj)
            return viewObj
            # await interaction.edit(embed=self.player.statEmbed(interaction.user.color),view=viewObj) #TODO put enemies in pic and use embed for players

        async def battle(self):
            while any(i.hp > 0 for i in self.players) and any(i.hp > 0 for i in self.enemies):
                logger.info(f"{self.players} vs {self.enemies}")
                for player in self.players:
                    if player.hp > 0:
                        if not player.AFK:
                            viewObj = await self.display_fight()
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
                                self.players.remove(player)
                atklog = ""
                for enemy in self.enemies:
                    if enemy.hp > 0:
                        atk = enemy.attack(self.players)
                        atklog += f"{atk}\n"
            else:
                if self.players:
                    logger.info("win")
                    for enemy in self.enemies:
                        self.loot.extend(enemy.lootTable) #TODO implement some randomizer here
                    await self.display_loot(self.interaction)
                    logger.info("displayed")
                    #TODO loot picker
                else:
                    logger.info("lose")

    class FightView(discord.ui.View):
        def __init__(self, player, battlefield):
            super().__init__(timeout=60, auto_defer=False)
            self.player: RPGGame.Player = player
            self.battlefield = battlefield
            # TODO self.view.stop() STOP the view manually after finishing the turn

        @discord.ui.button(label="self.player.equipment.weapon.display_name", style=discord.ButtonStyle.blurple, emoji=emoji.emojize(":left-facing_fist:", language="alias"))
        async def attackL(self, button, ctx):
            await self.player.attack(self.battlefield, self.player.equipment["Left hand"], ctx)
            self.stop()

        @discord.ui.button(label="self.player.equipment.weapon.display_name", style=discord.ButtonStyle.blurple, emoji=emoji.emojize(":right-facing_fist:", language="alias"))
        async def attackR(self, button, ctx):
            await self.player.attack(self.battlefield, self.player.equipment["Right hand"], ctx)
            self.stop()

        @discord.ui.button(emoji=emoji.emojize(":wine_glass:", language="alias"))
        async def potion(self, button, ctx):
            self.stop()
            pass

        @discord.ui.button(emoji=emoji.emojize(":t-shirt:", language="alias")) #TODO rethink if this should be posisble mid battle
        async def equipment(self, button, ctx):
            await ctx.edit(view=self.player.EquipButtons(self.player, self, ctx.message.embeds[0]), embed=self.player.showEqp())
            self.stop()

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
        logger.debug(player)
        await ctx.edit(content=player.terkep.render(player.terkep.window, player), view=viewObj, embed=player.statEmbed(ctx.user.color))

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
            await interaction.edit(embed=self.player.showEqp(), view=self.player.EquipButtons(self.player, self, interaction.message.embeds[0]))

        @discord.ui.button(style=discord.ButtonStyle.grey, emoji=emoji.emojize(":star:",language="alias"), disabled=False) #TODO show text and buttons depending if actually levelled up or not
        async def showlvlupbut(self, button, interaction):
            embedVar = discord.Embed(title="You have levelled up!", description=f"You have reached level **{self.player.lvl}**! You are now able to upgrade one of your attributes.",color=interaction.user.color)
            embedVar.add_field(name=f"Strength {self.player.strength} {emoji.emojize(':right_arrow:')} {self.player.strength+1}",value="Strength increases your **maximum health**, **health regeneration** and **weapon attack power**")
            embedVar.add_field(name=f"Intelligence {self.player.intelligence} {emoji.emojize(':right_arrow:')} {self.player.intelligence+1}",value="Intelligence increases your **maximum mana**, **mana regeneration** and **spell effectivity**")
            embedVar.add_field(name=f"Agility {self.player.agility} {emoji.emojize(':right_arrow:')} {self.player.agility+1}",value="Agility increases your **inventory capacity**, **parry** and **hit chances** and also increases your chance of **escaping** tough fights.")
            await interaction.edit(embed=embedVar, view=self.player.LvlUpButtons(self.player, interaction))
        #---------------------------row1--------------------------------------------

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":left_arrow:"), row=1)
        async def moveleft(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("left", self), embed=self.player.statEmbed(interaction.user.color), view=self)

##        @discord.ui.button(style=discord.ButtonStyle.gray,emoji=emoji.emojize(":OK_button:",language="alias"),row=1)
##        async def moveok(self,button,interaction):
##            await interaction.send("cmuk")

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":magnifying_glass_tilted_left:", language="alias"), row=1, disabled=True) #could be emoji.emojize(":mag:") as in magnifying glass to explore the place
        async def explore(self, button, interaction: discord.Interaction):
            tile = self.player.getCurrentTile()
            tile.isDiscoverable = False
            button.disabled = True
            await self.startfight(self.player.team, tile.enemies, self.player, interaction)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":right_arrow:"), row=1)
        async def moveright(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("right", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":package:", language="alias"), row=1)
        async def showinvbut(self, button, interaction):
            #await interaction.send(embed=self.player.showEqp(),view=self.player.EquipButtons())
            await interaction.edit(embed=self.player.listInv(), view=self.BackToMapButton(self.player))

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_lower_left:", language="alias"), row=2)
        async def moveleftdown(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("left down", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":down_arrow:"), row=2)
        async def movedown(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("down",self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emoji.emojize(":arrow_lower_right:", language="alias"), row=2)
        async def moverightdown(self, button, interaction):
            await interaction.response.edit_message(content=self.player.move("right down", self), embed=self.player.statEmbed(interaction.user.color),view=self)

        @discord.ui.button(style=discord.ButtonStyle.red, emoji=emoji.emojize(":x:", language="alias"), row=2)
        async def hidemapbutton(self, button, interaction):
            await interaction.response.edit_message(content="Map removed to improve the the Discord app's performance with their poor emoji rendering",view=None,embed=None)

        class BackToMapButton(discord.ui.View):
            def __init__(self, player):
                self.player = player
                super().__init__()

            @discord.ui.button(emoji=emoji.emojize(":left_arrow:"))
            async def backbutton(self, button, ctx):
                await RPGCog.backToMap(ctx, self.player)

        async def startfight(self, players, enemies, player, interaction: discord.Interaction):
            battle = RPGGame.Battlefield(players, enemies, player, interaction)
            await battle.display_fight()
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
        player.addLoot(new(pant2))
        pant2.armor += 5
        pant2.display_name = "Super awesome shorts"
        player.addLoot(pant2)
        shield = new(RPGGame.starter_shield)
        player.addLoot(shield)
        viewObj = self.MapMoveButtons(player)
        await ctx.send(player.move("down", viewObj), view=viewObj, embed=player.statEmbed(ctx.user.color))


def setup(client, baselogger):
    client.add_cog(RPGCog(client, baselogger))


if __name__ == "__main__":
    terkep = RPGGame.Terkep(140, randint(0, 100), 14)
