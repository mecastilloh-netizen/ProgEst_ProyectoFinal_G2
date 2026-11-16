"""Reglas del sistema: validaciones, CRUD, índices y consultas; sin lógica HTTP."""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import re
import arboles
import archivos
import grafos
import horarios
import listas
import monticulos


def iniciar_sistema(carpeta):
    carpeta = Path(carpeta)
    archivos.crear_archivos_si_no_existen(carpeta, archivos.datos_iniciales())
    datos = archivos.cargar_todo(carpeta)
    validar_referencias(datos)
    sistema = {"carpeta": carpeta, "datos": datos}
    sincronizar_indices(sistema)
    return sistema


def validar_referencias(datos):
    ids = {n: {r["id"] for r in registros} for n, registros in datos.items()}
    for aula in datos["aulas"]:
        if aula["edificio"] not in ids["edificios"]:
            raise ValueError(f"El aula {aula['id']} referencia un edificio inexistente; revise los JSON.")
    for edificio in datos["edificios"]:
        if any(c not in ids["edificios"] or c == edificio["id"] for c in edificio["conexiones"]):
            raise ValueError("Una conexión de edificios es inválida; revise edificios.json.")
    for nombre in ("horarios", "reservas", "solicitudes"):
        for registro in datos[nombre]:
            for campo, coleccion in (("aula", "aulas"), ("docente", "docentes"), ("asignatura", "asignaturas")):
                if campo in registro and registro[campo] not in ids[coleccion]:
                    raise ValueError(f"{nombre}: referencia {campo} inexistente en {registro['id']}.")


def sincronizar_indices(sistema):
    datos = sistema["datos"]
    sistema["arbol"] = arboles.reconstruir_arbol(datos["aulas"])
    sistema["grafo"] = grafos.construir_grafo(datos["edificios"], datos["aulas"])
    sistema["monticulo"] = monticulos.reconstruir_monticulo(datos["solicitudes"])


def confirmar(sistema, nuevos, accion, detalle, cola_actualizada=None):
    # Se prepara una copia y se escribe antes de cambiar el estado en memoria.
    historial = list(sistema["datos"]["historial"])
    listas.agregar_registro(historial, accion, detalle, horarios.ahora_nicaragua().isoformat())
    cambios = {**nuevos, "historial": historial}
    archivos.guardar_cambios(sistema["carpeta"], cambios)
    sistema["datos"].update(cambios)
    if "aulas" in nuevos:
        sistema["arbol"] = arboles.reconstruir_arbol(sistema["datos"]["aulas"])
    if "aulas" in nuevos or "edificios" in nuevos:
        sistema["grafo"] = grafos.construir_grafo(sistema["datos"]["edificios"], sistema["datos"]["aulas"])
    if "solicitudes" in nuevos:
        sistema["monticulo"] = (cola_actualizada if cola_actualizada is not None else
                                monticulos.reconstruir_monticulo(sistema["datos"]["solicitudes"]))


def texto(datos, campo, limite=120):
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
        raise ValueError(f"{campo}: escriba un texto de 1 a {limite} caracteres.")
    return valor.strip()


def entero(datos, campo, minimo, maximo):
    valor = datos.get(campo)
    if type(valor) is not int or not minimo <= valor <= maximo:
        raise ValueError(f"{campo}: se necesita un entero entre {minimo} y {maximo}.")
    return valor


def codigo(datos):
    valor = texto(datos, "id", 24).upper()
    if not re.fullmatch(r"[A-Z0-9_-]+", valor):
        raise ValueError("El código solo admite letras, números, guiones y guiones bajos.")
    return valor


def obtener(sistema, coleccion, identificador):
    registro = (arboles.buscar_aula(sistema["arbol"], identificador) if coleccion == "aulas" else
                next((r for r in sistema["datos"][coleccion] if r["id"] == identificador), None))
    if registro is None:
        raise LookupError(f"No existe {identificador} en {coleccion}.")
    return registro


def validar_aula(sistema, entrada):
    edificio = texto(entrada, "edificio")
    obtener(sistema, "edificios", edificio)
    equipamiento = entrada.get("equipamiento", [])
    if not isinstance(equipamiento, list) or len(equipamiento) > 20 or any(
            not isinstance(e, str) or not e.strip() or len(e) > 60 for e in equipamiento):
        raise ValueError("Equipamiento debe ser una lista de hasta 20 textos cortos.")
    return {"id": codigo(entrada), "nombre": texto(entrada, "nombre"), "edificio": edificio,
            "piso": entero(entrada, "piso", 0, 100), "capacidad": entero(entrada, "capacidad", 1, 2000),
            "tipo": texto(entrada, "tipo", 50), "equipamiento": [e.strip() for e in equipamiento]}


def guardar_aula(sistema, entrada, identificador=None):
    aula = validar_aula(sistema, entrada)
    if identificador:
        obtener(sistema, "aulas", identificador)
        if aula["id"] != identificador:
            raise ValueError("El código del aula no puede cambiarse; conserva sus referencias.")
        for nombre in ("horarios", "reservas", "solicitudes"):
            if any(r["aula"] == identificador and r.get("estado") not in ("cancelada", "rechazada")
                   and r["asistentes"] > aula["capacidad"] for r in sistema["datos"][nombre]):
                raise ValueError("La capacidad sería insuficiente para una actividad asociada.")
    elif arboles.buscar_aula(sistema["arbol"], aula["id"]):
        raise FileExistsError("Ya existe un aula con ese código.")
    registros = [r for r in sistema["datos"]["aulas"] if r["id"] != identificador] + [aula]
    confirmar(sistema, {"aulas": registros}, "Aula actualizada" if identificador else "Aula creada", aula["id"])
    return aula


def eliminar_registro(sistema, coleccion, identificador):
    obtener(sistema, coleccion, identificador)
    campo = {"aulas": "aula", "docentes": "docente", "asignaturas": "asignatura", "edificios": "edificio"}.get(coleccion)
    if campo:
        for nombre in ("aulas", "horarios", "reservas", "solicitudes"):
            if any(r.get(campo) == identificador for r in sistema["datos"][nombre]):
                raise FileExistsError(f"No se puede eliminar: existen registros asociados en {nombre}.")
    if coleccion == "edificios" and any(identificador in e["conexiones"] for e in sistema["datos"]["edificios"]):
        raise FileExistsError("El edificio tiene conexiones. Retírelas antes de eliminarlo.")
    registros = [r for r in sistema["datos"][coleccion] if r["id"] != identificador]
    confirmar(sistema, {coleccion: registros}, "Registro eliminado", f"{coleccion}: {identificador}")
    return {"mensaje": "Registro eliminado correctamente."}


def guardar_catalogo(sistema, coleccion, entrada, identificador=None):
    registro = {"id": codigo(entrada), "nombre": texto(entrada, "nombre")}
    if coleccion == "docentes":
        registro["especialidad"] = texto(entrada, "especialidad")
    elif coleccion == "asignaturas":
        registro["creditos"] = entero(entrada, "creditos", 1, 20)
    else:
        registro.update(descripcion=texto(entrada, "descripcion", 300), conexiones=[])
        if identificador:
            registro["conexiones"] = obtener(sistema, coleccion, identificador)["conexiones"]
    if identificador:
        obtener(sistema, coleccion, identificador)
        if registro["id"] != identificador:
            raise ValueError("El código no puede cambiarse.")
    elif any(r["id"] == registro["id"] for r in sistema["datos"][coleccion]):
        raise FileExistsError("El código ya está registrado.")
    registros = [r for r in sistema["datos"][coleccion] if r["id"] != identificador] + [registro]
    confirmar(sistema, {coleccion: registros}, "Catálogo actualizado", f"{coleccion}: {registro['nombre']}")
    return registro


def validar_evento(sistema, entrada, tipo):
    aula = obtener(sistema, "aulas", texto(entrada, "aula"))
    docente = obtener(sistema, "docentes", texto(entrada, "docente"))
    evento = {"aula": aula["id"], "docente": docente["id"], "inicio": texto(entrada, "inicio", 5),
              "fin": texto(entrada, "fin", 5), "asistentes": entero(entrada, "asistentes", 1, 2000)}
    horarios.validar_intervalo(evento["inicio"], evento["fin"])
    if evento["asistentes"] > aula["capacidad"]:
        raise ValueError(f"Capacidad insuficiente: el aula admite {aula['capacidad']} personas.")
    if tipo == "horarios":
        evento["dia"] = entero(entrada, "dia", 0, 5)
        evento["asignatura"] = obtener(sistema, "asignaturas", texto(entrada, "asignatura"))["id"]
    else:
        evento["fecha"] = horarios.validar_fecha(entrada.get("fecha")).isoformat()
        evento["motivo"] = texto(entrada, "motivo", 300)
    return evento


def comprobar_conflicto(sistema, evento, excluir=None):
    conflictos = horarios.detectar_conflictos(evento, sistema["datos"]["horarios"], sistema["datos"]["reservas"], excluir)
    if conflictos:
        c = conflictos[0]
        raise FileExistsError(f"El aula {evento['aula']} no está disponible: coincide con {c['tipo_registro']} {c['inicio']}–{c['fin']}.")


def guardar_evento(sistema, tipo, entrada, identificador=None):
    anterior = obtener(sistema, tipo, identificador) if identificador else None
    if anterior and anterior.get("estado") == "cancelada":
        raise ValueError("Una reserva cancelada no se puede modificar.")
    evento = validar_evento(sistema, entrada, tipo)
    comprobar_conflicto(sistema, evento, ("horario" if tipo == "horarios" else "reserva", identificador))
    evento["id"] = identificador or uuid4().hex[:12]
    if tipo == "reservas":
        evento["estado"] = "activa"
        if anterior and "solicitud" in anterior:
            evento["solicitud"] = anterior["solicitud"]
    registros = [r for r in sistema["datos"][tipo] if r["id"] != identificador] + [evento]
    confirmar(sistema, {tipo: registros}, "Actividad actualizada" if identificador else "Actividad creada",
              f"{tipo}: {evento['aula']} · {evento['inicio']}–{evento['fin']}")
    return evento


def cancelar_reserva(sistema, identificador):
    reserva = {**obtener(sistema, "reservas", identificador), "estado": "cancelada"}
    if obtener(sistema, "reservas", identificador)["estado"] == "cancelada":
        return reserva
    registros = [reserva if r["id"] == identificador else r for r in sistema["datos"]["reservas"]]
    confirmar(sistema, {"reservas": registros}, "Reserva cancelada", identificador)
    return reserva


def crear_solicitud(sistema, entrada):
    solicitud = validar_evento(sistema, entrada, "solicitudes")
    solicitud.update(id=uuid4().hex[:12], estado="pendiente", prioridad=entero(entrada, "prioridad", 1, 5),
                     orden=max((s["orden"] for s in sistema["datos"]["solicitudes"]), default=0)+1)
    registros = sistema["datos"]["solicitudes"] + [solicitud]
    cola = list(sistema["monticulo"])
    monticulos.agregar_solicitud(cola, solicitud)
    confirmar(sistema, {"solicitudes": registros}, "Solicitud recibida", solicitud["motivo"], cola)
    return solicitud


def listar_solicitudes(sistema):
    por_id = {s["id"]: s for s in sistema["datos"]["solicitudes"]}
    pendientes = [por_id[i] for i in monticulos.mostrar_pendientes(sistema["monticulo"])]
    return {"pendientes": pendientes, "atendidas": [s for s in por_id.values() if s["estado"] != "pendiente"],
            "proxima": monticulos.consultar_proxima(sistema["monticulo"])}


def procesar_solicitud(sistema):
    # Extraer de una copia: un error al guardar no consume la solicitud en memoria.
    cola = list(sistema["monticulo"])
    identificador = monticulos.atender_solicitud(cola)
    if not identificador:
        raise LookupError("No hay solicitudes pendientes.")
    solicitud = dict(obtener(sistema, "solicitudes", identificador))
    cambios = {}
    try:
        evento = validar_evento(sistema, solicitud, "reservas")
        comprobar_conflicto(sistema, evento)
    except (ValueError, LookupError, FileExistsError) as error:
        solicitud.update(estado="rechazada", resultado=str(error))
    else:
        reserva = {**evento, "id": "RS-" + identificador, "estado": "activa", "solicitud": identificador}
        cambios["reservas"] = sistema["datos"]["reservas"] + [reserva]
        solicitud.update(estado="aprobada", resultado="Reserva creada: " + reserva["id"])
    cambios["solicitudes"] = [solicitud if s["id"] == identificador else s for s in sistema["datos"]["solicitudes"]]
    confirmar(sistema, cambios, "Solicitud " + solicitud["estado"], solicitud["motivo"], cola)
    return solicitud


def momento_consulta(parametros):
    ahora = horarios.ahora_nicaragua()
    fecha = horarios.validar_fecha(parametros.get("fecha", ahora.date().isoformat()))
    hora = parametros.get("hora", ahora.strftime("%H:%M"))
    horarios.minutos(hora)
    return datetime.fromisoformat(fecha.isoformat() + "T" + hora).replace(tzinfo=horarios.ZONA)


def consultar_aulas(sistema, parametros):
    momento = momento_consulta(parametros)
    capacidad = parametros.get("capacidad", "0")
    piso = parametros.get("piso", "")
    if not str(capacidad).isdigit() or (piso and not str(piso).isdigit()):
        raise ValueError("Capacidad y piso deben ser números enteros no negativos.")
    inicio, fin = parametros.get("inicio"), parametros.get("fin")
    if inicio or fin:
        horarios.validar_intervalo(inicio, fin)
    resultado = []
    for aula in arboles.recorrido_inorden(sistema["arbol"]):
        if parametros.get("edificio") and aula["edificio"] != parametros["edificio"]:
            continue
        if piso and aula["piso"] != int(piso) or aula["capacidad"] < int(capacidad):
            continue
        if parametros.get("q", "").casefold() not in (aula["id"] + " " + aula["nombre"]).casefold():
            continue
        estado = horarios.disponibilidad(aula["id"], momento, sistema["datos"]["horarios"], sistema["datos"]["reservas"])
        filtro = parametros.get("estado")
        if filtro and estado["estado"] != filtro and not (filtro == "ocupada" and estado["estado"] == "por_liberarse"):
            continue
        if inicio and horarios.detectar_conflictos({"aula": aula["id"], "fecha": momento.date().isoformat(),
                    "inicio": inicio, "fin": fin}, sistema["datos"]["horarios"], sistema["datos"]["reservas"]):
            continue
        resultado.append({**aula, **estado})
    return resultado


def resumen(sistema):
    aulas = consultar_aulas(sistema, {})
    fecha = horarios.ahora_nicaragua().date().isoformat()
    disponibles = sum(a["estado"] == "disponible" for a in aulas)
    return {"total": len(aulas), "disponibles": disponibles, "ocupadas": len(aulas)-disponibles,
            "reservas_hoy": sum(r["fecha"] == fecha and r["estado"] == "activa" for r in sistema["datos"]["reservas"]),
            "pendientes": len(sistema["monticulo"]), "ahora": horarios.ahora_nicaragua().isoformat(),
            "zona_horaria": "America/Managua", "recientes": listas.operaciones_recientes(sistema["datos"]["historial"])}


def consultar_ruta(sistema, parametros):
    grafo = sistema["grafo"]
    origen, destino = parametros.get("origen"), parametros.get("destino")
    if (origen or destino) and (origen not in grafo or destino not in grafo):
        raise LookupError("Seleccione un origen y un destino existentes.")
    return {"vertices": list(grafo), "conexiones": grafos.mostrar_conexiones(grafo),
            "vecinos": grafos.consultar_vecinos(grafo, origen) if origen else [],
            "ruta": grafos.buscar_ruta_bfs(grafo, origen, destino) if origen and destino else []}


def modificar_conexion(sistema, entrada, eliminar=False):
    origen, destino = texto(entrada, "origen"), texto(entrada, "destino")
    obtener(sistema, "edificios", origen)
    obtener(sistema, "edificios", destino)
    if origen == destino:
        raise ValueError("Seleccione edificios diferentes.")
    edificios = deepcopy(sistema["datos"]["edificios"])
    grafo = deepcopy(sistema["grafo"])
    operacion = grafos.eliminar_conexion if eliminar else grafos.conectar_vertices
    operacion(grafo, "Edificio " + origen, "Edificio " + destino)
    for edificio in edificios:
        otro = destino if edificio["id"] == origen else origen if edificio["id"] == destino else None
        if otro:
            edificio["conexiones"] = [vecino.removeprefix("Edificio ") for vecino in
                grafos.consultar_vecinos(grafo, "Edificio " + edificio["id"]) if vecino.startswith("Edificio ")]
    confirmar(sistema, {"edificios": edificios}, "Conexión eliminada" if eliminar else "Edificios conectados", f"{origen} ↔ {destino}")
    return consultar_ruta(sistema, {})
