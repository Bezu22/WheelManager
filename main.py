from pathlib import Path
from database import InventoryDB
from gui import MagazynGUI

def main():
    # Definicja ścieżki sieciowej do folderu
    SCIEZKA_SIECIOWA = Path("//192.168.1.1/technika/Kosiarski/BazaSciernic")
    
    # Pełna ścieżka do pliku JSON
    PLIK_BAZY = SCIEZKA_SIECIOWA / "magazyn.json"
    
    # Przekazujemy pełną ścieżkę do bazy
    db = InventoryDB(str(PLIK_BAZY))
    
    app = MagazynGUI(db)
    app.mainloop()

if __name__ == "__main__":
    main()