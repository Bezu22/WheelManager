import customtkinter as ctk
from tkinter import messagebox

class EditWindow(ctk.CTkToplevel):
    def __init__(self, parent, db, item_data, callback):
        super().__init__(parent)
        self.db = db
        self.item = item_data
        self.callback = callback

        # --- USTAWIENIA OKNA ---
        self.title(f"Edycja ID: {self.item['id']}")
        
        # Blokowanie okna głównego i wymuszenie wierzchu
        self.transient(parent)
        self.grab_set()
        
        window_w, window_h = 500, 750
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - window_w) / 2)
        y = int((screen_h - window_h) / 2)
        self.geometry(f"{window_w}x{window_h}+{x}+{y}")

        # --- STYLE I CZCIONKI ---
        f_bold = ("Arial", 16, "bold")
        f_norm = ("Arial", 14)

        # --- DYNAMICZNA KONFIGURACJA PARAMETRU ---
        # Pobieramy ustawienia dla danego typu z konfiguracji wczytanej z JSON
        typ_s = self.item.get("typ", "")
        ustawienia_typow = self.db.dane["konfiguracja"].get("typy_ustawienia", {})
        konfig_typu = ustawienia_typow.get(typ_s, {})
        
        label_base = konfig_typu.get("label", "Parametr")
        prefix = konfig_typu.get("prefix", "")
        suffix = konfig_typu.get("suffix", "")
        
        # Budujemy czytelną etykietę, np. "Promień (R ...):"
        hint = f" ({prefix}...{suffix})" if (prefix or suffix) else ""
        p_label_text = f"{label_base}{hint}:"

        # --- BUDOWA INTERFEJSU ---
        ctk.CTkLabel(self, text="EDYCJA POZYCJI", font=("Arial", 22, "bold")).pack(pady=20)

        # Informacja o Typie (nieedytowalne dla bezpieczeństwa bazy)
        ctk.CTkLabel(self, text=f"Typ ściernicy: {typ_s}", font=f_bold, text_color="#3498db").pack(pady=5)

        # Pole: Opis
        ctk.CTkLabel(self, text="Opis wymiarowy:", font=f_norm).pack(pady=(20, 0))
        self.e_opis = ctk.CTkEntry(self, width=380, height=40, font=f_norm)
        self.e_opis.insert(0, self.item.get("opis", ""))
        self.e_opis.pack(pady=5)

        # Pole: Parametr (dynamiczny)
        ctk.CTkLabel(self, text=p_label_text, font=f_norm).pack(pady=(15, 0))
        self.e_param = ctk.CTkEntry(self, width=380, height=40, font=f_norm)
        self.e_param.insert(0, str(self.item.get("kat", "")))
        self.e_param.pack(pady=5)

        # Sekcja: Stany Magazynowe
        ctk.CTkLabel(self, text="STANY MAGAZYNOWE", font=f_bold).pack(pady=25)
        
        self.status_entries = {}
        # Pobieramy listę statusów z konfiguracji
        lista_statusow = self.db.dane["konfiguracja"].get("statusy", ["magazyn", "W uzyciu", "zamowiona", "zlom"])
        
        for status in lista_statusow:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(pady=3, fill="x", padx=60)
            
            ctk.CTkLabel(f, text=status, width=150, anchor="w", font=f_norm).pack(side="left")
            
            ent = ctk.CTkEntry(f, width=80, height=35, font=f_norm)
            # Pobieramy aktualną ilość dla danego statusu
            aktualna_ilosc = self.item["ilosc"].get(status, 0)
            ent.insert(0, str(aktualna_ilosc))
            ent.pack(side="right")
            
            self.status_entries[status] = ent

        # Przycisk Zapisu
        self.btn_save = ctk.CTkButton(
            self, 
            text="ZAPISZ ZMIANY", 
            fg_color="#2ecc71", 
            hover_color="#27ae60",
            font=f_bold, 
            height=55, 
            width=380,
            command=self.save
        )
        self.btn_save.pack(pady=(40, 20))

    def save(self):
        """Walidacja i zapis danych do bazy SQL."""
        try:
            # Konwersja pól stanów na liczby całkowite
            nowe_ilosci = {s: int(e.get()) for s, e in self.status_entries.items()}
            
            update_data = {
                "opis": self.e_opis.get(),
                "kat": self.e_param.get(),
                "ilosc": nowe_ilosci
            }
            
            # Wywołanie aktualizacji w bazie danych
            self.db.aktualizuj_pozycje(self.item["id"], update_data)
            
            # Odświeżenie tabeli głównej i zamknięcie okna
            self.callback()
            self.destroy()
            
        except ValueError:
            # parent=self zapewnia, że błąd nie schowa się pod oknem
            messagebox.showerror(
                "Błąd formatu", 
                "Pola ilościowe muszą zawierać tylko liczby całkowite!", 
                parent=self
            )