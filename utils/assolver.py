import math

def solver(cisla: str) -> str:
    """
    Expected format:
    (1,2,3)o(4,5,6)o(7,8,9)"""
    cisla = cisla.replace(",","")
    perms = cisla.split("o")
    permy = []
    for perm in perms:
        permy.append(perm.strip("(").strip(")").split(")("))
    pocitam = 1
    
    najdene = [[]]
    hladany  = pocitam
    while pocitam < 8:
        if str(hladany) not in sum(najdene,[]):
            hladany = str(hladany)
            najdene[-1].append(hladany)
            for perm in reversed(permy):
                for cyklus in perm:
                    if hladany in cyklus:
                        hladany = cyklus[(cyklus.index(hladany)+1) % len(cyklus)]
                        break
        else:
            pocitam += 1
            hladany = pocitam
            najdene.append([])
                        
        hladany = int(hladany)
    najdene = [i for i in najdene if len(set(i)) > 1]
    out = ""
    for i in najdene:
        out += (f"({''.join(i)})")
    return out

def solver2(mnozina: str) -> str:
    """
        Expected format:
        (a,b,c,d)o(a,d,c,b)"""
    mnozina = mnozina.split("o")
    mnozina,perm = mnozina
    if mnozina[2] == ",":
        mnozina = mnozina.strip(")").strip("(").split(",")
    else:
        mnozina = mnozina.strip(")").strip("(")

    if perm[2] == ",":
        perm = perm.strip(")").strip("(").split(",")
    else:
        perm = perm.strip(")").strip("(")
    
    nove = []
    for pismenko in reversed(mnozina):
        try:
            a=perm[(perm.index(pismenko)+1)%len(perm)]
        except ValueError:
            a = pismenko
        nove.insert(0,a)
    return "".join(nove)

def solver3(perm:str)->str:
    """
    Expected format:
    (1,2,3)^3"""
    perm, mocnina = perm.split("^")
    cisla = perm.replace(",", "")
    permy = cisla.strip("(").strip(")").split(")(")
    pocty = [len(i) for i in permy]
    nsn = math.lcm(*pocty)
    return solver("o".join([perm for _ in range(int(mocnina)%nsn)])) or "Identita"

