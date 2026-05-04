import sqlite3
import os

class InventoryDB:
    def __init__(self, db_path):
        self.db_path = db_path
        # Przykładowa konfiguracja (można ją przenieść do osobnego JSONa później)
        self.dane = {
            "konfiguracja": {
                "typy": ["1A1", "1V1", "11V9", "1S1"],
                "producenci": ["Tyrolit", "Toolgal", "DrMuller"],
                "statusy": ["magazyn", "W uzyciu", "zamowiona", "zlom"]
            }
        }
        self.setup_db()

    def polacz(self):
        """Sprawdza czy można nawiązać połączenie z bazą na dysku."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except Exception:
            return False

    def setup_db(self):
        """Inicjalizuje tabelę jeśli nie istnieje."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sciernice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                typ TEXT,
                kat TEXT,
                opis TEXT,
                ziarno TEXT,
                producent TEXT,
                magazyn INTEGER DEFAULT 0,
                uzycie INTEGER DEFAULT 0,
                zamowiona INTEGER DEFAULT 0,
                zlom INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def pobierz_dane(self, filtr=""):
        """Pobiera dane z filtrowaniem pod Searchbar."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT * FROM sciernice WHERE typ LIKE ? OR opis LIKE ? OR producent LIKE ?"
        f = f"%{filtr}%"
        cur.execute(query, (f, f, f))
        
        rows = cur.fetchall()
        wynik = []
        for r in rows:
            wynik.append({
                "id": r["id"],
                "typ": r["typ"],
                "kat": r["kat"],
                "opis": r["opis"],
                "ziarno": r["ziarno"],
                "producent": r["producent"],
                "ilosc": {
                    "magazyn": r["magazyn"],
                    "W uzyciu": r["uzycie"],
                    "zamowiona": r["zamowiona"],
                    "zlom": r["zlom"]
                }
            })
        conn.close()
        return wynik

    def dodaj_sciernice(self, typ, kat, opis, ziarno, producent, ilosc_start):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sciernice (typ, kat, opis, ziarno, producent, magazyn)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (typ, kat, opis, ziarno, producent, ilosc_start))
        conn.commit()
        conn.close()

    def aktualizuj_pozycje(self, id_pozycji, nowe_dane):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # Mapowanie kluczy z GUI na kolumny SQL
        cur.execute("""
            UPDATE sciernice 
            SET opis=?, kat=?, magazyn=?, uzycie=?, zamowiona=?, zlom=?
            WHERE id=?
        """, (
            nowe_dane["opis"], 
            nowe_dane["kat"], 
            nowe_dane["ilosc"].get("magazyn", 0),
            nowe_dane["ilosc"].get("W uzyciu", 0),
            nowe_dane["ilosc"].get("zamowiona", 0),
            nowe_dane["ilosc"].get("zlom", 0),
            id_pozycji
        ))
        conn.commit()
        conn.close()

    def usun_pozycje(self, id_pozycji):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM sciernice WHERE id=?", (id_pozycji,))
        conn.commit()
        conn.close()