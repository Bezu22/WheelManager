import customtkinter as ctk
from tkinter import messagebox # Potrzebne do okna ostrzeżenia

# --- USTAWIENIA GLOBALNE ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.15)

class EditWindow(ctk.CTkToplevel):
    def __init__(self, parent, db, item_data, callback):
        super().__init__(parent)
        self.title(f"Edycja ID: {item_data['id']}")
        self.geometry("500x750")
        self.db = db
        self.item = item_data
        self.callback = callback
        self.attributes('-topmost', True)

        f_bold = ("Arial", 16, "bold")
        f_norm = ("Arial", 14)

        ctk.CTkLabel(self, text="EDYCJA PARAMETRÓW", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Opis
        ctk.CTkLabel(self, text="Opis:", font=f_norm).pack(pady=(10, 0))
        self.e_opis = ctk.CTkEntry(self, width=350, height=40, font=f_norm)
        self.e_opis.insert(0, self.item.get("opis", ""))
        self.e_opis.pack(pady=5)

        # Kąt z kosmetyką stopnia
        ctk.CTkLabel(self, text="Kąt:", font=f_norm).pack(pady=(10, 0))
        # Dodajemy symbol stopnia do wartości z bazy w menu rozwijanym
        katy_z_ikona = [f"{k}°" if k != "N/A" else k for k in self.db.dane["konfiguracja"]["katy"]]
        self.c_kat = ctk.CTkComboBox(self, values=katy_z_ikona, width=350, height=40, font=f_norm)
        
        aktualny_kat = str(self.item.get("kat", "N/A"))
        if aktualny_kat != "N/A" and "°" not in aktualny_kat:
            aktualny_kat += "°"
        self.c_kat.set(aktualny_kat)
        self.c_kat.pack(pady=5)

        ctk.CTkLabel(self, text="STANY MAGAZYNOWE", font=f_bold).pack(pady=20)
        
        self.status_entries = {}
        for status, ilosc in self.item["ilosc"].items():
            f = ctk.CTkFrame(self)
            f.pack(pady=3, fill="x", padx=40)
            ctk.CTkLabel(f, text=status, width=180, anchor="w", font=f_norm).pack(side="left", padx=10)
            ent = ctk.CTkEntry(f, width=80, height=35, font=f_norm)
            ent.insert(0, str(ilosc))
            ent.pack(side="right", padx=10)
            self.status_entries[status] = ent

        # PRZYCISKI AKCJI
        self.btn_save = ctk.CTkButton(self, text="ZAPISZ ZMIANY", fg_color="#2ecc71", hover_color="#27ae60",
                                     font=f_bold, height=50, command=self.save)
        self.btn_save.pack(pady=(30, 10))

        self.btn_delete = ctk.CTkButton(self, text="USUŃ POZYCJĘ Z BAZY", fg_color="#e74c3c", hover_color="#c0392b",
                                       font=("Arial", 12, "bold"), height=40, command=self.confirm_delete)
        self.btn_delete.pack(pady=10)

    def save(self):
        try:
            nowe_ilosci = {s: int(e.get()) for s, e in self.status_entries.items()}
            # Usuwamy symbol stopnia przed zapisem do JSON, żeby zachować czyste dane
            czysty_kat = self.c_kat.get().replace("°", "")
            
            update = {"opis": self.e_opis.get(), "kat": czysty_kat, "ilosc": nowe_ilosci}
            self.db.aktualizuj_pozycje(self.item["id"], update)
            self.callback()
            self.destroy()
        except ValueError:
            pass

    def confirm_delete(self):
        # Liczymy sumę wszystkich sztuk
        suma_sztuk = sum(int(e.get()) for e in self.status_entries.values())
        
        msg = "Czy na pewno chcesz usunąć tę ściernicę?"
        if suma_sztuk > 0:
            msg = f"UWAGA! Na stanie znajduje się jeszcze {suma_sztuk} szt. tej ściernicy.\nCzy na pewno chcesz ją CAŁKOWICIE usunąć z bazy?"

        if messagebox.askyesno("Potwierdzenie usunięcia", msg):
            # Usuwanie z listy w bazie
            self.db.dane["sciernice"] = [s for s in self.db.dane["sciernice"] if s["id"] != self.item["id"]]
            self.db.zapisz()
            self.callback()
            self.destroy()

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected_id = None
        self.color_map = {"W uzyciu": "#90EE90", "magazyn": "#FFFFFF", "zamowiona": "#3498db", "zlom": "#e74c3c"}
        self.font_header = ("Arial", 13, "bold")
        self.font_row = ("Arial", 13)
        self.font_ui = ("Arial", 14)

        self.title("System Magazynowy Ściernic v2.8")
        self.geometry("1450x900")
        
        self.col_widths = {"typ": 100, "kat": 80, "opis": 280, "ziarno": 100, "producent": 170, "statusy": 500}

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.sprawdz_polaczenie()

    def sprawdz_polaczenie(self):
        for w in self.container.winfo_children(): w.destroy()
        if self.db.polacz():
            self.setup_ui_pelny()
        else:
            self.setup_ui_error()

    def setup_ui_error(self):
        f = ctk.CTkFrame(self.container)
        f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="⚠️", font=("Arial", 70)).pack(pady=10)
        ctk.CTkLabel(f, text="BRAK POŁĄCZENIA Z BAZĄ", font=("Arial", 22, "bold"), text_color="#e74c3c").pack(pady=10, padx=60)
        ctk.CTkButton(f, text="PONÓW", font=self.font_ui, height=45, command=self.sprawdz_polaczenie).pack(pady=25)

    def setup_ui_pelny(self):
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frame_tabela = ctk.CTkFrame(self.container)
        self.frame_tabela.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.h_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=10, pady=10)
        
        for h in ["typ", "kat", "opis", "ziarno", "producent", "statusy"]:
            ctk.CTkLabel(self.h_frame, text=h.upper(), width=self.col_widths[h], 
                         anchor="w", font=self.font_header).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.p_form = ctk.CTkFrame(self.container)
        self.p_form.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        conf = self.db.dane["konfiguracja"]
        katy_ikona = [f"{k}°" if k != "N/A" else k for k in conf["katy"]]

        self.c_typ = ctk.CTkComboBox(self.p_form, values=conf["typy"], width=100, height=40)
        self.c_typ.pack(side="left", padx=3)
        self.c_kat = ctk.CTkComboBox(self.p_form, values=katy_ikona, width=80, height=40)
        self.c_kat.pack(side="left", padx=3)
        self.e_opis = ctk.CTkEntry(self.p_form, placeholder_text="Opis", width=280, height=40)
        self.e_opis.pack(side="left", padx=3)
        self.e_ziarno = ctk.CTkEntry(self.p_form, placeholder_text="Ziarno", width=100, height=40)
        self.e_ziarno.pack(side="left", padx=3)
        self.c_prod = ctk.CTkComboBox(self.p_form, values=conf["producenci"], width=170, height=40)
        self.c_prod.pack(side="left", padx=3)
        self.e_il = ctk.CTkEntry(self.p_form, placeholder_text="Szt.", width=70, height=40)
        self.e_il.pack(side="left", padx=3)

        ctk.CTkButton(self.p_form, text="DODAJ", fg_color="#2ecc71", width=120, height=40, font=self.font_header, command=self.handle_add).pack(side="left", padx=15)
        self.btn_ed = ctk.CTkButton(self.p_form, text="EDYTUJ WYBRANĄ", fg_color="#3498db", state="disabled", width=200, height=40, font=self.font_header, command=self.open_edit)
        self.btn_ed.pack(side="right", padx=10)

        self.odswiez_tabele()

    def odswiez_tabele(self):
        for w in self.scroll.winfo_children(): w.destroy()
        for s in self.db.dane["sciernice"]:
            is_selected = (self.selected_id == s["id"])
            bg = "#1f538d" if is_selected else "#2b2b2b"
            f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=0)
            f.pack(fill="x", pady=2)
            f.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
            
            # Wartość kąta z ikoną w tabeli
            kat_val = str(s.get("kat", "N/A"))
            if kat_val != "N/A" and "°" not in kat_val:
                kat_val += "°"

            pola = [("typ", s["typ"]), ("kat", kat_val), ("opis", s["opis"]), 
                    ("ziarno", s["ziarno"]), ("producent", s["producent"])]
            
            for key, val in pola:
                l = ctk.CTkLabel(f, text=str(val), width=self.col_widths[key], anchor="w", font=self.font_row)
                l.pack(side="left", padx=5, pady=8)
                l.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

            stat_frame = ctk.CTkFrame(f, fg_color="transparent")
            stat_frame.pack(side="left", padx=5)
            aktywne = {k: v for k, v in s["ilosc"].items() if v > 0}
            if not aktywne:
                ctk.CTkLabel(stat_frame, text="---", text_color="gray", font=self.font_row).pack(side="left")
            else:
                for st, il in aktywne.items():
                    lbl = ctk.CTkLabel(stat_frame, text=f"{st}: {il}", text_color=self.color_map.get(st, "#FFF"), font=("Arial", 12, "bold"))
                    lbl.pack(side="left", padx=12)
                    lbl.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

    def select_item(self, cid):
        self.selected_id = cid
        self.btn_ed.configure(state="normal")
        self.odswiez_tabele()

    def handle_add(self):
        # Usuwamy symbol stopnia przed wysłaniem do bazy
        kat_czysty = self.c_kat.get().replace("°", "")
        self.db.dodaj_sciernice(self.c_typ.get(), kat_czysty, self.e_opis.get(), 
                               self.e_ziarno.get(), self.c_prod.get(), self.e_il.get())
        self.e_opis.delete(0, 'end'); self.e_il.delete(0, 'end')
        self.odswiez_tabele()

    def open_edit(self):
        if self.selected_id:
            item = next(s for s in self.db.dane["sciernice"] if s["id"] == self.selected_id)
            EditWindow(self, self.db, item, self.odswiez_tabele)