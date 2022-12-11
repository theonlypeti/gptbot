import math

from tabulate import tabulate
# pstring = 'ababbabbabbababbabb'


def pitable(pstring: str) -> list[int]:
    pi = [0]
    for i in range(2, len(pstring)+1):
        # print("--",i)
        slice = pstring[:i]
        char = pi[-1]
        # print(slice[:char + 1],slice[-char - 1:])
        if slice[:char + 1] == slice[-char - 1:]:
            pi.append(char + 1)
        else:
            pi.append(0)
            for char2 in range(char+1):
                # print(slice[:char2 + 1],"aa",slice[-char2 - 1:], "sanyi")
                if slice[:char2 + 1] == slice[-char2 - 1:]:
                    pi[-1] = char2 + 1
    return pi


def prettypitable(pstring: str) -> str:
    pi = pitable(pstring)
    iis = ["i"] + [f"{i:4d}" for i in range(1, len(pstring) + 1)]
    pis = ["π(i)"] + [f"{i:4d}" for i in pi]
    ks = ["k"] + [f"0/{pi[0]}"] + [f"{pi[i - 1]}/{pi[i]}" for i in range(1, len(pstring))]
    return tabulate([" " + pstring, iis, pis, ks], tablefmt="fancy_grid")


def automat(pstring: str) -> dict:
    abc = set(pstring)
    pi = pitable(pstring)
    tab = {char: [0] * (len(pstring)+1) for char in abc}
    for n,char in enumerate(pstring, start=0):
        if n != 0:
            for row in tab.values():
                row[n] = row[pi[n - 1]]
        tab[char][n] = n + 1
    n = len(pstring)
    for row in tab.values():
        row[n] = row[pi[n - 1]]
    return tab


def prettyautomat(pstring: str) -> str:
    tab = automat(pstring)
    iis = ["(i)"] + [str(i) for i in range(len(pstring) + 1)]
    return tabulate([" "+pstring, iis, *[[k] + v for k,v in tab.items()]], tablefmt="fancy_grid")


def piautomat(pstring: str) -> str:
    return prettypitable(pstring) + "\n\n" + prettyautomat(pstring)


if __name__ == "__main__":
    print(piautomat("ababbabbabbababbabb"))
    print(piautomat("LALLL"))
    print(piautomat("ababa"))
