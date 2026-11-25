"""Pruebas de reservas por persona con informes JSON independientes del campus."""
from datetime import datetime
from random import Random
from time import perf_counter
from uuid import uuid4
import re

import archivos
import horarios
import servicios


NOMBRE = re.compile(r"prueba-([0-9]{8}-[0-9]{6})-([1-9][0-9]*)-[0-9a-f]{32}")


def carpeta_informes(sistema):
    carpeta = sistema["carpeta"].resolve() / "simulaciones"
    if carpeta.resolve() != carpeta:
        raise ValueError("La carpeta de simulaciones debe estar dentro de la carpeta de datos.")
    return carpeta


def ruta_informe(sistema, identificador):
    if not NOMBRE.fullmatch(identificador):
        raise LookupError("No existe ese informe de prueba.")
    ruta = carpeta_informes(sistema) / (identificador + ".json")
    if ruta.is_symlink() or not ruta.is_file():
        raise LookupError("No existe ese informe de prueba.")
    return ruta


def listar_informes(sistema):
    informes = []
    for ruta in sorted(carpeta_informes(sistema).glob("prueba-*.json"), reverse=True):
        partes = NOMBRE.fullmatch(ruta.stem)
        if partes and not ruta.is_symlink() and ruta.is_file():
            creado = datetime.strptime(partes[1], "%Y%m%d-%H%M%S")
            informes.append({"id": ruta.stem, "creado": creado, "cantidad": int(partes[2])})
    return informes


def ejecutar(sistema, cantidad, fecha):
    if not re.fullmatch(r"0*[1-9][0-9]*", cantidad):
        raise ValueError("Indica un número entero mayor que cero.")
    cantidad = int(cantidad)
    horarios.validar_fecha(fecha)
    datos = sistema["datos"]
    if not datos["aulas"] or not datos["docentes"]:
        raise ValueError("Registra al menos un aula y un docente para ejecutar la prueba.")

    # Solo agregamos registros a esta lista local. Los catálogos se usan para consulta.
    reservas = list(datos["reservas"])
    copia = {"arbol": sistema["arbol"], "datos": {**datos, "reservas": reservas}}
    azar = Random(42)  # La misma secuencia permite comparar tamaños de prueba.
    resultados = []
    aprobadas = 0
    inicio = perf_counter()
    for persona in range(1, cantidad + 1):
        hora = azar.randrange(8, 16)
        entrada = {"aula": azar.choice(datos["aulas"])["id"], "docente": azar.choice(datos["docentes"])["id"],
                   "inicio": f"{hora:02}:00", "fin": f"{hora+1:02}:00", "fecha": fecha,
                   "motivo": f"Prueba de persona {persona}", "asistentes": 1}
        fila = {"persona": persona, "aula": entrada["aula"], "inicio": entrada["inicio"], "fin": entrada["fin"]}
        try:
            evento = servicios.validar_evento(copia, entrada, "reservas")
            servicios.comprobar_conflicto(copia, evento)
        except (ValueError, FileExistsError) as error:
            fila.update(estado="Rechazada", motivo=str(error))
        else:
            reservas.append({**evento, "id": f"sim-{persona}", "estado": "activa"})
            aprobadas += 1
            fila.update(estado="Aprobada", motivo="Aula disponible")
        resultados.append(fila)

    informe = {"fecha": fecha, "cantidad": cantidad, "aprobadas": aprobadas, "rechazadas": cantidad - aprobadas,
               "duracion_ms": round((perf_counter() - inicio) * 1000, 2), "resultados": resultados}
    marca = horarios.ahora_nicaragua().strftime("%Y%m%d-%H%M%S")
    identificador = f"prueba-{marca}-{cantidad}-{uuid4().hex}"
    archivos.guardar_datos(carpeta_informes(sistema) / (identificador + ".json"), informe)
    return identificador
