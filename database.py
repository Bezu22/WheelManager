import sqlite3
import os
import json

class InventoryDB:
    def __init__(self, db_path, config_path):
        """
        Inicjalizacja bazy danych i wczytanie konfiguracji.
        Obie ścieżki są przekazywane jako atrybuty.
        """
        self.db_path = db_path
        self.config_path = config_path
        self.dane = {"konfiguracja": {}}
        
        # Próba wczytania konfiguracji z pliku. 
        # Brak metody domyślnej wymusza istnienie pliku JSON.
        self.wczytaj_konfiguracje()
        self.setup_db()

    def polacz(self):
        """Sprawdza czy można nawiązać połączenie z bazą na dysku."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except Exception:
            return False

    def wczytaj_konfiguracje(self):
        """
        Wczytuje strukturę konfiguracji bezpośrednio z pliku JSON.
        Jeśli plik nie istnieje lub jest uszkodzony, rzuca błąd, co zapobiega 
        działaniu programu na nieprawidłowych danych[cite: 6].
        """
        if not os.path.exists(self.config_path):
            print(f"BŁĄD: Plik konfiguracji {self.config_path} nie istnieje!")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.dane["konfiguracja"] = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"BŁĄD podczas wczytywania JSON: {e}")

    def setup_db(self):
        """Inicjalizuje tabelę SQLite, jeśli nie istnieje w podanej lokalizacji[cite: 6]."""
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
        """Pobiera dane z filtrowaniem dla wyszukiwarki[cite: 6]."""
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
        """Dodaje nową pozycję do bazy danych[cite: 6]."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sciernice (typ, kat, opis, ziarno, producent, magazyn)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (typ, kat, opis, ziarno, producent, ilosc_start))
        conn.commit()
        conn.close()

    def aktualizuj_pozycje(self, id_pozycji, nowe_dane):
        """Aktualizuje istniejącą pozycję na podstawie słownika z GUI[cite: 6]."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
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
        """Usuwa ściernicę o danym ID z bazy[cite: 6]."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM sciernice WHERE id=?", (id_pozycji,))
        conn.commit()
        conn.close()

    @property
    def lista_typow(self):
        """Pomocnicza metoda zwracająca tylko nazwy typów do ComboBoxa z JSON[cite: 6]."""
        return list(self.dane["konfiguracja"].get("typy_ustawienia", {}).keys())