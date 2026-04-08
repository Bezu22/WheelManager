import json
import os

class InventoryDB:
    def __init__(self, filename="magazyn.json"):
        self.filename = filename
        self.dane = self._wczytaj_baze()

    def _wczytaj_baze(self):
        if not os.path.exists(self.filename):
            default_data = {
                "konfiguracja": {
                    "typy": ["1A1", "1V1", "11V9"],
                    "producenci": ["Tyrolit", "Toolgal", "DrMuller"],
                    "statusy": ["W uzyciu", "magazyn", "zamowiona", "złom"]
                },
                "sciernice": []
            }
            self._zapisz(default_data)
            return default_data
        
        with open(self.filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def _zapisz(self, dane=None):
        do_zapisu = dane if dane else self.dane
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(do_zapisu, f, indent=4)

    def dodaj_sciernice(self, typ, opis, ziarno, producent, status):
        nowa = {
            "id": len(self.dane["sciernice"]) + 1,
            "typ": typ,
            "opis": opis,
            "ziarno": ziarno,
            "producent": producent,
            "status": status
        }
        self.dane["sciernice"].append(nowa)
        self._zapisz()

    def sortuj(self, klucz, reverse):
        self.dane["sciernice"].sort(key=lambda x: str(x[klucz]).lower(), reverse=reverse)