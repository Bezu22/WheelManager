import sqlite3
import os
import json
from datetime import datetime 

class InventoryDB:
    def __init__(self, db_path, config_path):
        self.db_path = db_path
        self.config_path = config_path
        self.dane = {"konfiguracja": {}}
        self.wczytaj_konfiguracje()
        self.setup_db()

    def polacz(self):
        """Sprawdza dostępność bazy danych."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except Exception:
            return False

    def wczytaj_konfiguracje(self):
        """Wczytuje strukturę z JSON bez wartości domyślnych w kodzie."""
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
        """Dodaje nową pozycję i zapisuje fakt utworzenia w logu TXT."""
        ziarno_std = str(ziarno).upper()
        kat_std = str(kat).replace(',', '.')
        opis_std = str(opis).replace(',', '.')

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sciernice (typ, kat, opis, ziarno, producent, magazyn)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (typ, kat_std, opis_std, ziarno_std, producent, ilosc_start))
        
        # Pobieramy ID nowo dodanego elementu, aby log był precyzyjny
        nowe_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Zapis do pliku TXT
        szczegoly = f"Typ: {typ}, Opis: {opis_std}, Startowa ilość: {ilosc_start}"
        self._zapisz_log_txt(nowe_id, "NOWA POZYCJA", szczegoly)

    def aktualizuj_pozycje(self, id_pozycji, nowe_dane):
        """Aktualizuje dane i zapisuje zmiany do pliku TXT."""
        # 1. Pobieramy stan obecny z bazy, żeby wiedzieć co się zmieni[cite: 2]
        stare_dane = None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM sciernice WHERE id=?", (id_pozycji,))
        stare_dane = cur.fetchone()
        conn.close()

        if not stare_dane:
            return

        # 2. Porównujemy stare z nowym
        zmiany = []
        pola_do_sprawdzenia = {
            "magazyn": nowe_dane["ilosc"].get("magazyn", 0),
            "uzycie": nowe_dane["ilosc"].get("W uzyciu", 0),
            "zamowiona": nowe_dane["ilosc"].get("zamowiona", 0),
            "zlom": nowe_dane["ilosc"].get("zlom", 0)
        }

        for klucz, nowa_val in pola_do_sprawdzenia.items():
            stara_val = stare_dane[klucz]
            if int(stara_val) != int(nowa_val):
                zmiany.append(f"{klucz} ({stara_val}->{nowa_val})")

        # 3. Jeśli wykryto zmiany, zapisz do pliku TXT
        if zmiany:
            self._zapisz_log_txt(id_pozycji, "EDYCJA", ", ".join(zmiany))

        # 4. Zapisujemy nowe dane do bazy danych[cite: 2]
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            UPDATE sciernice 
            SET opis=?, kat=?, magazyn=?, uzycie=?, zamowiona=?, zlom=?
            WHERE id=?
        """, (
            str(nowe_dane["opis"]).replace(',', '.'),
            str(nowe_dane["kat"]).replace(',', '.'),
            pola_do_sprawdzenia["magazyn"],
            pola_do_sprawdzenia["uzycie"],
            pola_do_sprawdzenia["zamowiona"],
            pola_do_sprawdzenia["zlom"],
            id_pozycji
        ))
        conn.commit()
        conn.close()

    def usun_pozycje(self, id_pozycji):
        """Pobiera dane o pozycji, usuwa ją z bazy i zapisuje fakt w logu TXT."""
        # 1. Najpierw pobierz dane, żeby wiedzieć co usuwasz
        informacja_o_usuwanym = "Nieznany element"
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT typ, opis FROM sciernice WHERE id=?", (id_pozycji,))
            row = cur.fetchone()
            if row:
                informacja_o_usuwanym = f"{row['typ']} - {row['opis']}"
            
            # 2. Usuń rekord
            cur.execute("DELETE FROM sciernice WHERE id=?", (id_pozycji,))
            conn.commit()
            conn.close()
            
            # 3. Zapisz do logu TXT
            self._zapisz_log_txt(id_pozycji, "USUNIĘCIE", informacja_o_usuwanym)
            
        except Exception as e:
            print(f"Błąd podczas usuwania: {e}")

    def _zapisz_log_txt(self, id_sciernicy, akcja, szczegoly):
        """Zapisuje zdarzenie do pliku historia.txt w folderze bazy danych."""
        # Tworzymy ścieżkę do pliku logu w tym samym folderze co baza danych
        log_path = os.path.join(os.path.dirname(self.db_path), "historia_zmian.txt")
        
        teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        wpis = f"[{teraz}] ID:{id_sciernicy} | Akcja: {akcja} | Zmiany: {szczegoly}\n"
        
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(wpis)
        except Exception as e:
            print(f"Błąd zapisu logu: {e}")

    @property
    def lista_typow(self):
        """Zwraca klucze typów z konfiguracji[cite: 6]."""
        return list(self.dane["konfiguracja"].get("typy_ustawienia", {}).keys())