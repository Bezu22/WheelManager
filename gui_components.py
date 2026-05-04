import customtkinter as ctk
from tkinter import messagebox

class EditWindow(ctk.CTkToplevel):
    def __init__(self, parent, db, item_data, callback):
        super().__init__(parent)
        self.title(f"Edycja ID: {item_data['id']}")
        
        # Ustawienie okna na wierzchu względem rodzica
        self.transient(parent)
        self.grab_set() # Blokuje interakcję z oknem pod spodem do czasu zamknięcia

        window_w, window_h = 500, 700 # Nieco niższe okno, bo nie ma przycisku usuń
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - window_w) / 2)
        y = int((screen_h - window_h) / 2)
        self.geometry(f"{window_w}x{window_h}+{x}+{y}")

        self.db = db
        self.item = item_data
        self.callback = callback

        f_bold = ("Arial", 16, "bold")
        f_norm = ("Arial", 14)

        ctk.CTkLabel(self, text="EDYCJA PARAMETRÓW", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Dynamiczna etykieta parametru (Kąt/Promień/Szerokość)
        typ_s = self.item.get("typ", "")
        p_label = "Parametr:"
        if typ_s == "1V1": p_label = "Kąt (°):"
        elif typ_s == "1S1": p_label = "Promień (R):"
        elif typ_s == "1A1": p_label = "Szerokość (T):"

        # Pola edycyjne
        ctk.CTkLabel(self, text="Opis:", font=f_norm).pack(pady=(10, 0))
        self.e_opis = ctk.CTkEntry(self, width=350, height=40)
        self.e_opis.insert(0, self.item.get("opis", ""))
        self.e_opis.pack(pady=5)

        ctk.CTkLabel(self, text=p_label, font=f_norm).pack(pady=(10, 0))
        self.e_param = ctk.CTkEntry(self, width=350, height=40)
        self.e_param.insert(0, str(self.item.get("kat", "")))
        self.e_param.pack(pady=5)

        ctk.CTkLabel(self, text="STANY MAGAZYNOWE", font=f_bold).pack(pady=20)
        
        self.status_entries = {}
        for status, ilosc in self.item["ilosc"].items():
            f = ctk.CTkFrame(self)
            f.pack(pady=3, fill="x", padx=40)
            ctk.CTkLabel(f, text=status, width=180, anchor="w", font=f_norm).pack(side="left", padx=10)
            ent = ctk.CTkEntry(f, width=80, height=35)
            ent.insert(0, str(ilosc))
            ent.pack(side="right", padx=10)
            self.status_entries[status] = ent

        self.btn_save = ctk.CTkButton(
            self, text="ZAPISZ ZMIANY", 
            fg_color="#2ecc71", font=f_bold, height=50, 
            command=self.save
        )
        self.btn_save.pack(pady=(40, 10))

    def save(self):
        try:
            nowe_ilosci = {s: int(e.get()) for s, e in self.status_entries.items()}
            update = {
                "opis": self.e_opis.get(),
                "kat": self.e_param.get(),
                "ilosc": nowe_ilosci
            }
            self.db.aktualizuj_pozycje(self.item["id"], update)
            self.callback()
            self.destroy()
        except ValueError:
            messagebox.showerror("Błąd", "Wprowadź poprawne liczby w stanach!", parent=self)