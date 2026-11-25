"""Verificación HTTP real con dos arranques de Flask y archivos temporales."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from archivos import cargar_datos


def peticion(base, ruta, metodo="GET", datos=None):
    cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
    solicitud = Request(base + ruta, data=cuerpo, method=metodo,
                        headers={"Content-Type": "application/json"} if cuerpo else {})
    with urlopen(solicitud, timeout=5) as respuesta:
        contenido = respuesta.read()
        return respuesta.status, json.loads(contenido) if "application/json" in respuesta.headers.get("Content-Type", "") else contenido


def iniciar(carpeta, puerto, registro):
    proceso = subprocess.Popen([sys.executable, "main.py", "--puerto", str(puerto), "--datos", str(carpeta)],
                               cwd=Path(__file__).resolve().parent, stdout=registro, stderr=registro,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    limite = time.monotonic() + 15
    try:
        while time.monotonic() < limite:
            if proceso.poll() is not None:
                raise RuntimeError("Flask terminó antes de iniciar.")
            try:
                peticion(f"http://127.0.0.1:{puerto}", "/api/resumen")
                return proceso
            except (URLError, TimeoutError):
                time.sleep(0.1)
        raise RuntimeError("Flask no respondió dentro de 15 segundos.")
    except Exception:
        detener(proceso)
        raise


def detener(proceso):
    if proceso.poll() is not None:
        return
    if os.name == "nt":
        # En Windows el lanzador del entorno virtual puede iniciar otro proceso Python.
        subprocess.run(["taskkill", "/PID", str(proceso.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, check=True)
    else:
        proceso.terminate()
    try:
        proceso.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.wait(timeout=5)


def main():
    with tempfile.TemporaryDirectory(prefix="aulagest-http-") as temporal:
        carpeta = Path(temporal) / "datos"
        with socket.socket() as puerto_libre:
            puerto_libre.bind(("127.0.0.1", 0))
            puerto = puerto_libre.getsockname()[1]
        base = f"http://127.0.0.1:{puerto}"
        with (Path(temporal) / "http.log").open("w", encoding="utf-8") as registro:
            proceso = iniciar(carpeta, puerto, registro)
            try:
                estado, html = peticion(base, "/")
                assert estado == 200 and b"AulaGest" in html
                for endpoint in ("resumen", "aulas", "horarios", "reservas", "docentes", "asignaturas", "edificios", "solicitudes", "rutas", "historial"):
                    assert peticion(base, "/api/" + endpoint)[0] == 200
                aula = {"id": "HTTP999", "nombre": "Aula de prueba HTTP", "edificio": "A", "piso": 3,
                        "capacidad": 42, "tipo": "Teórica", "equipamiento": ["Pizarra"]}
                assert peticion(base, "/api/aulas", "POST", aula)[0] == 201
                assert any(a["id"] == "HTTP999" for a in cargar_datos(carpeta / "aulas.json", "aulas"))
                reserva = {"aula": "HTTP999", "docente": "D01", "fecha": "2030-01-06", "inicio": "10:00",
                           "fin": "11:00", "motivo": "Verificación HTTP", "asistentes": 20}
                estado, guardada = peticion(base, "/api/reservas", "POST", reserva)
                assert estado == 201
                print("OK: HTML, 10 endpoints, alta de aula y escritura del JSON por HTTP.")
            finally:
                detener(proceso)
            proceso = iniciar(carpeta, puerto, registro)
            try:
                assert peticion(base, "/api/aulas/HTTP999")[1]["capacidad"] == 42
                assert any(r["id"] == guardada["id"] for r in peticion(base, "/api/reservas")[1])
                assert peticion(base, "/api/historial")[1]
                print("OK: reinicio real; aula, reserva e historial conservados.")
            finally:
                detener(proceso)
        print("Prueba HTTP completada. Los datos principales no se modificaron.")


if __name__ == "__main__":
    main()
