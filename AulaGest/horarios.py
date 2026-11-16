"""Validación de intervalos y disponibilidad semanal y por fecha en Nicaragua."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
import math

try:
    ZONA = ZoneInfo("America/Managua")
except ZoneInfoNotFoundError:
    # Windows puede no incluir IANA. Nicaragua usa UTC-6 sin cambio estacional
    # actualmente. Este respaldo evita otra dependencia para el prototipo.
    ZONA = timezone(timedelta(hours=-6), "America/Managua")

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def ahora_nicaragua():
    return datetime.now(ZONA)


def validar_fecha(valor):
    if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        raise ValueError("La fecha debe tener formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ValueError("La fecha indicada no existe.") from None


def minutos(hora):
    if not isinstance(hora, str) or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", hora):
        raise ValueError("La hora debe tener formato HH:MM, entre 00:00 y 23:59.")
    horas, minuto = map(int, hora.split(":"))
    return horas * 60 + minuto


def validar_intervalo(inicio, fin):
    if minutos(inicio) >= minutos(fin):
        raise ValueError("La hora inicial debe ser menor que la hora final; use un solo día.")


def se_superponen(inicio_a, fin_a, inicio_b, fin_b):
    # O(1). Intervalos [inicio, fin): 08:00-09:00 y 09:00-10:00 son compatibles.
    return inicio_a < fin_b and inicio_b < fin_a


def mismo_dia(a, b):
    if "fecha" in a and "fecha" in b:
        return a["fecha"] == b["fecha"]
    if "fecha" not in a and "fecha" not in b:
        return a["dia"] == b["dia"]
    fechado, semanal = (a, b) if "fecha" in a else (b, a)
    return validar_fecha(fechado["fecha"]).weekday() == semanal["dia"]


def detectar_conflictos(nuevo, horarios, reservas, excluir_id=None):
    # O(H + R). Al editar, solo se excluye el registro de su propio tipo.
    conflictos = []
    for tipo, registros in (("horario", horarios), ("reserva", reservas)):
        for registro in registros:
            if registro.get("estado") == "cancelada":
                continue
            if excluir_id == (tipo, registro["id"]):
                continue
            if registro["aula"] == nuevo["aula"] and mismo_dia(nuevo, registro):
                if se_superponen(nuevo["inicio"], nuevo["fin"], registro["inicio"], registro["fin"]):
                    conflictos.append({**registro, "tipo_registro": tipo})
    return conflictos


def eventos_del_dia(aula, fecha, horarios, reservas):
    dia = validar_fecha(fecha).weekday()
    eventos = [{**h, "fecha": fecha, "tipo_registro": "horario"} for h in horarios
               if h["aula"] == aula and h["dia"] == dia]
    eventos += [{**r, "tipo_registro": "reserva"} for r in reservas
                if r["aula"] == aula and r["fecha"] == fecha and r["estado"] == "activa"]
    return sorted(eventos, key=lambda e: e["inicio"])


def disponibilidad(aula, momento, horarios, reservas):
    # O(H + R + k log k), k = eventos del aula. Incluye la próxima semana.
    fecha = momento.date().isoformat()
    hora = momento.strftime("%H:%M")
    eventos = eventos_del_dia(aula, fecha, horarios, reservas)
    actual = next((e for e in eventos if e["inicio"] <= hora < e["fin"]), None)
    futuras = []
    for horario in horarios:
        if horario["aula"] != aula:
            continue
        dias = (horario["dia"] - momento.weekday()) % 7
        if dias == 0 and horario["inicio"] <= hora:
            dias = 7
        futura = (momento.date() + timedelta(days=dias)).isoformat()
        futuras.append({**horario, "fecha": futura, "tipo_registro": "horario"})
    proxima_clase = min(futuras, key=lambda e: (e["fecha"], e["inicio"]), default=None)
    futuras += [{**r, "tipo_registro": "reserva"} for r in reservas if r["aula"] == aula
                and r["estado"] == "activa" and (r["fecha"], r["inicio"]) > (fecha, hora)]
    proxima = min(futuras, key=lambda e: (e["fecha"], e["inicio"]), default=None)
    liberacion, restantes = None, 0
    if actual:
        liberacion = actual["fin"]
        # Si hay clases consecutivas, el aula no queda libre entre ellas.
        for evento in eventos:
            if evento["inicio"] <= liberacion < evento["fin"]:
                liberacion = evento["fin"]
        fin_actual = datetime.fromisoformat(fecha + "T" + actual["fin"]).replace(tzinfo=ZONA)
        restantes = max(0, math.ceil((fin_actual - momento).total_seconds() / 60))
    pronto = actual and minutos(liberacion) - minutos(hora) <= 30
    return {"estado": "por_liberarse" if pronto else "ocupada" if actual else "disponible",
            "actual": actual, "liberacion": liberacion, "minutos_restantes": restantes,
            "proxima": proxima, "proxima_clase": proxima_clase}
