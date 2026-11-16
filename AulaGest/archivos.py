"""Único módulo de lectura/escritura JSON; validación y reemplazo atómico."""
import json
import os
import tempfile
from pathlib import Path
from datetime import timedelta
from horarios import ahora_nicaragua, validar_fecha, validar_intervalo

COLECCIONES = ("aulas", "docentes", "asignaturas", "horarios", "reservas",
               "edificios", "solicitudes", "historial")
CAMPOS = {
    "aulas": {"nombre": str, "edificio": str, "piso": int, "capacidad": int,
              "tipo": str, "equipamiento": list},
    "docentes": {"nombre": str, "especialidad": str},
    "asignaturas": {"nombre": str, "creditos": int},
    "edificios": {"nombre": str, "descripcion": str, "conexiones": list},
    "horarios": {"aula": str, "docente": str, "asignatura": str, "dia": int,
                 "inicio": str, "fin": str, "asistentes": int},
    "reservas": {"aula": str, "docente": str, "fecha": str, "inicio": str,
                 "fin": str, "motivo": str, "asistentes": int, "estado": str},
    "solicitudes": {"aula": str, "docente": str, "fecha": str, "inicio": str,
                    "fin": str, "motivo": str, "asistentes": int, "estado": str,
                    "prioridad": int, "orden": int},
    "historial": {"accion": str, "detalle": str, "fecha": str},
}


def verificar_estructura(datos, nombre):
    # O(n), además del tamaño de los campos. Nunca repara datos silenciosamente.
    if nombre not in CAMPOS or not isinstance(datos, list):
        raise ValueError(f"{nombre}: se esperaba una lista de registros.")
    identificadores, ordenes = set(), set()
    for registro in datos:
        if not isinstance(registro, dict):
            raise ValueError(f"{nombre}: cada registro debe ser un objeto.")
        for campo, tipo in {"id": str, **CAMPOS[nombre]}.items():
            if type(registro.get(campo)) is not tipo:
                raise ValueError(f"{nombre}: campo '{campo}' ausente o de tipo incorrecto.")
        if not registro["id"] or registro["id"] in identificadores:
            raise ValueError(f"{nombre}: identificador vacío o duplicado.")
        identificadores.add(registro["id"])
        for campo in ("equipamiento", "conexiones"):
            if campo in registro and any(not isinstance(v, str) for v in registro[campo]):
                raise ValueError(f"{nombre}: {campo} debe contener textos.")
        if "inicio" in registro:
            validar_intervalo(registro["inicio"], registro["fin"])
        if nombre in ("reservas", "solicitudes"):
            validar_fecha(registro["fecha"])
            estados = ("activa", "cancelada") if nombre == "reservas" else ("pendiente", "aprobada", "rechazada")
            if registro["estado"] not in estados:
                raise ValueError(f"{nombre}: estado incorrecto.")
        if nombre == "horarios" and not 0 <= registro["dia"] <= 5:
            raise ValueError("horarios: día fuera de rango 0–5.")
        if nombre == "solicitudes":
            if not 1 <= registro["prioridad"] <= 5 or registro["orden"] < 1 or registro["orden"] in ordenes:
                raise ValueError("solicitudes: prioridad o contador de llegada incorrectos.")
            ordenes.add(registro["orden"])
        for campo in ("capacidad", "asistentes", "creditos"):
            if campo in registro and registro[campo] < 1:
                raise ValueError(f"{nombre}: {campo} debe ser positivo.")
        if "piso" in registro and registro["piso"] < 0:
            raise ValueError("aulas: el piso debe ser cero o mayor.")
    return datos


def cargar_datos(ruta, nombre=None):
    ruta = Path(ruta)
    try:
        with ruta.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if nombre:
            verificar_estructura(datos, nombre)
        return datos
    except (OSError, ValueError, UnicodeError) as error:
        raise ValueError(f"No se pudo leer {ruta.name}: {error}. Archivo conservado; recupérelo antes de continuar.") from error


def guardar_datos(ruta, datos):
    # O(bytes del JSON). El temporal está en el mismo disco para os.replace.
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ruta.parent,
                                         suffix=".tmp", delete=False) as archivo:
            temporal = Path(archivo.name)
            json.dump(datos, archivo, ensure_ascii=False, indent=2, allow_nan=False)
            archivo.write("\n")
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal and temporal.exists():
            temporal.unlink()


def crear_archivos_si_no_existen(carpeta, iniciales):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    # Validar TODOS los archivos existentes antes de crear alguno.
    for nombre in COLECCIONES:
        ruta = carpeta / f"{nombre}.json"
        if ruta.exists():
            cargar_datos(ruta, nombre)
    for nombre in COLECCIONES:
        ruta = carpeta / f"{nombre}.json"
        if not ruta.exists():
            guardar_datos(ruta, iniciales.get(nombre, []))


def guardar_cambios(carpeta, cambios):
    """Diario sencillo para recuperar una operación que afecta varios JSON."""
    carpeta = Path(carpeta)
    for nombre, registros in cambios.items():
        verificar_estructura(registros, nombre)
        destino = carpeta / f"{nombre}.json"
        if destino.exists():
            cargar_datos(destino, nombre)  # No sobreescribir un archivo dañado.
    diario = carpeta / "transaccion.json"
    guardar_datos(diario, cambios)
    for nombre, registros in cambios.items():
        guardar_datos(carpeta / f"{nombre}.json", registros)
    diario.unlink()


def cargar_todo(carpeta):
    carpeta = Path(carpeta)
    diario = carpeta / "transaccion.json"
    if diario.exists():
        cambios = cargar_datos(diario)
        if not isinstance(cambios, dict) or not cambios or any(n not in COLECCIONES for n in cambios):
            raise ValueError("Diario de transacción dañado. Se conservó para recuperación manual.")
        guardar_cambios(carpeta, cambios)
    return {n: cargar_datos(carpeta / f"{n}.json", n) for n in COLECCIONES}


def datos_iniciales():
    """Datos ficticios reproducibles; fechas relativas solo al crear por primera vez."""
    datos = {n: [] for n in COLECCIONES}
    datos["edificios"] = [
        {"id": "A", "nombre": "Ciencias y Tecnología", "descripcion": "Aulas teóricas y laboratorios de informática.", "conexiones": ["B"]},
        {"id": "B", "nombre": "Humanidades e Innovación", "descripcion": "Espacios para aprender, colaborar y crear.", "conexiones": ["A"]},
    ]
    for edificio in "AB":
        for piso in (1, 2):
            for numero in range(1, 4):
                codigo = f"{edificio}{piso}0{numero}"
                datos["aulas"].append({"id": codigo, "nombre": f"Aula {codigo}", "edificio": edificio,
                    "piso": piso, "capacidad": 25 + numero * 10, "tipo": "Laboratorio" if numero == 3 else "Teórica",
                    "equipamiento": ["Pizarra", "Proyector"] + (["Computadoras"] if numero == 3 else [])})
    nombres = ["Lucía Montes", "Gabriel Rivas", "Elena Solís", "Mateo Duarte", "Valeria Paz", "Daniel Lagos"]
    materias = ["Programación Estructurada", "Matemática I", "Física General", "Álgebra Lineal",
                "Comunicación", "Estadística", "Introducción a Sistemas", "Ética Profesional"]
    datos["docentes"] = [{"id": f"D{i+1:02}", "nombre": n, "especialidad": materias[i]} for i, n in enumerate(nombres)]
    datos["asignaturas"] = [{"id": f"AS{i+1:02}", "nombre": n, "creditos": 4 if i < 4 else 3} for i, n in enumerate(materias)]
    for dia in range(6):
        for i, aula in enumerate(datos["aulas"]):
            inicio = 7 + (i % 4) * 2
            datos["horarios"].append({"id": f"H{dia}{i:02}", "aula": aula["id"], "docente": f"D{i%6+1:02}",
                "asignatura": f"AS{i%8+1:02}", "dia": dia, "inicio": f"{inicio:02}:00",
                "fin": f"{inicio+2:02}:00", "asistentes": 25})
    hoy = ahora_nicaragua().date()
    for i in range(3):
        fecha = (hoy + timedelta(days=i)).isoformat()
        datos["reservas"].append({"id": f"R-DEMO-{i}", "aula": f"A10{i+1}", "docente": f"D{i+1:02}",
            "fecha": fecha, "inicio": "16:00", "fin": "17:30", "motivo": ["Tutoría de programación", "Sesión de estudio", "Taller de proyectos"][i],
            "asistentes": 20, "estado": "activa"})
        datos["solicitudes"].append({"id": f"S-DEMO-{i}", "aula": f"B10{i+1}", "docente": f"D{i+1:02}",
            "fecha": fecha, "inicio": "17:00", "fin": "18:00", "motivo": ["Examen de recuperación", "Clase de refuerzo", "Club de tecnología"][i],
            "asistentes": 20, "estado": "pendiente", "prioridad": [2, 3, 4][i], "orden": i+1})
    return datos
