import customtkinter as ctk
from tkinter import messagebox
from gui_components import EditWindow

# Konfiguracja wyglądu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.1)

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected_id = None

        # --- 1. USTAWIENIA OKNA ---
        self.window_width = 1450
        self.window_height = 850
        screen_width = self.winfo_screenwidth()
        pos_x = int((screen_width - self.window_width) / 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{pos_x}+50")
        self.title("System Zarządzania Ściernicami v4.0 (SQL + Search)")

        # --- 2. KONFIGURACJA WIZUALNA ---
        self.color_map = {
            "W uzyciu": "#90EE90",  # Zielony
            "magazyn": "#FFFFFF",   # Biały
            "zamowiona": "#3498db", # Niebieski
            "zlom": "#e74c3c"       # Czerwony
        }
        
        self.font_header = ("Arial", 13, "bold")
        self.font_row = ("Arial", 13)
        self.font_ui = ("Arial", 14)

        # Szerokości kolumn (zoptymalizowane pod nowy parametr)
        self.col_widths = {
            "typ": 100, 
            "kat": 120,    # Nazwa klucza 'kat' zostaje, ale nagłówek to 'PARAMETR'
            "opis": 300, 
            "ziarno": 100, 
            "producent": 170, 
            "statusy": 500
        }

        # Kontener główny
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # --- 3. INICJALIZACJA ---
        self.sprawdz_polaczenie()

    def sprawdz_polaczenie(self):
        """Weryfikuje czy baza danych na dysku sieciowym jest dostępna."""
        for w in self.container.winfo_children(): w.destroy()
        if self.db.polacz():
            self.setup_ui_pelny()
        else:
            self.setup_ui_error()

    def setup_ui_error(self):
        """Ekran błędu w przypadku braku dostępu do dysku/bazy."""
        f = ctk.CTkFrame(self.container)
        f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="⚠️", font=("Arial", 70)).pack(pady=10)
        ctk.CTkLabel(f, text="BRAK POŁĄCZENIA Z BAZĄ DANYCH", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=10, padx=50)
        ctk.CTkLabel(f, text=f"Lokalizacja: {self.db.db_path}", font=("Arial", 12)).pack(pady=5)
        ctk.CTkButton(f, text="SPRÓBUJ PONOWNIE", height=45, command=self.sprawdz_polaczenie).pack(pady=25)

    def setup_ui_pelny(self):
        """Buduje główny interfejs użytkownika."""
        self.container.grid_rowconfigure(1, weight=1)  # Tabela zajmuje resztę miejsca
        self.container.grid_columnconfigure(0, weight=1)

        # --- PANEL GÓRNY: WYSZUKIWARKA ---
        self.frame_top = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.odswiez_tabele())
        
        self.e_search = ctk.CTkEntry(
            self.frame_top, 
            placeholder_text="🔍 Wyszukaj ściernicę (typ, opis lub producent)...",
            textvariable=self.search_var,
            width=500,
            height=40,
            font=self.font_ui
        )
        self.e_search.pack(side="left")

        # --- PANEL ŚRODKOWY: TABELA ---
        self.frame_tabela = ctk.CTkFrame(self.container)
        self.frame_tabela.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        
        # Nagłówki
        self.h_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=10, pady=10)
        
        headers = [
            ("typ", "TYP"), 
            ("kat", "PARAMETR"), 
            ("opis", "OPIS (WYMIARY)"), 
            ("ziarno", "ZIARNO"), 
            ("producent", "PRODUCENT"), 
            ("statusy", "STATUSY / STANY")
        ]

        for key, text in headers:
            ctk.CTkLabel(self.h_frame, text=text, width=self.col_widths[key], anchor="w", font=self.font_header).pack(side="left", padx=5)

        # Obszar przewijany danych
        self.scroll = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- PANEL DOLNY: FORMULARZ DODAWANIA ---
        self.p_form = ctk.CTkFrame(self.container)
        self.p_form.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        conf = self.db.dane["konfiguracja"]

        self.c_typ = ctk.CTkComboBox(self.p_form, values=conf["typy"], width=100, height=40)
        self.c_typ.pack(side="left", padx=3)
        
        self.e_param = ctk.CTkEntry(self.p_form, placeholder_text="Parametr", width=100, height=40)
        self.e_param.pack(side="left", padx=3)
        
        self.e_opis = ctk.CTkEntry(self.p_form, placeholder_text="Opis wymiarowy", width=280, height=40)
        self.e_opis.pack(side="left", padx=3)
        
        self.e_ziarno = ctk.CTkEntry(self.p_form, placeholder_text="Ziarno", width=100, height=40)
        self.e_ziarno.pack(side="left", padx=3)
        
        self.c_prod = ctk.CTkComboBox(self.p_form, values=conf["producenci"], width=170, height=40)
        self.c_prod.pack(side="left", padx=3)
        
        self.e_il = ctk.CTkEntry(self.p_form, placeholder_text="Szt.", width=70, height=40)
        self.e_il.pack(side="left", padx=3)

        self.btn_add = ctk.CTkButton(
            self.p_form, 
            text="DODAJ DO BAZY", 
            fg_color="#2ecc71", 
            hover_color="#27ae60",
            width=140, 
            height=40, 
            font=self.font_header, 
            command=self.handle_add
        )
        self.btn_add.pack(side="left", padx=15)
        
        # Przycisk USUŃ (Dodany po prawej jako pierwszy od krawędzi)
        self.btn_del = ctk.CTkButton(
            self.p_form, 
            text="USUŃ", 
            state="disabled", 
            fg_color="#c0392b", 
            hover_color="#e74c3c",
            width=100, 
            height=40,           # Dodano wysokość dla spójności
            font=self.font_header, # Dodano czcionkę
            command=self.confirm_delete_main
        )
        self.btn_del.pack(side="right", padx=5)

        # Przycisk EDYTUJ (Dodany po prawej jako drugi od krawędzi)
        self.btn_ed = ctk.CTkButton(
            self.p_form, 
            text="EDYTUJ WYBRANĄ", 
            fg_color="#3498db", 
            state="disabled", 
            width=150, 
            height=40,           # Dodano wysokość dla spójności
            font=self.font_header, 
            command=self.open_edit
        )
        self.btn_ed.pack(side="right", padx=5)

        # Inicjalizacja tabeli
        self.odswiez_tabele()

    def odswiez_tabele(self):
        """Pobiera przefiltrowane dane z bazy SQL i rysuje wiersze."""
        for w in self.scroll.winfo_children(): w.destroy()
        
        fraza = self.search_var.get()
        dane = self.db.pobierz_dane(fraza)
        
        for s in dane:
            is_selected = (self.selected_id == s["id"])
            bg = "#1f538d" if is_selected else "#2b2b2b"
            
            f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4)
            f.pack(fill="x", pady=2, padx=2)
            
            # Reakcja na kliknięcie wiersza
            f.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
            
            # Pola tekstowe w wierszu
            pola = [
                ("typ", s["typ"]), 
                ("kat", s["kat"]), 
                ("opis", s["opis"]), 
                ("ziarno", s["ziarno"]), 
                ("producent", s["producent"])
            ]
            
            for key, val in pola:
                l = ctk.CTkLabel(f, text=str(val), width=self.col_widths[key], anchor="w", font=self.font_row)
                l.pack(side="left", padx=5, pady=8)
                l.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

            # Renderowanie stanów ilościowych
            stat_frame = ctk.CTkFrame(f, fg_color="transparent")
            stat_frame.pack(side="left", padx=5, fill="y")
            
            for st, il in s["ilosc"].items():
                if il > 0:
                    lbl = ctk.CTkLabel(
                        stat_frame, 
                        text=f"{st.upper()}: {il}", 
                        text_color=self.color_map.get(st, "#FFF"), 
                        font=("Arial", 11, "bold")
                    )
                    lbl.pack(side="left", padx=10)
                    lbl.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

    def select_item(self, cid):
        """Aktywacja przycisków po kliknięciu wiersza."""
        self.selected_id = cid
        self.btn_ed.configure(state="normal")
        self.btn_del.configure(state="normal") # Aktywujemy przycisk usuwania
        self.odswiez_tabele()

    def handle_add(self):
        """Pobiera dane z formularza i wysyła do bazy SQL."""
        try:
            ilosc = int(self.e_il.get()) if self.e_il.get() else 0
            self.db.dodaj_sciernice(
                self.c_typ.get(), 
                self.e_param.get(), 
                self.e_opis.get(), 
                self.e_ziarno.get(), 
                self.c_prod.get(), 
                ilosc
            )
            # Czyszczenie pól po dodaniu
            self.e_opis.delete(0, 'end')
            self.e_param.delete(0, 'end')
            self.e_il.delete(0, 'end')
            self.odswiez_tabele()
        except ValueError:
            pass # Można dodać popup z błędem "Ilość musi być liczbą"

    def open_edit(self):
        """Otwiera okno edycji dla zaznaczonego ID."""
        if self.selected_id:
            # Pobieramy najświeższe dane o tym konkretnym elemencie
            wszystkie = self.db.pobierz_dane("")
            item = next((s for s in wszystkie if s["id"] == self.selected_id), None)
            if item:
                EditWindow(self, self.db, item, self.odswiez_tabele)

    def confirm_delete_main(self):
        if self.selected_id:
            # Pobieramy dane wybranej ściernicy, aby sprawdzić stan
            wszystkie = self.db.pobierz_dane("")
            item = next((s for s in wszystkie if s["id"] == self.selected_id), None)
            
            if item:
                suma_sztuk = sum(item["ilosc"].values())
                msg = f"Czy na pewno usunąć ściernicę ID: {self.selected_id} ({item['typ']} {item['opis']})?"
                if suma_sztuk > 0:
                    msg += f"\n\nUWAGA! Na stanie jest jeszcze {suma_sztuk} sztuk!"

                # parent=self gwarantuje, że popup będzie na wierzchu głównego okna
                if messagebox.askyesno("Potwierdzenie usunięcia", msg, parent=self):
                    self.db.usun_pozycje(self.selected_id)
                    self.selected_id = None
                    self.btn_ed.configure(state="disabled")
                    self.btn_del.configure(state="disabled")
                    self.odswiez_tabele()