"""Punto de entrada de AulaGest; ejecutar con python main.py."""
import argparse
from servidor import crear_app


def main():
    parser = argparse.ArgumentParser(description="AulaGest · administración local de aulas")
    parser.add_argument("--puerto", type=int, default=5000)
    parser.add_argument("--datos", default=None, help="Carpeta JSON alternativa para pruebas aisladas")
    opciones = parser.parse_args()
    try:
        app = crear_app(opciones.datos)
    except (ValueError, OSError) as error:
        parser.exit(1, f"AulaGest no pudo iniciar: {error}\n")
    app.run(host="127.0.0.1", port=opciones.puerto, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
