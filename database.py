import sqlite3
import os
import json

class InventoryDB:
    def __init__(self, db_path, config_path):
        self.db_path = db_path
        self.config_path = config_path
        self.dane = {"konfiguracja": {}}
        self.wczytaj_konfiguracje()
        self.setup_db()

    def polacz(self):
        """Sprawdza dostępność bazy danych[cite: 6]."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except Exception:
            return False

    def wczytaj_konfiguracje(self):
        """Wczytuje strukturę z JSON bez wartości domyślnych w kodzie[cite: 6]."""
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.dane["konfiguracja"] = json.load(f)
        except Exception as e:
            print(f"Błąd wczytywania JSON: {e}")

    def setup_db(self):
        """Tworzy tabelę SQLite[cite: 6]."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sciernice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                typ TEXT, kat TEXT, opis TEXT, ziarno TEXT, 
                producent TEXT, magazyn INTEGER DEFAULT 0, 
                uzycie INTEGER DEFAULT 0, zamowiona INTEGER DEFAULT 0, zlom INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def pobierz_dane(self, filtr=""):
        """Pobiera dane uwzględniając ziarno i parametr w wyszukiwarce[cite: 6]."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = """
            SELECT * FROM sciernice 
            WHERE typ LIKE ? OR opis LIKE ? OR producent LIKE ? OR ziarno LIKE ? OR kat LIKE ?
        """
        f = f"%{filtr}%"
        cur.execute(query, (f, f, f, f, f))
        
        rows = cur.fetchall()
        wynik = []
        for r in rows:
            wynik.append({
                "id": r["id"], "typ": r["typ"], "kat": r["kat"], "opis": r["opis"],
                "ziarno": r["ziarno"], "producent": r["producent"],
                "ilosc": {
                    "magazyn": r["magazyn"], "W uzyciu": r["uzycie"], 
                    "zamowiona": r["zamowiona"], "zlom": r["zlom"]
                }
            })
        conn.close()
        return wynik

    def dodaj_sciernice(self, typ, kat, opis, ziarno, producent, ilosc_start):
        """Dodaje nową pozycję ze standaryzacją znaków[cite: 6]."""
        ziarno_std = str(ziarno).upper()
        kat_std = str(kat).replace(',', '.')
        opis_std = str(opis).replace(',', '.')

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sciernice (typ, kat, opis, ziarno, producent, magazyn)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (typ, kat_std, opis_std, ziarno_std, producent, ilosc_start))
        conn.commit()
        conn.close()

    def aktualizuj_pozycje(self, id_pozycji, nowe_dane):
        """Aktualizuje dane z zamianą przecinków na kropki[cite: 6]."""
        opis_std = str(nowe_dane["opis"]).replace(',', '.')
        kat_std = str(nowe_dane["kat"]).replace(',', '.')
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            UPDATE sciernice 
            SET opis=?, kat=?, magazyn=?, uzycie=?, zamowiona=?, zlom=?
            WHERE id=?
        """, (
            opis_std, kat_std, 
            nowe_dane["ilosc"].get("magazyn", 0),
            nowe_dane["ilosc"].get("W uzyciu", 0),
            nowe_dane["ilosc"].get("zamowiona", 0),
            nowe_dane["ilosc"].get("zlom", 0),
            id_pozycji
        ))
        conn.commit()
        conn.close()

    def usun_pozycje(self, id_pozycji):
        """Usuwa rekord z bazy[cite: 6]."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM sciernice WHERE id=?", (id_pozycji,))
        conn.commit()
        conn.close()

    @property
    def lista_typow(self):
        """Zwraca klucze typów z konfiguracji[cite: 6]."""
        return list(self.dane["konfiguracja"].get("typy_ustawienia", {}).keys())