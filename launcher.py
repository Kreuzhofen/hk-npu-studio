from engine.brand_manager import BrandManager


def main():
    while True:
        print("=" * 50)
        print(f"      {BrandManager.APP_NAME} {BrandManager.APP_VERSION}")
        print("=" * 50)
        print()
        print("1  GUI starten")
        print("0  Beenden")
        print()
        choice = input("Auswahl: ").strip()
        print()
        if choice == "1":
            import gui
            app = gui.SnapdragonAIStudio()
            app.mainloop()
        elif choice == "0":
            print("Beendet.")
            break
        else:
            print("Ungültige Eingabe.")
        print()

if __name__ == "__main__":
    main()
