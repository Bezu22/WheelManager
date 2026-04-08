import customtkinter as ctk

class MagazynGUI(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db  # Połączenie z bazą
        self.sort_reverse = False
        
        self.title("System Magazynowy - Modułowy")
        self.geometry("1100x750")
        
        self.col_widths = {"typ": 100, "opis": 300, "ziarno": 100, "producent": 200, "status": 200}
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()

    def setup_ui(self):
        # Sekcja Tabeli
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.header_frame = ctk.CTkFrame(self.frame_tabela, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        for h in ["typ", "opis", "ziarno", "producent", "status"]:
            ctk.CTkButton(self.header_frame, text=h.upper(), width=self.col_widths[h],
                         command=lambda k=h: self.handle_sort(k)).pack(side="left", padx=2)

        self.scroll_frame = ctk.CTkScrollableFrame(self.frame_tabela, fg_color="#1a1a1a")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sekcja Formularza
        self.frame_form = ctk.CTkFrame(self)
        self.frame_form.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        konfig = self.db.dane["konfiguracja"]
        self.c_typ = ctk.CTkComboBox(self.frame_form, values=konfig["typy"], width=100)
        self.c_typ.pack(side="left", padx=2)
        
        self.e_opis = ctk.CTkEntry(self.frame_form, placeholder_text="Opis", width=300)
        self.e_opis.pack(side="left", padx=2)
        
        self.e_ziarno = ctk.CTkEntry(self.frame_form, placeholder_text="Ziarno", width=100)
        self.e_ziarno.pack(side="left", padx=2)
        
        self.c_prod = ctk.CTkComboBox(self.frame_form, values=konfig["producenci"], width=200)
        self.c_prod.pack(side="left", padx=2)
        
        self.c_stat = ctk.CTkComboBox(self.frame_form, values=konfig["statusy"], width=200)
        self.c_stat.pack(side="left", padx=2)

        ctk.CTkButton(self.frame_form, text="DODAJ", fg_color="green", width=80, 
                     command=self.handle_add).pack(side="left", padx=10)

        self.odswiez_tabele()

    def odswiez_tabele(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for i, s in enumerate(self.db.dane["sciernice"]):
            bg = "#2b2b2b" if i % 2 == 0 else "#333333"
            f = ctk.CTkFrame(self.scroll_frame, fg_color=bg, corner_radius=0)
            f.pack(fill="x", pady=1)
            for k in ["typ", "opis", "ziarno", "producent", "status"]:
                ctk.CTkLabel(f, text=s[k], width=self.col_widths[k]).pack(side="left", padx=2)

    def handle_add(self):
        self.db.dodaj_sciernice(self.c_typ.get(), self.e_opis.get(), 
                               self.e_ziarno.get(), self.c_prod.get(), self.c_stat.get())
        self.e_opis.delete(0, 'end')
        self.odswiez_tabele()

    def handle_sort(self, klucz):
        self.sort_reverse = not self.sort_reverse
        self.db.sortuj(klucz, self.sort_reverse)
        self.odswiez_tabele()