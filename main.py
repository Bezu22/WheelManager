from pathlib import Path
from database import InventoryDB
from gui_main import MagazynGUI

def main():
    # Definicja ścieżki sieciowej do folderu
    SCIEZKA_SIECIOWA = Path("//192.168.1.1/technika/Kosiarski/BazaSciernic")
    
    # Pełna ścieżka do pliku JSON
    PLIK_BAZY = SCIEZKA_SIECIOWA / "magazyn.db"
    PLIK_CONFIG = SCIEZKA_SIECIOWA / "config.json"
    
    # Przekazujemy pełną ścieżkę do bazy
    db = InventoryDB(str(PLIK_BAZY),str(PLIK_CONFIG))
    
    app = MagazynGUI(db)
    app.mainloop()

if __name__ == "__main__":
    main()