import customtkinter as ctk
from tkinter import messagebox  # Import niezbędny do obsługi okien dialogowych[cite: 4]
from gui_components import EditWindow

# Konfiguracja wyglądu interfejsu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.1)

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected_id = None

        # --- USTAWIENIA OKNA ---
        self.window_width = 1450
        self.window_height = 850
        screen_width = self.winfo_screenwidth()
        pos_x = int((screen_width - self.window_width) / 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{pos_x}+50")
        self.title("System Zarządzania Ściernicami v4.5 (SQL + Config JSON)")

        # Mapowanie kolorów dla statusów wizualnych
        self.color_map = {
            "W uzyciu": "#90EE90",
            "magazyn": "#FFFFFF",
            "zamowiona": "#3498db",
            "zlom": "#e74c3c"
        }
        
        self.font_header = ("Arial", 13, "bold")
        self.font_row = ("Arial", 13)
        self.font_ui = ("Arial", 14)

        # Szerokości kolumn w tabeli
        self.col_widths = {
            "typ": 100, 
            "kat": 120, 
            "opis": 300, 
            "ziarno": 100, 
            "producent": 170, 
            "statusy": 500
        }

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.sprawdz_polaczenie()

    def sprawdz_polaczenie(self):
        """Weryfikuje połączenie z bazą danych[cite: 2, 4]."""
        for w in self.container.winfo_children(): w.destroy()
        if self.db.polacz():
            self.setup_ui_pelny()
        else:
            self.setup_ui_error()

    def setup_ui_error(self):
        """Ekran błędu w przypadku problemów z siecią/bazą[cite: 4]."""
        f = ctk.CTkFrame(self.container)
        f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="⚠️", font=("Arial", 70)).pack(pady=10)
        ctk.CTkLabel(f, text="BRAK POŁĄCZENIA Z BAZĄ DANYCH", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=10, padx=50)
        ctk.CTkButton(f, text="ODŚWIEŻ", command=self.sprawdz_polaczenie).pack(pady=25)

    def setup_ui_pelny(self):
        """Buduje główny interfejs programu[cite: 4]."""
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # --- PANEL GÓRNY: WYSZUKIWARKA ---
        self.frame_top = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.odswiez_tabele())
        
        self.e_search = ctk.CTkEntry(
            self.frame_top, 
            placeholder_text="🔍 Szukaj po typie, opisie lub producencie...",
            textvariable=self.search_var,
            width=500, height=40
        )
        self.e_search.pack(side="left")

        # --- PANEL ŚRODKOWY: TABELA ---
        self.frame_tabela = ctk.CTkFrame(self.container)
        self.frame_tabela.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        
        self.h_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=10, pady=10)
        
        headers = [("typ", "TYP"), ("kat", "PARAMETR"), ("opis", "OPIS"), ("ziarno", "ZIARNO"), ("producent", "PRODUCENT"), ("statusy", "STATUSY")]
        for key, text in headers:
            ctk.CTkLabel(self.h_frame, text=text, width=self.col_widths[key], anchor="w", font=self.font_header).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- PANEL DOLNY: FORMULARZ I PRZYCISKI ---
        self.p_form = ctk.CTkFrame(self.container)
        self.p_form.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        # Pobieranie konfiguracji z bazy (obsługa nowej struktury JSON)[cite: 5]
        conf = self.db.dane["konfiguracja"]
        lista_typow = list(conf.get("typy_ustawienia", {}).keys())

        self.c_typ = ctk.CTkComboBox(self.p_form, values=lista_typow, width=100, height=40)
        self.c_typ.pack(side="left", padx=3)
        
        self.e_param = ctk.CTkEntry(self.p_form, placeholder_text="Parametr", width=100, height=40)
        self.e_param.pack(side="left", padx=3)
        
        self.e_opis = ctk.CTkEntry(self.p_form, placeholder_text="Opis", width=280, height=40)
        self.e_opis.pack(side="left", padx=3)
        
        self.e_ziarno = ctk.CTkEntry(self.p_form, placeholder_text="Ziarno", width=100, height=40)
        self.e_ziarno.pack(side="left", padx=3)
        
        self.c_prod = ctk.CTkComboBox(self.p_form, values=conf.get("producenci", []), width=170, height=40)
        self.c_prod.pack(side="left", padx=3)
        
        self.e_il = ctk.CTkEntry(self.p_form, placeholder_text="Szt.", width=70, height=40)
        self.e_il.pack(side="left", padx=3)

        # Przyciski akcji
        self.btn_add = ctk.CTkButton(
            self.p_form, text="DODAJ", fg_color="#2ecc71", 
            width=120, height=40, font=self.font_header, command=self.handle_add
        )
        self.btn_add.pack(side="left", padx=15)

        self.btn_del = ctk.CTkButton(
            self.p_form, text="USUŃ", state="disabled", 
            fg_color="#c0392b", hover_color="#e74c3c", 
            width=100, height=40, font=self.font_header, command=self.confirm_delete_main
        )
        self.btn_del.pack(side="right", padx=5)

        self.btn_ed = ctk.CTkButton(
            self.p_form, text="EDYTUJ WYBRANĄ", state="disabled", 
            fg_color="#3498db", width=150, height=40, font=self.font_header, command=self.open_edit
        )
        self.btn_ed.pack(side="right", padx=5)

        self.odswiez_tabele()

    def odswiez_tabele(self):
        """Odświeża widok danych z uwzględnieniem wyszukiwarki[cite: 2, 4]."""
        for w in self.scroll.winfo_children(): w.destroy()
        
        fraza = self.search_var.get()
        dane = self.db.pobierz_dane(fraza)
        
        ustawienia = self.db.dane["konfiguracja"].get("typy_ustawienia", {})

        for s in dane:
            is_selected = (self.selected_id == s["id"])
            bg = "#1f538d" if is_selected else "#2b2b2b"
            
            f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4)
            f.pack(fill="x", pady=2, padx=2)
            f.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
            
            # Pobieranie prefixu/suffixu dla parametru z JSON[cite: 5]
            konfig = ustawienia.get(s["typ"], {})
            pre = konfig.get("prefix", "")
            suf = konfig.get("suffix", "")
            wyswietlany_param = f"{pre}{s['kat']}{suf}"

            pola = [
                ("typ", s["typ"]), 
                ("kat", wyswietlany_param), 
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
            stat_frame.pack(side="left", padx=5)
            for st, il in s["ilosc"].items():
                if il > 0:
                    lbl = ctk.CTkLabel(
                        stat_frame, text=f"{st.upper()}: {il}", 
                        text_color=self.color_map.get(st, "#FFF"), font=("Arial", 11, "bold")
                    )
                    lbl.pack(side="left", padx=10)
                    lbl.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

    def select_item(self, cid):
        """Obsługa zaznaczenia wiersza w tabeli[cite: 4]."""
        self.selected_id = cid
        self.btn_ed.configure(state="normal")
        self.btn_del.configure(state="normal")
        self.odswiez_tabele()

    def handle_add(self):
        """Dodaje nową pozycję do bazy SQL[cite: 2, 4]."""
        try:
            il = int(self.e_il.get()) if self.e_il.get() else 0
            self.db.dodaj_sciernice(
                self.c_typ.get(), self.e_param.get(), 
                self.e_opis.get(), self.e_ziarno.get(), 
                self.c_prod.get(), il
            )
            # Czyszczenie pól po sukcesie
            self.e_opis.delete(0, 'end')
            self.e_param.delete(0, 'end')
            self.e_il.delete(0, 'end')
            self.odswiez_tabele()
        except ValueError:
            messagebox.showerror("Błąd", "Ilość musi być liczbą całkowitą!", parent=self)

    def confirm_delete_main(self):
        """Usuwa pozycję z bazy z potwierdzeniem[cite: 2, 4]."""
        if self.selected_id:
            wszystkie = self.db.pobierz_dane("")
            item = next((s for s in wszystkie if s["id"] == self.selected_id), None)
            if item:
                suma = sum(item["ilosc"].values())
                msg = f"Czy usunąć ściernicę ID {self.selected_id}?"
                if suma > 0: 
                    msg += f"\n\nUWAGA: Na stanie znajduje się {suma} sztuk!"
                
                # parent=self gwarantuje, że popup nie schowa się pod oknem[cite: 3, 4]
                if messagebox.askyesno("Potwierdzenie usunięcia", msg, parent=self):
                    self.db.usun_pozycje(self.selected_id)
                    self.selected_id = None
                    self.btn_ed.configure(state="disabled")
                    self.btn_del.configure(state="disabled")
                    self.odswiez_tabele()

    def open_edit(self):
        """Otwiera okno edycji wybranej pozycji[cite: 3, 4]."""
        if self.selected_id:
            wszystkie = self.db.pobierz_dane("")
            item = next((s for s in wszystkie if s["id"] == self.selected_id), None)
            if item:
                EditWindow(self, self.db, item, self.odswiez_tabele)