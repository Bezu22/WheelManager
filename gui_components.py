import customtkinter as ctk
from tkinter import messagebox

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

        # Kąt
        ctk.CTkLabel(self, text="Kąt:", font=f_norm).pack(pady=(10, 0))
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

        self.btn_save = ctk.CTkButton(self, text="ZAPISZ ZMIANY", fg_color="#2ecc71", font=f_bold, height=50, command=self.save)
        self.btn_save.pack(pady=(30, 10))

        self.btn_delete = ctk.CTkButton(self, text="USUŃ POZYCJĘ", fg_color="#e74c3c", height=40, command=self.confirm_delete)
        self.btn_delete.pack(pady=10)

    def save(self):
        try:
            nowe_ilosci = {s: int(e.get()) for s, e in self.status_entries.items()}
            czysty_kat = self.c_kat.get().replace("°", "")
            update = {"opis": self.e_opis.get(), "kat": czysty_kat, "ilosc": nowe_ilosci}
            self.db.aktualizuj_pozycje(self.item["id"], update)
            self.callback()
            self.destroy()
        except ValueError: pass

    def confirm_delete(self):
        suma_sztuk = sum(int(e.get()) for e in self.status_entries.values())
        msg = "Czy usunąć tę ściernicę?"
        if suma_sztuk > 0:
            msg = f"UWAGA! Na stanie jest {suma_sztuk} szt. Czy na pewno usunąć?"
        if messagebox.askyesno("Potwierdzenie", msg):
            self.db.dane["sciernice"] = [s for s in self.db.dane["sciernice"] if s["id"] != self.item["id"]]
            self.db.zapisz()
            self.callback()
            self.destroy()