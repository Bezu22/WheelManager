import customtkinter as ctk
from tkinter import messagebox
from gui_components import EditWindow

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected_id = None
        self._filter_popup = None
        self.widzety_wierszy = {}
        self._ostatnia_fraza = ""
        self.active_filters = {
            "typ": [],
            "ziarno": [],
            "producent": []
        }
        self.filter_order = [] # do śledzenia kolejności kliknięć

        self.window_width, self.window_height = 1450, 850
        pos_x = int((self.winfo_screenwidth() - self.window_width) / 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{pos_x}+50")
        self.title("System Zarządzania Ściernicami v5.0")

        self.color_map = {"W uzyciu": "#90EE90", "magazyn": "#FFFFFF", "zamowiona": "#3498db", "zlom": "#e74c3c"}
        self.font_header = ("Arial", 13, "bold")
        self.font_row = ("Arial", 13)
        self.col_widths = {"typ": 100, "kat": 120, "opis": 300, "ziarno": 100, "producent": 170, "statusy": 500}

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.sprawdz_polaczenie()

    def sprawdz_polaczenie(self):
        for w in self.container.winfo_children(): w.destroy()
        if self.db.polacz(): self.setup_ui_pelny()
        else: self.setup_ui_error()

    def setup_ui_pelny(self):
        """Buduje pełny interfejs z interaktywnymi nagłówkami filtrów."""
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # 1. Searchbar (tylko Opis i Parametr)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.odswiez_tabele(pelne=True))
        self.e_search = ctk.CTkEntry(self.container, 
                                     placeholder_text="🔍 Szukaj w opisie lub parametrach...", 
                                     textvariable=self.search_var, width=500, height=40)
        self.e_search.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # 2. Tabela i Nagłówki
        self.frame_tabela = ctk.CTkFrame(self.container)
        self.frame_tabela.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        
        # Nagłówki z obsługą kliknięcia (Filtry)
        self.h_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=10, pady=10)
        
        # Definicja nagłówków: (klucz_db, nazwa_wyswietlana, czy_filtrowalna)
        self.header_labels = {}
        headers = [
            ("typ", "TYP ▾", True), 
            ("kat", "PARAMETR", False), 
            ("opis", "OPIS", False), 
            ("ziarno", "ZIARNO ▾", True), 
            ("producent", "PRODUCENT ▾", True),
            ("statusy", "STATUSY", False)
        ]

        for k, text, filtrowalna in headers:
            lbl = ctk.CTkLabel(self.h_frame, text=text, width=self.col_widths[k], 
                               anchor="w", font=self.font_header)
            lbl.pack(side="left", padx=5)
            self.header_labels[k] = lbl
            
            if filtrowalna:
                lbl.configure(cursor="hand2")
                # Bindujemy kliknięcie do otwarcia Twojego okna popup
                lbl.bind("<Button-1>", lambda e, col=k, name=text: self.show_popup_filter(col, name))

        # 3. Obszar przewijany danych
        self.scroll = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 4. Formularz dodawania (Dolny panel)
        self.p_form = ctk.CTkFrame(self.container)
        self.p_form.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        conf = self.db.dane["konfiguracja"]
        self.c_typ = ctk.CTkComboBox(self.p_form, values=self.db.lista_typow, width=120, height=40)
        self.c_typ.pack(side="left", padx=3)
        self.e_param = ctk.CTkEntry(self.p_form, placeholder_text="Parametr", width=100, height=40)
        self.e_param.pack(side="left", padx=3)
        self.e_opis = ctk.CTkEntry(self.p_form, placeholder_text="Opis wymiarowy", width=280, height=40)
        self.e_opis.pack(side="left", padx=3)
        self.e_ziarno = ctk.CTkEntry(self.p_form, placeholder_text="Ziarno", width=100, height=40)
        self.e_ziarno.pack(side="left", padx=3)
        self.c_prod = ctk.CTkComboBox(self.p_form, values=conf.get("producenci", []), width=170, height=40)
        self.c_prod.pack(side="left", padx=3)
        self.e_il = ctk.CTkEntry(self.p_form, placeholder_text="Szt.", width=70, height=40)
        self.e_il.pack(side="left", padx=3)

        # Przyciski akcji
        self.btn_add = ctk.CTkButton(self.p_form, text="DODAJ", fg_color="#2ecc71", 
                                     width=120, height=40, font=self.font_header, command=self.handle_add)
        self.btn_add.pack(side="left", padx=15)
        
        self.btn_del = ctk.CTkButton(self.p_form, text="USUŃ", state="disabled", 
                                     fg_color="#c0392b", width=100, height=40, font=self.font_header, 
                                     command=self.confirm_delete_main)
        self.btn_del.pack(side="right", padx=5)
        
        self.btn_ed = ctk.CTkButton(self.p_form, text="EDYTUJ", state="disabled", 
                                    fg_color="#3498db", width=120, height=40, font=self.font_header, 
                                    command=self.open_edit)
        self.btn_ed.pack(side="right", padx=5)

        self.odswiez_tabele(pelne=True)

    def odswiez_tabele(self, pelne=False):
        """Zoptymalizowane odświeżanie z obsługą filtrów kolumnowych."""
        fraza = self.search_var.get()
        
        # Tworzymy unikalny klucz na podstawie frazy i wybranych filtrów
        # To wymusi odświeżenie, gdy zmienisz checkboxy w popupie
        stan_filtrow = f"{fraza}_{str(self.active_filters)}"
        
        if pelne or stan_filtrow != self._ostatnia_fraza:
            self._ostatnia_fraza = stan_filtrow
            
            # Czyszczenie widżetów
            for w in self.scroll.winfo_children(): 
                w.destroy()
            self.widzety_wierszy = {}
            
            # POBIERANIE DANYCH
            dane = self.db.pobierz_dane(fraza, self.active_filters, self.filter_order)
            
            ustawienia = self.db.dane["konfiguracja"].get("typy_ustawienia", {})

            for s in dane:
                bg = "#1f538d" if self.selected_id == s["id"] else "#2b2b2b"
                f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4)
                f.pack(fill="x", pady=2, padx=2)
                self.widzety_wierszy[s["id"]] = f
                f.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
                
                konfig = ustawienia.get(s["typ"], {})
                wyswietlany_param = f"{konfig.get('prefix','')}{s['kat']}{konfig.get('suffix','')}"

                pola = [("typ", s["typ"]), ("kat", wyswietlany_param), ("opis", s["opis"]), ("ziarno", s["ziarno"]), ("producent", s["producent"])]
                for k, val in pola:
                    l = ctk.CTkLabel(f, text=str(val), width=self.col_widths[k], anchor="w", font=self.font_row)
                    l.pack(side="left", padx=5, pady=8)
                    l.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

                stat_frame = ctk.CTkFrame(f, fg_color="transparent")
                stat_frame.pack(side="left", padx=5)
                for st, il in s["ilosc"].items():
                    if il > 0:
                        lbl = ctk.CTkLabel(stat_frame, text=f"{st.upper()}: {il}", text_color=self.color_map.get(st, "#FFF"), font=("Arial", 11, "bold"))
                        lbl.pack(side="left", padx=10)
                        lbl.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
        else:
            # Szybka aktualizacja tylko kolorów ramek (bez niszczenia widżetów)
            for cid, frame in self.widzety_wierszy.items():
                nowy_bg = "#1f538d" if cid == self.selected_id else "#2b2b2b"
                if frame.cget("fg_color") != nowy_bg:
                    frame.configure(fg_color=nowy_bg)

    def select_item(self, cid):
        self.selected_id = cid
        self.btn_ed.configure(state="normal")
        self.btn_del.configure(state="normal")
        self.odswiez_tabele(pelne=False) # Tylko zmiana koloru

    def handle_add(self):
        try:
            il = int(self.e_il.get()) if self.e_il.get() else 0
            self.db.dodaj_sciernice(self.c_typ.get(), self.e_param.get(), self.e_opis.get(), self.e_ziarno.get(), self.c_prod.get(), il)
            self.e_opis.delete(0, 'end'); self.e_param.delete(0, 'end'); self.e_il.delete(0, 'end')
            self.odswiez_tabele(pelne=True)
        except ValueError:
            messagebox.showerror("Błąd", "Ilość musi być liczbą!", parent=self)

    def confirm_delete_main(self):
        if self.selected_id and messagebox.askyesno("Potwierdzenie", f"Czy usunąć ściernicę ID {self.selected_id}?", parent=self):
            self.db.usun_pozycje(self.selected_id)
            self.selected_id = None
            self.btn_ed.configure(state="disabled")
            self.btn_del.configure(state="disabled")
            self.odswiez_tabele(pelne=True)

    def open_edit(self):
        if self.selected_id:
            dane = self.db.pobierz_dane("")
            item = next((s for s in dane if s["id"] == self.selected_id), None)
            if item: EditWindow(self, self.db, item, lambda: self.odswiez_tabele(pelne=True))

    def setup_ui_error(self):
        f = ctk.CTkFrame(self.container); f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="⚠️ BRAK POŁĄCZENIA", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=20, padx=50)
        ctk.CTkButton(f, text="PONÓW", command=self.sprawdz_polaczenie).pack(pady=10)

    def show_popup_filter(self, column_name, display_name):
        """Uniwersalne okno filtra z rygorystyczną blokadą wielokrotnego otwarcia."""
        
        # 1. Sprawdzenie czy okno istnieje. winfo_exists() jest kluczowe, 
        # bo zmienna może nie być None, mimo że okno zostało zamknięte przez 'X'.
        if self._filter_popup is not None and self._filter_popup.winfo_exists():
            self._filter_popup.focus()  # Przywołaj istniejące okno na wierzch
            return

        # 2. Pobranie unikalnych wartości z bazy danych
        all_options = self.db.pobierz_unikalne_wartosci(column_name)

        # 3. Tworzenie okna
        self._filter_popup = ctk.CTkToplevel(self)
        self._filter_popup.title(f"Filtr: {display_name}")
        self._filter_popup.geometry("280x420")
        self._filter_popup.attributes("-topmost", True)
        
        # Pozycjonowanie przy kursorze myszy
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        self._filter_popup.geometry(f"+{x}+{y}")

        # 4. Obsługa zamknięcia okna przez "X" w rogu (systemowe zamknięcie)
        # Bez tego, po kliknięciu X zmienna _filter_popup nie stałaby się None
        self._filter_popup.protocol("WM_DELETE_WINDOW", self._on_filter_popup_close)

        vars = {}
        is_all_selected = len(self.active_filters[column_name]) == 0
        all_var = ctk.BooleanVar(value=is_all_selected)

        def toggle_all():
            for v in vars.values(): v.set(all_var.get())

        ctk.CTkCheckBox(self._filter_popup, text="Zaznacz wszystko", variable=all_var, command=toggle_all).pack(pady=10, padx=10, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self._filter_popup)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        for opt in all_options:
            is_selected = opt in self.active_filters[column_name] if self.active_filters[column_name] else True
            v = ctk.BooleanVar(value=is_selected)
            ctk.CTkCheckBox(scroll, text=opt, variable=v).pack(pady=2, padx=5, anchor="w")
            vars[opt] = v

        def apply():
            selected = [opt for opt, v in vars.items() if v.get()]
            
            if 0 < len(selected) < len(all_options):
                self.active_filters[column_name] = selected
                self.header_labels[column_name].configure(text_color="#f1c40f")
                
                # Dynamiczne zarządzanie kolejnością:
                if column_name not in self.filter_order:
                    self.filter_order.append(column_name) # Dodaj na koniec jako najważniejszy
            else:
                self.active_filters[column_name] = []
                self.header_labels[column_name].configure(text_color="#FFFFFF")
                
                # Usuń z kolejki, jeśli filtr został wyłączony:
                if column_name in self.filter_order:
                    self.filter_order.remove(column_name)
            
            self._on_filter_popup_close()
            self.odswiez_tabele(pelne=True)

        ctk.CTkButton(self._filter_popup, text="Zastosuj", fg_color="#1f538d", command=apply).pack(pady=10)

    def _on_filter_popup_close(self):
        """Pomocnicza metoda niszcząca okno i resetująca referencję."""
        if self._filter_popup:
            self._filter_popup.destroy()
            self._filter_popup = None