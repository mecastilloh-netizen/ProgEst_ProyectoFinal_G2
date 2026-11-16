"""Operaciones sencillas sobre la lista persistente de movimientos."""
from uuid import uuid4


def agregar_registro(historial, accion, detalle, fecha):
    # append es O(1) amortizado; no incluye el guardado en disco.
    registro = {"id": uuid4().hex, "accion": accion, "detalle": detalle, "fecha": fecha}
    historial.append(registro)
    return registro


def filtrar_registros(historial, texto=""):
    # O(n * m), donde m es la longitud del texto de cada registro.
    texto = texto.casefold()
    return [r for r in historial if texto in (r["accion"] + " " + r["detalle"]).casefold()]


def consultar_movimientos(historial, texto=""):
    return list(reversed(filtrar_registros(historial, texto)))


def operaciones_recientes(historial, limite=8):
    # O(min(n, limite)).
    return historial[-limite:][::-1] if limite > 0 else []
