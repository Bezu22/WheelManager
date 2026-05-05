from pathlib import Path
from database import InventoryDB
from gui_main import MagazynGUI

def main():
    # 1. Definicja ścieżek dostępu
    # Wykorzystanie Path z biblioteki pathlib zapewnia kompatybilność między systemami
    SCIEZKA_SIECIOWA = Path("//192.168.1.1/technika/Kosiarski/BazaSciernic")
    
    PLIK_BAZY = SCIEZKA_SIECIOWA / "magazyn.db"
    PLIK_CONFIG = SCIEZKA_SIECIOWA / "config.json"
    PLIK_LOG = SCIEZKA_SIECIOWA / "log.txt"
    
    # 2. Inicjalizacja Modelu (Bazy danych)
    # Przekazujemy ścieżki jako napisy (strings), bo sqlite3 tego wymaga
    db = InventoryDB(
        str(PLIK_BAZY), 
        str(PLIK_CONFIG), 
        str(PLIK_LOG)
    )
    
    # 3. Uruchomienie Widoku (GUI)
    # GUI otrzymuje obiekt bazy
    app = MagazynGUI(db)
    
    # Start pętli zdarzeń
    app.mainloop()

if __name__ == "__main__":
    main()