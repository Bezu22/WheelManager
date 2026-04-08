import customtkinter as ctk

class EditWindow(ctk.CTkToplevel):
    def __init__(self, parent, db, item_data, callback):
        super().__init__(parent)
        self.title(f"Edycja ID: {item_data['id']}")
        self.geometry("450x600")
        self.db = db
        self.item = item_data
        self.callback = callback
        self.attributes('-topmost', True)

        ctk.CTkLabel(self, text="EDYCJA PARAMETROW", font=("Arial", 16, "bold")).pack(pady=20)
        
        self.e_opis = ctk.CTkEntry(self, width=300)
        self.e_opis.insert(0, self.item["opis"])
        self.e_opis.pack(pady=10)

        ctk.CTkLabel(self, text="STANY MAGAZYNOWE", font=("Arial", 14, "bold")).pack(pady=10)
        self.status_entries = {}
        
        for status, ilosc in self.item["ilosc"].items():
            f = ctk.CTkFrame(self)
            f.pack(pady=2, fill="x", padx=50)
            ctk.CTkLabel(f, text=status, width=150, anchor="w").pack(side="left")
            ent = ctk.CTkEntry(f, width=70)
            ent.insert(0, str(ilosc))
            ent.pack(side="right")
            self.status_entries[status] = ent

        ctk.CTkButton(self, text="ZAPISZ ZMIANY", fg_color="#2ecc71", font=("Arial", 12, "bold"),
                     height=40, command=self.save).pack(pady=40)

    def save(self):
        try:
            nowe_ilosci = {s: int(e.get()) for s, e in self.status_entries.items()}
            update = {"opis": self.e_opis.get(), "ilosc": nowe_ilosci}
            self.db.aktualizuj_pozycje(self.item["id"], update)
            self.callback()
            self.destroy()
        except ValueError:
            pass

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected_id = None
        self.title("System Magazynowy Sciernic v2.5")
        self.geometry("1250x800")
        self.col_widths = {"typ": 80, "opis": 250, "ziarno": 80, "producent": 150, "statusy": 450}

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
        ctk.CTkLabel(f, text="⚠️", font=("Arial", 50)).pack(pady=10)
        ctk.CTkLabel(f, text="BRAK DOSTEPU DO BAZY (JSON)", font=("Arial", 16, "bold"), text_color="#e74c3c").pack(pady=10, padx=40)
        ctk.CTkButton(f, text="SPRAWDZ PONOWNIE", command=self.sprawdz_polaczenie).pack(pady=20)

    def setup_ui_pelny(self):
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # TABELA
        self.frame_tabela = ctk.CTkFrame(self.container)
        self.frame_tabela.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.h_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=10, pady=5)
        for h in ["typ", "opis", "ziarno", "producent", "statusy"]:
            ctk.CTkLabel(self.h_frame, text=h.upper(), width=self.col_widths[h], anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # PANEL DOLNY
        self.p_form = ctk.CTkFrame(self.container)
        self.p_form.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        conf = self.db.dane["konfiguracja"]
        self.c_typ = ctk.CTkComboBox(self.p_form, values=conf["typy"], width=80)
        self.c_typ.pack(side="left", padx=2)
        self.e_opis = ctk.CTkEntry(self.p_form, placeholder_text="Opis", width=250)
        self.e_opis.pack(side="left", padx=2)
        self.e_ziarno = ctk.CTkEntry(self.p_form, placeholder_text="Ziarno", width=80)
        self.e_ziarno.pack(side="left", padx=2)
        self.c_prod = ctk.CTkComboBox(self.p_form, values=conf["producenci"], width=150)
        self.c_prod.pack(side="left", padx=2)
        self.e_il = ctk.CTkEntry(self.p_form, placeholder_text="Ilosc", width=60)
        self.e_il.pack(side="left", padx=2)

        ctk.CTkButton(self.p_form, text="DODAJ", fg_color="#2ecc71", width=100, command=self.handle_add).pack(side="left", padx=15)
        self.btn_ed = ctk.CTkButton(self.p_form, text="EDYTUJ ZAZNACZONE", fg_color="#3498db", state="disabled", command=self.open_edit)
        self.btn_ed.pack(side="right", padx=10)

        self.odswiez_tabele()

    def odswiez_tabele(self):
        for w in self.scroll.winfo_children(): w.destroy()
        for s in self.db.dane["sciernice"]:
            bg = "#1f538d" if self.selected_id == s["id"] else "#2b2b2b"
            f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=0)
            f.pack(fill="x", pady=1)
            f.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))
            
            for k in ["typ", "opis", "ziarno", "producent"]:
                l = ctk.CTkLabel(f, text=s[k], width=self.col_widths[k], anchor="w")
                l.pack(side="left", padx=5)
                l.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

            aktywne = [f"{k}: {v}" for k, v in s["ilosc"].items() if v > 0]
            txt = " | ".join(aktywne) if aktywne else "---"
            l_st = ctk.CTkLabel(f, text=txt, width=self.col_widths["statusy"], anchor="w", text_color="#f1c40f")
            l_st.pack(side="left", padx=5)
            l_st.bind("<Button-1>", lambda e, cid=s["id"]: self.select_item(cid))

    def select_item(self, cid):
        self.selected_id = cid
        self.btn_ed.configure(state="normal")
        self.odswiez_tabele()

    def handle_add(self):
        self.db.dodaj_sciernice(self.c_typ.get(), self.e_opis.get(), self.e_ziarno.get(), self.c_prod.get(), self.e_il.get())
        self.e_opis.delete(0, 'end'); self.e_il.delete(0, 'end')
        self.odswiez_tabele()

    def open_edit(self):
        item = next(s for s in self.db.dane["sciernice"] if s["id"] == self.selected_id)
        EditWindow(self, self.db, item, self.odswiez_tabele)