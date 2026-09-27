"""
Google Sheets Local Launcher
============================
Abre Google Sheets en el navegador predeterminado y copia la ruta
del archivo Excel al portapapeles para importarlo con un clic o arrastrar.
"""

import sys
import os
import subprocess
import webbrowser

def open_file_in_sheets(file_path: str):
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"[!] El archivo no existe: {abs_path}")
        return

    # Copiar ruta al portapapeles en Windows
    try:
        subprocess.run(
            ["powershell", "-Command", f"Set-Clipboard -Value '{abs_path}'"],
            check=True,
            capture_output=True
        )
        print(f"[OK] Ruta copiada al portapapeles: {abs_path}")
    except Exception:
        pass

    # Abrir Google Sheets
    print("[*] Abriendo Google Sheets en el navegador...")
    webbrowser.open("https://sheets.new")

    print("\n" + "=" * 65)
    print("INSTRUCCIONES PARA VER EN GOOGLE SHEETS:")
    print("=" * 65)
    print("1. En la pestaña de Google Sheets, presiona Ctrl + O (o Archivo > Abrir).")
    print("2. Ve a la pestaña 'Subir' (Upload).")
    print("3. Arrastra el archivo Excel o presiona 'Examinar' y pega (Ctrl + V) la ruta.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Chicago_Commercial_Market_Sample.xlsx"
    open_file_in_sheets(target)
