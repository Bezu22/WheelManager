import customtkinter as ctk
from tkinter import messagebox
from gui_components import EditWindow, FilterPopup

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        # Inicjalizacja stanu
        self.selected_id = None
        self._filter_popup = None
        self.widzety_wierszy = {}
        self._ostatnia_fraza = ""
        self.active_filters = {"typ": [], "ziarno": [], "producent": []}
        self.filter_order = []

        # Konfiguracja okna
        self.window_width, self.window_height = 1450, 850
        pos_x = int((self.winfo_screenwidth() - self.window_width) / 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{pos_x}+50")
        self.title("System Zarządzania Ściernicami v5.0")

        # Stałe wizualne
        self.color_map = {"W uzyciu": "#90EE90", "magazyn": "#FFFFFF", "zamowiona": "#3498db", "zlom": "#e74c3c"}
        self.font_header = ("Arial", 13, "bold")
        self.font_row = ("Arial", 13)
        self.col_widths = {"typ": 100, "kat": 120, "opis": 300, "ziarno": 100, "producent": 170, "statusy": 500}

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.sprawdz_polaczenie()

    def sprawdz_polaczenie(self):
        """Weryfikacja dostępności bazy danych przed budową UI."""
        for w in self.container.winfo_children(): w.destroy()
        if self.db.polacz(): 
            self.setup_ui_pelny()
        else: 
            self.setup_ui_error()

    def setup_ui_pelny(self):
        """Główny layout aplikacji."""
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Panel górny: Wyszukiwarka
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.odswiez_tabele(pelne=True))
        self.e_search = ctk.CTkEntry(self.container, placeholder_text="🔍 Szukaj w opisie lub parametrach...", 
                                     textvariable=self.search_var, width=500, height=40)
        self.e_search.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Sekcja Środkowa: Tabela
        self.frame_tabela = ctk.CTkFrame(self.container)
        self.frame_tabela.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        
        self._build_table_headers()
        
        self.scroll = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Sekcja Dolna: Formularz
        self._build_bottom_form()
        
        self.odswiez_tabele(pelne=True)

    def _build_table_headers(self):
        """Buduje nagłówki tabeli z funkcją filtrowania."""
        self.h_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=10, pady=10)
        
        self.header_labels = {}
        headers = [("typ", "TYP ▾", True), ("kat", "PARAMETR", False), ("opis", "OPIS", False), 
                   ("ziarno", "ZIARNO ▾", True), ("producent", "PRODUCENT ▾", True), ("statusy", "STATUSY", False)]

        for k, text, filtrowalna in headers:
            lbl = ctk.CTkLabel(self.h_frame, text=text, width=self.col_widths[k], anchor="w", font=self.font_header)
            lbl.pack(side="left", padx=5)
            self.header_labels[k] = lbl
            if filtrowalna:
                lbl.configure(cursor="hand2")
                lbl.bind("<Button-1>", lambda e, col=k, name=text: self.show_filter(col, name))

    def _build_bottom_form(self):
        """Buduje panel dodawania nowych ściernic."""
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

        self.btn_add = ctk.CTkButton(self.p_form, text="DODAJ", fg_color="#2ecc71", width=120, command=self.handle_add)
        self.btn_add.pack(side="left", padx=15)
        self.btn_del = ctk.CTkButton(self.p_form, text="USUŃ", state="disabled", fg_color="#c0392b", command=self.confirm_delete)
        self.btn_del.pack(side="right", padx=5)
        self.btn_ed = ctk.CTkButton(self.p_form, text="EDYTUJ", state="disabled", fg_color="#3498db", command=self.open_edit)
        self.btn_ed.pack(side="right", padx=5)

    def odswiez_tabele(self, pelne=False):
        """Zarządza wyświetlaniem danych w tabeli."""
        fraza = self.search_var.get()
        stan_filtrow = f"{fraza}_{str(self.active_filters)}_{str(self.filter_order)}"
        
        if pelne or stan_filtrow != self._ostatnia_fraza:
            self._ostatnia_fraza = stan_filtrow
            for w in self.scroll.winfo_children(): w.destroy()
            self.widzety_wierszy = {}
            
            dane = self.db.pobierz_dane(fraza, self.active_filters, self.filter_order)
            self._render_rows(dane)
        else:
            self._update_row_colors()

    def _render_rows(self, dane):
        """Renderuje wiersze danych w ScrollableFrame."""
        ustawienia = self.db.dane["konfiguracja"].get("typy_ustawienia", {})
        for s in dane:
            bg = "#1f538d" if self.selected_id == s["id"] else "#2b2b2b"
            f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4)
            f.pack(fill="x", pady=2, padx=2)
            self.widzety_wierszy[s["id"]] = f
            f.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
            
            konfig = ustawienia.get(s["typ"], {})
            wyswietlany_param = f"{konfig.get('prefix','')}{s['kat']}{konfig.get('suffix','')}"

            pola = [("typ", s["typ"]), ("kat", wyswietlany_param), ("opis", s["opis"]), 
                    ("ziarno", s["ziarno"]), ("producent", s["producent"])]
            for k, val in pola:
                l = ctk.CTkLabel(f, text=str(val), width=self.col_widths[k], anchor="w", font=self.font_row)
                l.pack(side="left", padx=5, pady=8)
                l.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

            self._render_status_badges(f, s)

    def _render_status_badges(self, parent_frame, item_data):
        """Renderuje kolorowe etykiety stanów magazynowych bezpośrednio z danych obiektu."""
        stat_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        stat_frame.pack(side="left", padx=5)
        
        # Definiujemy nazwy kluczy, które odpowiadają kolumnom w bazie danych
        statusy = [
            ("magazyn", "MAGAZYN"),
            ("uzycie", "W UZYCIU"),
            ("zamowiona", "ZAMÓWIONA"),
            ("zlom", "ZŁOM")
        ]
        
        for klucz, etykieta in statusy:
            # Pobieramy wartość bezpośrednio z item_data
            ilosc = item_data.get(klucz, 0)
            
            if ilosc > 0:
                # Mapowanie kolorów (uzywamy klucza z bazy lub etykiety dla color_map)
                color_key = "W uzyciu" if klucz == "uzycie" else klucz
                kolor = self.color_map.get(color_key, "#FFF")
                
                lbl = ctk.CTkLabel(
                    stat_frame, 
                    text=f"{etykieta}: {ilosc}", 
                    text_color=kolor, 
                    font=("Arial", 11, "bold")
                )
                lbl.pack(side="left", padx=10)
                lbl.bind("<Button-1>", lambda e, cid=item_data["id"]: self.select_item(cid))

    def _update_row_colors(self):
        """Szybka aktualizacja kolorów zaznaczenia."""
        for cid, frame in self.widzety_wierszy.items():
            nowy_bg = "#1f538d" if cid == self.selected_id else "#2b2b2b"
            if frame.cget("fg_color") != nowy_bg:
                frame.configure(fg_color=nowy_bg)

    def select_item(self, cid):
        self.selected_id = cid
        self.btn_ed.configure(state="normal")
        self.btn_del.configure(state="normal")
        self.odswiez_tabele(pelne=False)

    def show_filter(self, col, name):
        """Wywołuje zewnętrzny komponent filtra."""
        if self._filter_popup and self._filter_popup.winfo_exists():
            self._filter_popup.focus(); return
            
        self._filter_popup = FilterPopup(
            self, col, name, self.db, self.active_filters[col], self._handle_filter_apply
        )

    def _handle_filter_apply(self, col, selected_values):
        """Callback obsługujący zastosowanie filtra."""
        if selected_values:
            self.active_filters[col] = selected_values
            self.header_labels[col].configure(text_color="#f1c40f")
            if col in self.filter_order: self.filter_order.remove(col)
            self.filter_order.insert(0, col)
        else:
            self.active_filters[col] = []
            self.header_labels[col].configure(text_color="#FFFFFF")
            if col in self.filter_order: self.filter_order.remove(col)
        self.odswiez_tabele(pelne=True)

    def open_edit(self):
        """Wywołuje zewnętrzny komponent edycji."""
        dane = self.db.pobierz_dane("")
        item = next((s for s in dane if s["id"] == self.selected_id), None)
        if item: 
            EditWindow(self, self.db, item, lambda: self.odswiez_tabele(pelne=True))

    def handle_add(self):
        try:
            dane = {
                'typ': self.c_typ.get(), 'kat': self.e_param.get(), 
                'opis': self.e_opis.get(), 'ziarno': self.e_ziarno.get(),
                'producent': self.c_prod.get(), 'magazyn': int(self.e_il.get() or 0)
            }
            self.db.dodaj_sciernice(dane)
            self.e_opis.delete(0, 'end'); self.e_param.delete(0, 'end'); self.e_il.delete(0, 'end')
            self.odswiez_tabele(pelne=True)
        except ValueError:
            messagebox.showerror("Błąd", "Ilość musi być liczbą!", parent=self)

    def confirm_delete(self):
        if self.selected_id and messagebox.askyesno("Potwierdzenie", f"Czy usunąć ściernicę ID {self.selected_id}?", parent=self):
            self.db.usun_pozycje(self.selected_id)
            self.selected_id = None
            self.btn_ed.configure(state="disabled"); self.btn_del.configure(state="disabled")
            self.odswiez_tabele(pelne=True)

    def setup_ui_error(self):
        f = ctk.CTkFrame(self.container); f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="⚠️ BRAK POŁĄCZENIA", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=20, padx=50)
        ctk.CTkButton(f, text="PONÓW", command=self.sprawdz_polaczenie).pack(pady=10)