import customtkinter as ctk
import json
import os

# Konfiguracja wyglądu
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

DB_FILE = "magazyn.json"

class MagazynApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pomocnik Magazyniera - Tarcze Ścierne")
        self.geometry("1100x750")

        # --- DEFINICJA PROPORCJI SZEROKOŚCI ---
        # Baza (Opis) = 300
        # 1/3 z 300 = 100 (Typ, Ziarno)
        # 2/3 z 300 = 200 (Producent, Status)
        self.col_widths = {
            "typ": 100,
            "opis": 300,
            "ziarno": 100,
            "producent": 200,
            "status": 200
        }

        self.dane = self.wczytaj_baze()
        self.sort_reverse = False

        # Układ okna
        self.grid_rowconfigure(0, weight=1)  # Tabela
        self.grid_rowconfigure(1, weight=0)  # Formularz
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui_tabela()
        self.setup_ui_formularz()
        self.odswiez_widok_tabeli()

    def wczytaj_baze(self):
        """Wczytuje JSON lub tworzy plik startowy z Twoimi parametrami."""
        if not os.path.exists(DB_FILE):
            default_data = {
                "konfiguracja": {
                    "typy": ["1A1", "1V1", "11V9"],
                    "producenci": ["Tyrolit", "Toolgal", "DrMuller"],
                    "statusy": ["W uzyciu", "magazyn", "zamowiona", "złom"]
                },
                "sciernice": [
                    {
                        "id": 1,
                        "typ": "1A1",
                        "opis": "125x10x32",
                        "ziarno": "B107",
                        "producent": "Tyrolit",
                        "status": "magazyn"
                    }
                ]
            }
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)
            return default_data
        
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def zapisz_baze(self):
        """Zapisuje dane do pliku."""
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.dane, f, indent=4)

    def setup_ui_tabela(self):
        """Tworzy sekcję wyświetlania danych."""
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        # Nagłówki
        self.header_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        kolumny = ["typ", "opis", "ziarno", "producent", "status"]
        for h in kolumny:
            btn = ctk.CTkButton(
                self.header_frame, 
                text=h.upper(), 
                width=self.col_widths[h],
                corner_radius=0,
                command=lambda k=h: self.sortuj_tabelę(k)
            )
            btn.pack(side="left", padx=2)

        # Obszar z paskiem przewijania
        self.scroll_frame = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_ui_formularz(self):
        """Tworzy dolny panel dodawania ściernic."""
        self.frame_form = ctk.CTkFrame(self)
        self.frame_form.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

        konfig = self.dane["konfiguracja"]

        # Pola dopasowane szerokością do kolumn powyżej
        self.combo_typ = ctk.CTkComboBox(self.frame_form, values=konfig["typy"], width=self.col_widths["typ"])
        self.combo_typ.pack(side="left", padx=2, pady=10)

        self.entry_opis = ctk.CTkEntry(self.frame_form, placeholder_text="Opis", width=self.col_widths["opis"])
        self.entry_opis.pack(side="left", padx=2, pady=10)

        self.entry_ziarno = ctk.CTkEntry(self.frame_form, placeholder_text="Ziarno", width=self.col_widths["ziarno"])
        self.entry_ziarno.pack(side="left", padx=2, pady=10)

        self.combo_prod = ctk.CTkComboBox(self.frame_form, values=konfig["producenci"], width=self.col_widths["producent"])
        self.combo_prod.pack(side="left", padx=2, pady=10)

        self.combo_stat = ctk.CTkComboBox(self.frame_form, values=konfig["statusy"], width=self.col_widths["status"])
        self.combo_stat.pack(side="left", padx=2, pady=10)

        self.btn_dodaj = ctk.CTkButton(self.frame_form, text="DODAJ", fg_color="#2ecc71", hover_color="#27ae60", 
                                     width=80, command=self.dodaj_sciernice)
        self.btn_dodaj.pack(side="left", padx=10, pady=10)

    def odswiez_widok_tabeli(self):
        """Przerysowuje wiersze w tabeli."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for i, s in enumerate(self.dane["sciernice"]):
            # Efekt "zebry" (naprzemienne kolory tła)
            bg_color = "#2b2b2b" if i % 2 == 0 else "#333333"
            
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, corner_radius=0)
            row_frame.pack(fill="x", pady=1)

            # Wyświetlanie danych zgodnie z szerokościami
            ctk.CTkLabel(row_frame, text=s["typ"], width=self.col_widths["typ"]).pack(side="left", padx=2)
            ctk.CTkLabel(row_frame, text=s["opis"], width=self.col_widths["opis"], anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(row_frame, text=s["ziarno"], width=self.col_widths["ziarno"]).pack(side="left", padx=2)
            ctk.CTkLabel(row_frame, text=s["producent"], width=self.col_widths["producent"]).pack(side="left", padx=2)
            ctk.CTkLabel(row_frame, text=s["status"], width=self.col_widths["status"]).pack(side="left", padx=2)

    def sortuj_tabelę(self, klucz):
        """Sortuje dane i odświeża widok."""
        self.sort_reverse = not self.sort_reverse
        self.dane["sciernice"].sort(key=lambda x: str(x[klucz]).lower(), reverse=self.sort_reverse)
        self.odswiez_widok_tabeli()

    def dodaj_sciernice(self):
        """Pobiera dane z pól i zapisuje nową pozycję."""
        if not self.entry_opis.get(): # Małe zabezpieczenie
            return

        nowa = {
            "id": len(self.dane["sciernice"]) + 1,
            "typ": self.combo_typ.get(),
            "opis": self.entry_opis.get(),
            "ziarno": self.entry_ziarno.get(),
            "producent": self.combo_prod.get(),
            "status": self.combo_stat.get()
        }
        
        self.dane["sciernice"].append(nowa)
        self.zapisz_baze()
        self.odswiez_widok_tabeli()
        
        # Czyszczenie pól po dodaniu
        self.entry_opis.delete(0, 'end')
        self.entry_ziarno.delete(0, 'end')

if __name__ == "__main__":
    app = MagazynApp()
    app.mainloop()