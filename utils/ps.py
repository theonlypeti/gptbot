from math import log
from typing import Generator

class Adress:
    def __init__(self, ip:str , mask: int = None, adresses:int = None):
        assert adresses or mask and 24 <= mask <= 32
        self.ip = ip
        self._first_three = ".".join(ip.split(".")[:3])
        self.mask = mask or int(32-log(adresses,2)) #maska
        self.adresses = adresses or 2**(32-mask) #pocet adries
        try:
            self._lastbyte = int(self.ip.split(".")[-1])
        except ValueError as e:
            raise e

        self._id_byte = self._lastbyte // self.adresses * self.adresses
        self.ids = f"{self._first_three}.{self._id_byte}"

        self._broadcast_byte = self._id_byte + self.adresses - 1
        self.broadcast = f"{self._first_three}.{self._broadcast_byte}"

        self.first_host = f"{self._first_three}.{self._id_byte + 1 if self._id_byte + 1 != self._lastbyte else self._id_byte + 2}" if self.adresses > 2 else "---"
        self.last_host = f"{self._first_three}.{self._broadcast_byte - 1 if self._broadcast_byte - 1 != self._lastbyte else self._broadcast_byte - 2}" if self.adresses > 2 else "---"
        self.binary_mask = int(((self.mask-24)*"1").ljust(8,"0"),2)
        self.hosts = self.adresses - 2

def ipcalc(ip:str,adresy:int=None,mask:int=None):
    """ip: string, staci aj posledny byte, maska sa zadava /xy alebo ak neznama tak
    adresy: int = pocet adries ak maska neznama"""
    calc = Adress(ip,adresses=adresy,mask=mask)
    return f"""
pocet adries: {calc.adresses} , počet hostov: {calc.hosts}, maska: /{calc.mask} alebo 255.255.255.{calc.binary_mask}
id: {calc.ids}
prvy najmensi host: {calc.first_host}
posledny najvacsi host: {calc.last_host}
broadcast: {calc.broadcast}

"""

def broadcasty(ip:str) -> Generator[Adress,None,None]:
    """vstup:
    ip: string staci aj posledny byte"""
    return (Adress(ip,adresses=2**i) for i in range(2,6))

if __name__ == "__main__":
    print(ipcalc("192.168.1.129",adresy=256))
    print(broadcasty("192.168.1.97"))
