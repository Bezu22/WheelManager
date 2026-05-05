import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

class InventoryDB:
    def __init__(self, db_path, config_path, log_path):
        self.db_path = db_path
        self.config_path = config_path
        self.log_path = log_path
        self.dane = {"konfiguracja": {}}
        self.wczytaj_konfiguracje()
        self.setup_db()

    @contextmanager
    def _connection(self):
        """Prywatny menedżer połączeń z obsługą timeoutu dla dysków sieciowych."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _execute(self, query, params=(), fetch=False):
        """Uniwersalna metoda wykonawcza redukująca powtarzalność kodu."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            if fetch:
                return [dict(row) for row in cur.fetchall()]
            return cur.lastrowid

    def polacz(self):
        """Sprawdza dostępność bazy."""
        try:
            self._execute("SELECT 1")
            return True
        except Exception:
            return False

    def wczytaj_konfiguracje(self):
        """Wczytuje strukturę z JSON."""
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.dane["konfiguracja"] = json.load(f)
        except Exception as e:
            self._zapisz_log("ERROR", f"Błąd JSON: {e}")

    def setup_db(self):
        """Inicjalizacja tabel."""
        self._execute("""
            CREATE TABLE IF NOT EXISTS sciernice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                typ TEXT, kat TEXT, opis TEXT, ziarno TEXT, 
                producent TEXT, magazyn INTEGER DEFAULT 0, 
                uzycie INTEGER DEFAULT 0, zamowiona INTEGER DEFAULT 0, zlom INTEGER DEFAULT 0
            )
        """)

    def pobierz_dane(self, filtr="", aktywne_filtry=None, filter_order=None):
        """Pobiera dane z dynamicznym sortowaniem."""
        query = "SELECT * FROM sciernice WHERE (opis LIKE ? OR kat LIKE ?)"
        params = [f"%{filtr}%", f"%{filtr}%"]
        
        if aktywne_filtry:
            for col, values in aktywne_filtry.items():
                if values:
                    placeholders = ", ".join(["?"] * len(values))
                    query += f" AND {col} IN ({placeholders})"
                    params.extend(values)
        
        # Logika priorytetów sortowania
        order_clauses = []
        if filter_order:
            for col in filter_order:
                order_clauses.append(f"{col} ASC")
        
        domyslne = ["typ", "ziarno", "producent", "opis"]
        for d in domyslne:
            if not any(d in c for c in order_clauses):
                order_clauses.append(f"{d} ASC")
        
        query += " ORDER BY " + ", ".join(order_clauses)
        return self._execute(query, params, fetch=True)

    def dodaj_sciernice(self, dane_dict):
        """Dodaje pozycję i loguje fakt."""
        query = """
            INSERT INTO sciernice (typ, kat, opis, ziarno, producent, magazyn)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            dane_dict['typ'], 
            str(dane_dict['kat']).replace(',', '.'), 
            str(dane_dict['opis']).replace(',', '.'),
            str(dane_dict['ziarno']).upper(), 
            dane_dict['producent'], 
            dane_dict['magazyn']
        )
        nowe_id = self._execute(query, params)
        self._zapisz_log("DODANO", f"ID:{nowe_id} | {dane_dict['typ']} {dane_dict['opis']}")
        return nowe_id

    def aktualizuj_pozycje(self, id_poz, nowe_dane):
        """Aktualizuje rekord z logowaniem różnic."""
        stare = self._execute("SELECT * FROM sciernice WHERE id=?", (id_poz,), fetch=True)
        if not stare: return
        
        stare = stare[0]
        zmiany = []
        # Logika porównywania (skrócona dla czytelności)
        for k in ['magazyn', 'uzycie', 'zamowiona', 'zlom']:
            n_val = nowe_dane['ilosc'].get(k if k != 'uzycie' else 'W uzyciu', 0)
            if int(stare[k]) != int(n_val):
                zmiany.append(f"{k}: {stare[k]}->{n_val}")
        
        if zmiany:
            self._zapisz_log("AKTUALIZACJA", f"ID:{id_poz} | " + ", ".join(zmiany))

        query = """
            UPDATE sciernice SET opis=?, kat=?, magazyn=?, uzycie=?, zamowiona=?, zlom=? WHERE id=?
        """
        params = (
            str(nowe_dane['opis']).replace(',', '.'),
            str(nowe_dane['kat']).replace(',', '.'),
            nowe_dane['ilosc'].get('magazyn', 0),
            nowe_dane['ilosc'].get('W uzyciu', 0),
            nowe_dane['ilosc'].get('zamowiona', 0),
            nowe_dane['ilosc'].get('zlom', 0),
            id_poz
        )
        self._execute(query, params)

    def usun_pozycje(self, id_poz):
        """Usuwa rekord i loguje."""
        info = self._execute("SELECT typ, opis FROM sciernice WHERE id=?", (id_poz,), fetch=True)
        szczegoly = f"ID:{id_poz} ({info[0]['typ']} {info[0]['opis']})" if info else f"ID:{id_poz}"
        
        self._execute("DELETE FROM sciernice WHERE id=?", (id_poz,))
        self._zapisz_log("USUNIĘTO", szczegoly)

    def _zapisz_log(self, akcja, szczegoly):
        """Zapis do pliku TXT."""
        teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{teraz}] {akcja.upper()}: {szczegoly}\n")
        except Exception as e:
            print(f"Log Error: {e}")

    def pobierz_unikalne_wartosci(self, kolumna):
        """Dla potrzeb filtrów popup."""
        res = self._execute(f"SELECT DISTINCT {kolumna} FROM sciernice WHERE {kolumna} != ''", fetch=True)
        return sorted([str(r[kolumna]) for r in res])

    @property
    def lista_typow(self):
        return list(self.dane["konfiguracja"].get("typy_ustawienia", {}).keys())