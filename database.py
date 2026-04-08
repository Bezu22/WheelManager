import json
import os

class InventoryDB:
    def __init__(self, filename="magazyn.json"):
        self.filename = filename
        self.dane = None

    def polacz(self):
        """Sprawdza czy plik istnieje i go wczytuje. Nie tworzy pliku automatycznie."""
        if not os.path.exists(self.filename):
            return False
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                self.dane = json.load(f)
            return True
        except (json.JSONDecodeError, Exception):
            return False

    def zapisz(self):
        if self.dane:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.dane, f, indent=4)

    def dodaj_sciernice(self, typ, opis, ziarno, producent, ilosc_magazyn):
        statusy_startowe = {s: 0 for s in self.dane["konfiguracja"]["statusy"]}
        try:
            statusy_startowe["magazyn"] = int(ilosc_magazyn)
        except (ValueError, TypeError):
            statusy_startowe["magazyn"] = 0

        nowa = {
            "id": len(self.dane["sciernice"]) + 1,
            "typ": typ,
            "opis": opis,
            "ziarno": ziarno,
            "producent": producent,
            "ilosc": statusy_startowe
        }
        self.dane["sciernice"].append(nowa)
        self.zapisz()

    def aktualizuj_pozycje(self, id_pozycji, nowe_dane):
        for i, s in enumerate(self.dane["sciernice"]):
            if s["id"] == id_pozycji:
                self.dane["sciernice"][i].update(nowe_dane)
                break
        self.zapisz()