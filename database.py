import sqlite3
import os
import json
from datetime import datetime 

class InventoryDB:
    def __init__(self, db_path, config_path,log_path):
        self.db_path = db_path
        self.config_path = config_path
        self.log_path = log_path
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

    def pobierz_dane(self, filtr="", aktywne_filtry=None, filter_order=None):
        """Pobiera dane z dynamicznym sortowaniem zależnym od kolejności filtrów[cite: 8]."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT * FROM sciernice WHERE (opis LIKE ? OR kat LIKE ?)"
        f = f"%{filtr}%"
        params = [f, f]
        
        if aktywne_filtry:
            for col, values in aktywne_filtry.items():
                if values:
                    placeholders = ", ".join(["?"] * len(values))
                    query += f" AND {col} IN ({placeholders})"
                    params.extend(values)
        
        # BUDOWANIE DYNAMICZNEGO SORTOWANIA[cite: 8]
        order_clauses = []
        
        # Jeśli użytkownik klikał filtry, użyj jego kolejności:
        if filter_order:
            for col in filter_order:
                order_clauses.append(f"{col} ASC")
        
        # Dodaj domyślne sortowanie na końcu dla pozostałych pól:
        domyslne = ["typ", "ziarno", "producent", "opis"]
        for d in domyslne:
            if f"{d} ASC" not in order_clauses:
                order_clauses.append(f"{d} ASC")
        
        query += " ORDER BY " + ", ".join(order_clauses)
        
        cur.execute(query, params)
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
        """
        Dodaje nową ściernicę do bazy i tworzy wpis w logu.
        """
        # Standaryzacja danych (zamiana przecinków na kropki dla obliczeń)
        ziarno_std = str(ziarno).upper()
        kat_std = str(kat).replace(',', '.')
        opis_std = str(opis).replace(',', '.')

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Wstawienie rekordu do tabeli
        cur.execute("""
            INSERT INTO sciernice (typ, kat, opis, ziarno, producent, magazyn)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (typ, kat_std, opis_std, ziarno_std, producent, ilosc_start))
        
        # Pobieramy ID, które baza nadała automatycznie[cite: 2]
        nowe_id = cur.lastrowid
        
        conn.commit()
        conn.close()

        # Dokumentacja w pliku log.txt
        info = f"ID:{nowe_id} | Typ:{typ} | Opis:{opis_std} | Ilość:{ilosc_start}"
        self._zapisz_log("DODANO", info)

    def aktualizuj_pozycje(self, id_pozycji, nowe_dane):
        """
        Aktualizuje dane w bazie i rejestruje szczegółowe różnice w pliku log.txt.
        """
        # 1. Pobieramy stare dane, aby wiedzieć co się zmienia
        stare_dane = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM sciernice WHERE id=?", (id_pozycji,))
            stare_dane = cur.fetchone()
            conn.close()
        except Exception as e:
            print(f"Błąd podczas odczytu danych przed aktualizacją: {e}")
            return

        if not stare_dane:
            return

        # 2. Przygotowujemy listę zmian
        zmiany = []
        
        # Sprawdzamy pola tekstowe
        nowy_opis = str(nowe_dane["opis"]).replace(',', '.')
        nowy_param = str(nowe_dane["kat"]).replace(',', '.')
        
        if stare_dane["opis"] != nowy_opis:
            zmiany.append(f"Opis: '{stare_dane['opis']}' -> '{nowy_opis}'")
        
        if stare_dane["kat"] != nowy_param:
            zmiany.append(f"Parametr: '{stare_dane['kat']}' -> '{nowy_param}'")

        # Sprawdzamy stany magazynowe (ilości)[cite: 3]
        mapowanie_stanow = {
            "magazyn": nowe_dane["ilosc"].get("magazyn", 0),
            "uzycie": nowe_dane["ilosc"].get("W uzyciu", 0),
            "zamowiona": nowe_dane["ilosc"].get("zamowiona", 0),
            "zlom": nowe_dane["ilosc"].get("zlom", 0)
        }

        for klucz, nowa_wartosc in mapowanie_stanow.items():
            stara_wartosc = stare_dane[klucz]
            if int(stara_wartosc) != int(nowa_wartosc):
                zmiany.append(f"{klucz}: {stara_wartosc} -> {nowa_wartosc}")

        # 3. Jeśli są zmiany, zapisujemy je do logu
        if zmiany:
            szczegoly_logu = f"ID:{id_pozycji} | " + ", ".join(zmiany)
            self._zapisz_log("AKTUALIZACJA", szczegoly_logu)

        # 4. Wykonujemy faktyczny zapis w bazie SQL[cite: 2]
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                UPDATE sciernice 
                SET opis=?, kat=?, magazyn=?, uzycie=?, zamowiona=?, zlom=?
                WHERE id=?
            """, (
                nowy_opis, nowy_param, 
                mapowanie_stanow["magazyn"],
                mapowanie_stanow["uzycie"],
                mapowanie_stanow["zamowiona"],
                mapowanie_stanow["zlom"],
                id_pozycji
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Błąd podczas zapisu do bazy danych: {e}")

    def usun_pozycje(self, id_pozycji):
        """
        Usuwa ściernicę o podanym ID. Najpierw sprawdza jej dane, aby zapisać je w logu.
        """
        # 1. KROK EDUKACYJNY: Musimy najpierw pobrać dane, bo po usunięciu ich nie odzyskamy[cite: 2]
        opis_do_logu = f"ID:{id_pozycji}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row # Pozwala na dostęp do kolumn po nazwach[cite: 2]
            cur = conn.cursor()
            
            # Pobieramy szczegóły usuwanego przedmiotu
            cur.execute("SELECT typ, opis FROM sciernice WHERE id=?", (id_pozycji,))
            row = cur.fetchone()
            
            if row:
                opis_elementu = f"{row['typ']} {row['opis']}"
                opis_do_logu = f"ID:{id_pozycji} ({opis_elementu})"

            # 2. Usuwamy właściwy rekord[cite: 2]
            cur.execute("DELETE FROM sciernice WHERE id=?", (id_pozycji,))
            
            conn.commit()
            conn.close()
            
            # Zapisujemy informację o usunięciu do logu
            self._zapisz_log("USUNIĘTO", opis_do_logu)
            
        except Exception as e:
            print(f"Błąd podczas usuwania pozycji: {e}")

    def _zapisz_log(self, akcja, szczegoly):
        """Prywatna metoda dopisująca linię do pliku log.txt."""
        teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linia = f"[{teraz}] {akcja.upper()}: {szczegoly}\n"
        
        try:
            # Używamy kodowania utf-8, aby polskie znaki wyświetlały się poprawnie
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(linia)
        except Exception as e:
            print(f"Błąd zapisu do logu: {e}")
    
    def pobierz_unikalne_wartosci(self, kolumna):
        """Pobiera unikalne wartości dla danej kolumny do listy filtrów."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            query = f"SELECT DISTINCT {kolumna} FROM sciernice WHERE {kolumna} IS NOT NULL AND {kolumna} != ''"
            cur.execute(query)
            return sorted([str(r[0]) for r in cur.fetchall()])

    @property
    def lista_typow(self):
        """Zwraca klucze typów z konfiguracji[cite: 6]."""
        return list(self.dane["konfiguracja"].get("typy_ustawienia", {}).keys())