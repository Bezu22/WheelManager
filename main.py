from database import InventoryDB
from gui import MagazynGUI

def main():
    # 1. Inicjalizacja bazy danych
    db = InventoryDB("magazyn.json")
    
    # 2. Uruchomienie interfejsu i przekazanie mu bazy
    app = MagazynGUI(db)
    app.mainloop()

if __name__ == "__main__":
    main()