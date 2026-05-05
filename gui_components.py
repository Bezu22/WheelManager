import customtkinter as ctk
from tkinter import messagebox

class BaseDialog(ctk.CTkToplevel):
    """Klasa bazowa dla okien dialogowych zapewniająca spójność wizualną."""
    def __init__(self, parent, title, width=400, height=500):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        
        # Centrowanie okna względem ekranu
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.attributes("-topmost", True)

class EditWindow(BaseDialog):
    """Komponent okna edycji - zarządza własnym formularzem."""
    def __init__(self, parent, db, item_data, on_save_callback):
        super().__init__(parent, f"Edycja ID: {item_data['id']}", 500, 750)
        self.db = db
        self.item = item_data
        self.on_save = on_save_callback
        self.status_entries = {}
        self._setup_ui()

    def _setup_ui(self):
        f_bold = ("Arial", 16, "bold")
        f_norm = ("Arial", 14)

        # Pobieranie konfiguracji typu ściernicy
        conf = self.db.dane["konfiguracja"].get("typy_ustawienia", {}).get(self.item['typ'], {})
        label_text = f"{conf.get('label', 'Parametr')} ({conf.get('prefix', '')}...{conf.get('suffix', '')}):"

        ctk.CTkLabel(self, text="EDYCJA POZYCJI", font=("Arial", 22, "bold")).pack(pady=20)
        
        # Pola tekstowe
        self.e_opis = self._create_input("Opis wymiarowy:", self.item.get("opis", ""), f_norm)
        self.e_param = self._create_input(label_text, str(self.item.get("kat", "")), f_norm)

        # Sekcja ilościowa
        ctk.CTkLabel(self, text="STANY MAGAZYNOWE", font=f_bold).pack(pady=25)
        lista_statusow = self.db.dane["konfiguracja"].get("statusy", ["magazyn", "W uzyciu", "zamowiona", "zlom"])
        
        for status in lista_statusow:
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(pady=3, fill="x", padx=60)
            ctk.CTkLabel(frame, text=status, width=150, anchor="w", font=f_norm).pack(side="left")
            
            ent = ctk.CTkEntry(frame, width=80, height=35, font=f_norm)
            ent.insert(0, str(self.item["ilosc"].get(status, 0)))
            ent.pack(side="right")
            self.status_entries[status] = ent

        ctk.CTkButton(self, text="ZAPISZ ZMIANY", fg_color="#2ecc71", font=f_bold, 
                     height=55, width=380, command=self._handle_save).pack(pady=(40, 20))

    def _create_input(self, label, value, font):
        ctk.CTkLabel(self, text=label, font=font).pack(pady=(10, 0))
        entry = ctk.CTkEntry(self, width=380, height=40, font=font)
        entry.insert(0, value)
        entry.pack(pady=5)
        return entry

    def _handle_save(self):
        try:
            nowe_ilosci = {s: int(e.get()) for s, e in self.status_entries.items()}
            update_data = {
                "opis": self.e_opis.get(),
                "kat": self.e_param.get(),
                "ilosc": nowe_ilosci
            }
            self.db.aktualizuj_pozycje(self.item["id"], update_data)
            self.on_save()
            self.destroy()
        except ValueError:
            messagebox.showerror("Błąd", "Pola ilościowe muszą być liczbami!", parent=self)

class FilterPopup(BaseDialog):
    """Komponent okna filtra - enkapsuluje logikę wyboru wartości."""
    def __init__(self, parent, column_name, display_name, db, active_filters, on_apply_callback):
        super().__init__(parent, f"Filtr: {display_name}", 280, 420)
        self.db = db
        self.column_name = column_name
        self.active_filters = active_filters
        self.on_apply = on_apply_callback
        self.vars = {}
        self._setup_ui()

    def _setup_ui(self):
        options = self.db.pobierz_unikalne_wartosci(self.column_name)
        
        all_var = ctk.BooleanVar(value=len(self.active_filters) == 0)
        ctk.CTkCheckBox(self, text="Zaznacz wszystko", variable=all_var, 
                        command=lambda: [v.set(all_var.get()) for v in self.vars.values()]).pack(pady=10, padx=10, anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        for opt in options:
            is_sel = opt in self.active_filters if self.active_filters else True
            v = ctk.BooleanVar(value=is_sel)
            ctk.CTkCheckBox(scroll, text=opt, variable=v).pack(pady=2, padx=5, anchor="w")
            self.vars[opt] = v

        ctk.CTkButton(self, text="Zastosuj", fg_color="#1f538d", command=self._apply).pack(pady=10)

    def _apply(self):
        selected = [opt for opt, v in self.vars.items() if v.get()]
        # Zwracamy listę wybranych elementów lub pustą listę (jeśli wybrano wszystko)
        final_selection = selected if len(selected) < len(self.vars) else []
        self.on_apply(self.column_name, final_selection)
        self.destroy()