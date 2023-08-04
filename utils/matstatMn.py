from fractions import Fraction #na krasne printovanie cisiel ako zlomkov
from itertools import product as P_repeat #na generovanie vsetkych kombinacii hodov kockou
from itertools import combinations as C
from functools import lru_cache #na zrychlenie vypoctu, dont really give it too much thought
import matplotlib.pyplot as plt #na vykreslenie grafu
from numpy import prod #produkt, krátenie vsetkych elementov v zozname, som lazy to ručne robit
from math import ceil,floor

kocka = {i:0.2 for i in range(1,7)}
minca = {i:0.5 for i in range(0,2)}

def napoveda(f):
    """velmi smiesne"""
    return f.__doc__

def n_sided_dice(n):
    """vrati objekt s n udalostami a ich 1/n šancami
vstup:
    n = int"""
    return makePtable(range(1,n+1))
    #return {i:1/n for i in range(1,n+1)}

def gen_hody(sance: dict,n: int):
    """generuje vsetky mozne hody
tusim toto je vnutorna funkcia ale nepamatam si
pouzi skor Mn() alebo Dn()
vstup:
    sance: dictionary udalosti a ich sanci
    n: int - kolkokrat za pokus zosimulovat udalost"""
    return list(P_repeat(sance.keys(),repeat=n))

@lru_cache(maxsize=100000) #vynal som funkciu produkt zvlast aby som mohol cacheovat vysledky aby sa nemuseli furt znova prepocitavat lebo viacero hodov kockami sa zhoduje
def produkt(i: list):
    """sucin cisiel v liste
vstup:
    list"""
    if isinstance(i,str):
        return prod(list(map(float,i.split(",")))) #the faster method, lebo zoznamy sa nedaju cacheovať for some reason tak z nich urobim string a potom tu rozoberam
    return prod(i) #the 2x slower method

def Mn(sance: dict,n: int,operation="sum(hod)/n",prob=False) -> dict:
    """pomale takze nad n=9 neodporucam ist lol
vstup:
    n = pocet hodov
    sance = dictionary vysledkami hodom jednou kockou a ich sance napr {1:0.5 , 2:0.5}, alebo mozes pouzit minca,kocka,n_sided_dice(n)
    operation = aku operaciu vykonat na hodoch, sum(hod)/n je average hodu n kockami, max(hod) je maximum z hodov n kockami, sum(hod) je suma hodu n kockami napr
"""
    if "/" in operation:
        prob = True
    hody = gen_hody(sance,n) #presimulujem všetky možné hody kockami
    end_results = {} #dictionary kde keys budu priemery hodov kockami a ich values bude kumulativna šanca že sa ti podari tolko hodit
    for hod in hody:
        vysledok = eval(operation)
        
        #sanca_hodu = produkt(hod) #the 2x slower method
        
        sanca_hodu = produkt(",".join([str(sance[n]) for n in hod])) if prob else None #the 2x faster method, urobim z nich string lebo stringy sa daju cacheovat, vid funckiu produkt
        #print(sanca_hodu)
        try:
            end_results[vysledok] += sanca_hodu if prob else 1 #spocitavam sance toho, ze priemer hodu kockami bude "avg_of_hod"
        except KeyError: #ak sme taky average este nestretli,
            end_results[vysledok] = sanca_hodu if prob else 1 #.setdefault() by neslo
        
    return end_results

def tabulka(result: dict) -> str:
    """Vypise taubulku z result dictionary
vstup:
    dictionary of results"""
    return "\n"+"\n".join(sorted(["{:02d} = {}".format(i,Fraction(j).limit_denominator()) for i,j in result.items()])) # je to len fancy formatting

def graf(result):
    """vykresli graf z Mn"""
    plt.bar(*zip(*result.items()),width=(30/len(result.items()))) # nemozem za to ze matplotlib kniznica ma tak skaredu syntaxu
    plt.show()

def Ex(X):
    """alias for stred()"""
    return stred(X)

def stred(sance: dict) -> float:
    """stredobod/vazeny priemer/E(X)
suma kazdeho X * P , kde X je result hodu kockou a P je šance že to X padne
vstup:
    sance: dictionary so šancami"""
    return sum([i*j for i,j in sance.items()]) #suma kazdeho X * P , kde X je result hodu kockou a P je šance že to X padne

def Dn(result: dict,sance: dict) -> float: 
    """variacia/rozptyl/disperzia
suma kazdeho M^2 * P^2 minus stredobod^2
vstup:
result: dict
sance: dict"""
    return sum([(i**2)*j for i,j in result.items()]) - (stred(sance)**2) # suma kazdeho M^2 * P^2 minus stredobod^2

#//////////////////////////////////////////////////////////////////////

def rozptyl(array: list) -> float:
    """s2 variacia iba z vektora
variacia zoznamu cisiel basically
vstup:
    list"""
    mean = avg(array)
    return sum([(i - mean)**2 for i in array])/len(array)

def makeList(table: dict) -> list:
    """makes py list from tabulka pocetnosti.
input: dict {1:3,2:5}"""
    #print(table)
    a = list()
    for k,v in table.items():
        for _ in range(v):
            a.append(k)
    
    return a

def makePtable(array: list) -> dict:
    """make P(robability)_table dict from array of numbers
[2,2,2,3,4] -> {2:3/5,3:1/5,4:1/5}
vstup:
    list"""
    P_table = {}
    for i in set(array):
        P_table.update({i:Fraction(array.count(i)/len(array)).limit_denominator()})
    return P_table
        
def avg(array: list) -> float:
    """list in, average out as float
vstup:
    list"""
    return sum(array)/len(array)

def mean(array: list) -> float:
    """alias for avg()"""
    return avg(array)

def quantil(array: list,quant: float) -> float:
    """kvantil.
vstup:
    list čisiel,
    kvantil: float"""
    a = sorted(array)[ceil(quant*len(array))-1]    
    b = sorted(array)[-(ceil((1-quant)*len(array)))]
    return (a+b)/2

def median(array: list) -> float:
    """0.5 kvantil
vstup:
    list"""
    return quantil(array,0.5)

def rozsahQuant(rozsahy: dict,quant: float) -> float:
    """quantil but with rozsahy ako input dict. napr pri prikladoch 0-56 FX, 94-100 A chapes
vstup by mal byt dict z range a int pármi napr {range(0,56): 5,range(94-100): 2}"""
    suma = sum(rozsahy.values())
    relatives = [i/suma for i in rozsahy.values()]
    cumuls = [sum(relatives[0:i+1]) for i in range(len(relatives))]
    sirky = [len(i) for i in rozsahy.keys()]
    extendedcumuls = sum(([0],cumuls),[])
    betweens = [(extendedcumuls[i],extendedcumuls[i+1]) for i in range(len(extendedcumuls)-1)]
    for n,i in enumerate(betweens):
        if i[0] <= quant < i[1]:
            return min(list(rozsahy.keys())[n])+(quant-extendedcumuls[n])*sirky[n]/relatives[n]
    else:
        return min(list(rozsahy.keys())[n])+(quant-extendedcumuls[n])*sirky[n]/relatives[n]

def Bi(n: int,p: float,k: int) -> float:
    """Binomické rozdelenie
vstup:
    n = total pokusov
    p = šanca vyhodneho vysledku
    k = pocet vyhodnych vysledkov"""
    return len(list(C(range(n),k)))*(p**k)*((1-p)**(n-k)) #C total over vhodn * (sanca ^ vhodn) * (inverse of sanca ^ nevhodn)

def BiRange(chance: float,n: range) -> dict:
    """Binomicke rozdlenie ale naraz s viacerymi cislami
vracia dictionary resultov
vstup:
    chance: float
    range: range(a,b) kde b je exkluzivne
p,k su vypocitane z range"""
    return {i:Bi(max(n),chance,i) for i in n}

def Venn(circles: str) -> set:
    """spravi set segmentov z ven diagramu spocivajuc z kruhov, rozdelenych ciarkov
input: string napr: "A,B,C"
output: {A,B,AuB...}"""
    segments = sorted([sorted(i) for i in P_repeat(circles.split(","),repeat=len(circles.split(",")))])
    return set(["u".join(set(i)) for i in segments])
        
#//////////////////////////////////////

if __name__ == "__main__": #tu dole uz len na skusanie testovanie kodu
    pass
    #P_table = {1:0.3,0:0.7}
    #P_table = {}
    #[P_table.update({i:1/6}) for i in range(1,7)]
    #result = Mn(P_table,6)
    #print(tabulka(result))
    #print(Bi(10,0.3,6))
    #a = makePtable([2,2,3,3,4,4,4,4,5,5,5,7])
##    a = {1:5,2:3,3:8,4:1,5:0,6:2}
##    b = makeList(a)
##    b = quantil(b,0.25)
##    print(b)
    #print(BiRange(3/24,range(0,4)))
    #res = Mn(kocka,n=4,prob=True)
    #print(res)
    #print(tabulka(res))

#/////////////

##rozsahy = {
##range(0,2):27,
##range(2,6):84,
##range(6,12):277,
##range(12,15):61,
##range(15,20):19,
##range(20,30):3
##    }
##
##for i in (0.5,0.25,0.75,0.15,0.33,0.9):
##    print(i,"=",rozsahQuant(rozsahy,i))

#print(Bi(20,80,18))
# graf(Mn(kocka,2,operation="sum(hod)"))

#print(rozsahQuant(rozsahy,0.25))
#arr = makeList("[3 9 7 3 1 5 7 9 3 1]")
#arr = [54,70,45,30,1]
##
##print(*["kvantil {} = {}\n".format(i,quantil(arr,i)) for i in (0.11,0.24,0.72)])
##
##P = makePtable(arr)
##print(tabulka(P))
##graf(P)
##      
##plt.boxplot(arr,vert=False)
##plt.show()
