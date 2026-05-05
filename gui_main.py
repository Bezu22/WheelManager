import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from gui_components import EditWindow, FilterPopup

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        # --- KONFIGURACJA KOLORÓW ---
        self.RED_FIRMOWY = "#DF010E"
        self.RED_HOVER = "#B0010B"
        self.BG_DARK = "#121212"
        self.CARD_BG = "#1E1E1E"
        self.TEXT_DIM = "#AAAAAA"
        
        self.selected_id = None
        self.last_selected_id = None # Do optymalizacji odświeżania
        self._filter_popup = None
        self.widzety_wierszy = {}
        self._ostatnia_fraza = ""
        self.active_filters = {"typ": [], "ziarno": [], "producent": []}
        self.filter_order = []

        self.title("WHEEL MANAGER | System Zarządzania Ściernicami")
        self.window_width, self.window_height = 1450, 850
        pos_x = int((self.winfo_screenwidth() - self.window_width) / 2)
        self.geometry(f"{self.window_width}x{self.window_height}+{pos_x}+50")
        self.configure(fg_color=self.BG_DARK)

        self.color_map = {"W uzyciu": "#90EE90", "magazyn": "#FFFFFF", "zamowiona": "#3498db", "zlom": "#e74c3c"}
        
        self._setup_layout()
        self.sprawdz_polaczenie()

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color="#181818")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 1. Ładowanie obrazu logo
        try:
            # Ścieżka do pliku (najlepiej trzymać go w tym samym folderze co skrypt)
            logo_img_path = "logo.png" 
            raw_image = Image.open(logo_img_path)

            # Obliczamy proporcje, aby nie rozciągnąć logo
            width, height = raw_image.size
            ratio = width / height
            new_width = 180
            new_height = int(new_width / ratio)
                        
            self.logo_image = ctk.CTkImage(
                light_image=raw_image,
                dark_image=raw_image,
                size=(new_width, new_height) # Wymiary wyświetlania (szerokość, wysokość)
            )
            
            self.image_label = ctk.CTkLabel(self.sidebar, image=self.logo_image, text="")
            self.image_label.pack(pady=(20, 0))
        except Exception as e:
            print(f"Nie udało się załadować logo: {e}")

        # 2. Napis pod logo (zmniejszony odstęp górny)
        self.logo_label = ctk.CTkLabel(self.sidebar, text="WHEEL\nMANAGER", 
                                    font=("Impact", 28), text_color=self.RED_FIRMOWY)
        self.logo_label.pack(pady=(10, 50))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.odswiez_tabele(pelne=True))
        self.e_search = ctk.CTkEntry(self.sidebar, placeholder_text="Szukaj...", textvariable=self.search_var, height=40, fg_color="#252525", border_color="#333")
        self.e_search.pack(fill="x", padx=20, pady=(5, 30))

        self.btn_ed = self._sidebar_button("EDYTUJ POZYCJĘ", self.RED_FIRMOWY, self.open_edit)
        self.btn_del = self._sidebar_button("USUŃ Z BAZY", "#333", self.confirm_delete)
        
        # Main
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

    def _sidebar_button(self, text, color, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color=color, hover_color=self.RED_HOVER, height=45, font=("Arial", 12, "bold"), command=command, state="disabled")
        btn.pack(fill="x", padx=20, pady=10)
        return btn

    def sprawdz_polaczenie(self):
        if self.db.polacz(): self.setup_ui_pelny()
        else: self.setup_ui_error()

    def setup_ui_pelny(self):
        self.h_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.h_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        headers = [("typ", "TYP ▾"), ("ziarno", "ZIARNO ▾"), ("producent", "PRODUCENT ▾")]
        self.header_labels = {}
        for k, text in headers:
            btn = ctk.CTkButton(self.h_frame, text=text, width=140, height=32, fg_color="#252525", hover_color="#333", font=("Arial", 11, "bold"), command=lambda col=k, name=text: self.show_filter(col, name))
            btn.pack(side="left", padx=5)
            self.header_labels[k] = btn

        self.scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self._build_bottom_add_panel()
        self.odswiez_tabele(pelne=True)

    def _build_bottom_add_panel(self):
        self.p_form = ctk.CTkFrame(self.main_content, fg_color="#181818", corner_radius=12)
        self.p_form.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        conf = self.db.dane["konfiguracja"]
        
        r1 = ctk.CTkFrame(self.p_form, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=(10, 5))
        self.c_typ = ctk.CTkComboBox(r1, values=self.db.lista_typow, width=120)
        self.c_typ.pack(side="left", padx=5)
        self.e_param = ctk.CTkEntry(r1, placeholder_text="Parametr", width=120)
        self.e_param.pack(side="left", padx=5)
        self.e_ziarno = ctk.CTkEntry(r1, placeholder_text="Ziarno/Nasyp", width=120)
        self.e_ziarno.pack(side="left", padx=5)
        self.c_prod = ctk.CTkComboBox(r1, values=conf.get("producenci", []), width=180)
        self.c_prod.pack(side="left", padx=5)

        r2 = ctk.CTkFrame(self.p_form, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(5, 10))
        self.e_opis = ctk.CTkEntry(r2, placeholder_text="Opis wymiarowy...", width=450)
        self.e_opis.pack(side="left", padx=5)
        self.e_il = ctk.CTkEntry(r2, placeholder_text="Szt.", width=70)
        self.e_il.pack(side="left", padx=5)
        ctk.CTkButton(r2, text="DODAJ DO BAZY", fg_color=self.RED_FIRMOWY, hover_color=self.RED_HOVER, width=150, font=("Arial", 12, "bold"), command=self.handle_add).pack(side="right", padx=5)

    def odswiez_tabele(self, pelne=False):
        """Zoptymalizowane odświeżanie - nie przeładowuje wszystkiego przy zaznaczaniu."""
        if not pelne:
            self._update_card_selection()
            return

        fraza = self.search_var.get()
        self._ostatnia_fraza = f"{fraza}_{str(self.active_filters)}_{str(self.filter_order)}"
        
        for w in self.scroll.winfo_children(): w.destroy()
        self.widzety_wierszy = {}
        
        dane = self.db.pobierz_dane(fraza, self.active_filters, self.filter_order)
        self._render_cards(dane)

    def _render_cards(self, dane):
        """Renderuje kompaktowe karty"""
        ustawienia = self.db.dane["konfiguracja"].get("typy_ustawienia", {})
        for s in dane:
            is_sel = self.selected_id == s["id"]
            
            # ZMNIEJSZONY PADY I MARGINESY (pady=4 zamiast 8)
            card = ctk.CTkFrame(self.scroll, fg_color=self.CARD_BG if not is_sel else self.RED_FIRMOWY, 
                                border_color=self.RED_FIRMOWY if is_sel else "#333",
                                border_width=1, corner_radius=8)
            card.pack(fill="x", pady=4, padx=5) # Zwężenie odstępów między kartami
            self.widzety_wierszy[s["id"]] = card
            
            # --- LEWA SEKCJA (KOMPAKTOWA) ---
            left_f = ctk.CTkFrame(card, fg_color="transparent")
            left_f.pack(side="left", padx=15, pady=8) # Mniejszy padding pionowy
            
            ctk.CTkLabel(left_f, text=s["typ"], font=("Arial", 16, "bold"), 
                         text_color=self.RED_FIRMOWY if not is_sel else "white").pack(anchor="w")
            
            konfig = ustawienia.get(s["typ"], {})
            param_str = f"{konfig.get('prefix','')}{s['kat']}{konfig.get('suffix','')}"
            ctk.CTkLabel(left_f, text=param_str, font=("Arial", 13, "bold"), 
                         text_color="#FFFFFF" if not is_sel else "white").pack(anchor="w")

            # --- ŚRODKOWA SEKCJA ---
            mid_f = ctk.CTkFrame(card, fg_color="transparent")
            mid_f.pack(side="left", expand=True, fill="both", padx=15)
            
            prod_text = f"{s['producent']}  |  {s['ziarno']}"
            ctk.CTkLabel(mid_f, text=prod_text, font=("Arial", 13, "bold"), 
                         text_color="#EEEEEE" if not is_sel else "white").pack(anchor="w", pady=(5, 0))
            
            ctk.CTkLabel(mid_f, text=s["opis"], font=("Arial", 12), 
                         text_color=self.TEXT_DIM if not is_sel else "white", anchor="w").pack(fill="x", pady=(0, 5))

            # Statusy
            self._render_status_pills(card, s, is_sel)

            # Bindowanie kliknięcia do całej karty i jej dzieci
            card.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
                if isinstance(child, ctk.CTkFrame):
                    for subchild in child.winfo_children():
                        subchild.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

    def _render_status_pills(self, parent, item, is_sel):
        """Mniejsze pigułki statusu dla kompaktowego widoku."""
        pill_f = ctk.CTkFrame(parent, fg_color="transparent")
        pill_f.pack(side="right", padx=15)
        
        statusy = [("magazyn", "MAG"), ("uzycie", "UŻY"), ("zamowiona", "ZAM")]
        for key, label in statusy:
            val = item.get(key, 0)
            if val > 0:
                # Ciemniejsza pigułka gdy karta nie jest wybrana
                bg_pill = "#2A2A2A" if not is_sel else self.RED_HOVER
                f = ctk.CTkFrame(pill_f, fg_color=bg_pill, corner_radius=6, border_width=1, border_color="#444")
                f.pack(side="left", padx=4)
                
                color = self.color_map.get("W uzyciu" if key=="uzycie" else key, "#FFF")
                txt_color = color if not is_sel else "white"
                
                lbl = ctk.CTkLabel(f, text=f"{label}: {val}", font=("Arial", 11, "bold"), 
                                   text_color=txt_color, padx=8, pady=3)
                lbl.pack()
                lbl.original_color = color

    def _update_card_selection(self):
        """Zoptymalizowana aktualizacja z poprawnym przywracaniem kolorów statusów."""
        # 1. Reset starej karty
        if self.last_selected_id in self.widzety_wierszy:
            old_card = self.widzety_wierszy[self.last_selected_id]
            old_card.configure(fg_color=self.CARD_BG, border_color="#333", border_width=1)
            self._restore_original_colors(old_card)

        # 2. Aktywacja nowej karty
        if self.selected_id in self.widzety_wierszy:
            new_card = self.widzety_wierszy[self.selected_id]
            new_card.configure(fg_color=self.RED_FIRMOWY, border_color="#FFFFFF", border_width=2)
            self._set_labels_contrast(new_card, is_selected=True)

    def _set_labels_contrast(self, parent, is_selected):
        """Wymusza biały tekst na czerwonym tle zaznaczenia."""
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text_color="white")
            elif isinstance(child, ctk.CTkFrame):
                self._set_labels_contrast(child, is_selected)

    def _restore_original_colors(self, parent):
        """Przywraca kolory zgodnie z hierarchią bez nadpisywania statusów."""
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                # 1. Priorytet: Statusy (pigułki)
                if hasattr(child, "original_color"):
                    child.configure(text_color=child.original_color)
                # 2. Nagłówek (Typ) - sprawdzamy po czcionce lub kluczu
                elif child.cget("font") == ("Arial", 20, "bold"):
                    child.configure(text_color=self.RED_FIRMOWY)
                # 3. Parametr techniczny
                elif child.cget("font") == ("Arial", 15, "bold"):
                    child.configure(text_color="#FFFFFF")
                # 4. Producent/Ziarno
                elif child.cget("font") == ("Arial", 14, "bold"):
                    child.configure(text_color="#EEEEEE")
                # 5. Opis
                else:
                    child.configure(text_color=self.TEXT_DIM)
            elif isinstance(child, ctk.CTkFrame):
                self._restore_original_colors(child)

    def _set_labels_white(self, parent):
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text_color="white")
            if isinstance(child, ctk.CTkFrame):
                self._set_labels_white(child)

    def select_item(self, cid):
        """Zarządzanie wyborem bez zawieszania GUI."""
        if self.selected_id == cid: return # Kliknięcie w to samo
        
        self.last_selected_id = self.selected_id
        self.selected_id = cid
        
        self.btn_ed.configure(state="normal", fg_color=self.RED_FIRMOWY)
        self.btn_del.configure(state="normal", fg_color="#c0392b")
        
        self.odswiez_tabele(pelne=False) # To teraz wywoła tylko _update_card_selection

    def handle_add(self):
        try:
            d = {'typ': self.c_typ.get(), 'kat': self.e_param.get(), 'opis': self.e_opis.get(), 'ziarno': self.e_ziarno.get(), 'producent': self.c_prod.get(), 'magazyn': int(self.e_il.get() or 0)}
            self.db.dodaj_sciernice(d)
            self.odswiez_tabele(pelne=True)
        except Exception as e: messagebox.showerror("Błąd", f"Niepoprawne dane: {e}")

    def show_filter(self, col, name):
        if self._filter_popup and self._filter_popup.winfo_exists(): self._filter_popup.focus(); return
        self._filter_popup = FilterPopup(self, col, name, self.db, self.active_filters[col], self._handle_filter_apply)

    def _handle_filter_apply(self, col, vals):
        self.active_filters[col] = vals
        self.header_labels[col].configure(fg_color=self.RED_FIRMOWY if vals else "#252525")
        if col in self.filter_order: self.filter_order.remove(col)
        if vals: self.filter_order.insert(0, col)
        self.odswiez_tabele(pelne=True)

    def open_edit(self):
        item = next((s for s in self.db.pobierz_dane("") if s["id"] == self.selected_id), None)
        if item: EditWindow(self, self.db, item, lambda: self.odswiez_tabele(pelne=True))

    def confirm_delete(self):
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć tę ściernicę?"):
            self.db.usun_pozycje(self.selected_id)
            self.selected_id = None
            self.odswiez_tabele(pelne=True)

    def setup_ui_error(self):
        f = ctk.CTkFrame(self.container); f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="⚠️ BŁĄD POŁĄCZENIA", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=20, padx=50)
        ctk.CTkButton(f, text="SPRÓBUJ PONOWNIE", command=self.sprawdz_polaczenie).pack(pady=10)