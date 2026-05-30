"""
app.py — Punto de entrada.

Sin argumentos  -> abre la GUI (customtkinter).
Con argumentos  -> modo consola (CLI con argparse).

Ejemplos:
    python app.py                 # ventana
    python app.py --list          # lista perfiles
    python app.py --use copia     # activa el perfil "copia"
    python app.py --status        # estado actual
"""

import sys


def main() -> int:
    if len(sys.argv) > 1:
        import cli
        return cli.main()
    import gui
    gui.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
