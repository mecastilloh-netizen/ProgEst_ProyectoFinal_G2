"""Pantallas HTML de AulaGest. Las reglas y el guardado se delegan a servicios."""
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
import archivos
import horarios
import listas
import monticulos
import servicios
import simulaciones

web = Blueprint("web", __name__)

CAMPOS = {
    "aulas": ("id", "nombre", "edificio", "piso", "capacidad", "tipo", "equipamiento"),
    "horarios": ("aula", "asignatura", "docente", "dia", "inicio", "fin", "asistentes"),
    "reservas": ("motivo", "aula", "docente", "fecha", "inicio", "fin", "asistentes"),
    "docentes": ("id", "nombre", "especialidad"),
    "asignaturas": ("id", "nombre", "creditos"),
    "edificios": ("id", "nombre", "descripcion"),
    "solicitudes": ("motivo", "prioridad", "aula", "docente", "fecha", "inicio", "fin", "asistentes"),
}
ETIQUETAS = {"id": "Código", "dia": "Día", "creditos": "Créditos", "descripcion": "Descripción",
             "inicio": "Hora inicial", "fin": "Hora final", "orden": "Orden de llegada", "accion": "Acción"}
NUMEROS = {"dia", "prioridad", "capacidad", "piso", "asistentes", "creditos"}


def sistema():
    return current_app.config["SISTEMA"]


@web.app_context_processor
def contexto():
    datos = sistema()["datos"]
    opciones = {}
    for campo, tabla in (("aula", "aulas"), ("edificio", "edificios"), ("docente", "docentes"),
                         ("asignatura", "asignaturas")):
        opciones[campo] = {r["id"]: f"{r['id']} · {r['nombre']}" for r in datos[tabla]}
    opciones["dia"] = dict(enumerate(horarios.DIAS[:6]))
    opciones["prioridad"] = monticulos.PRIORIDADES
    return dict(opciones=opciones, campos=CAMPOS, numeros=NUMEROS, etiquetas=ETIQUETAS,
                ahora=horarios.ahora_nicaragua())


def volver(tipo, mensaje):
    flash(mensaje)
    return redirect(url_for("web.listado", tipo=tipo), code=303)


def filtros():
    return {k: v for k, v in request.args.items() if v.strip()}


@web.get("/")
def inicio():
    return render_template("index.html", titulo="Resumen del campus", resumen=servicios.resumen(sistema()),
                           aulas=servicios.consultar_aulas(sistema(), filtros()))


@web.get("/web/index.html")
def antiguo_inicio():
    return redirect(url_for("web.inicio"))


@web.route("/pruebas", methods=["GET", "POST"])
def pruebas_registros():
    fecha = request.form.get("fecha", horarios.ahora_nicaragua().date().isoformat())
    cantidad = request.form.get("ejemplo", request.form.get("cantidad", "10"))
    error = None
    if request.method == "POST":
        try:
            identificador = simulaciones.ejecutar(sistema(), cantidad, fecha)
        except ValueError as exc:
            error = str(exc)
        except OSError:
            abort(503, "No se pudo guardar el informe de prueba. Revisa el espacio y los permisos de la carpeta.")
        else:
            return redirect(url_for("web.informe_prueba", identificador=identificador), code=303)
    return render_template("pruebas.html", titulo="Pruebas de registros", fecha=fecha, cantidad=cantidad,
                           informes=simulaciones.listar_informes(sistema()), error=error), 400 if error else 200


@web.get("/pruebas/<identificador>")
def informe_prueba(identificador):
    informe = archivos.cargar_datos(simulaciones.ruta_informe(sistema(), identificador))
    por_pagina = 25
    paginas = (informe["cantidad"] + por_pagina - 1) // por_pagina
    pagina = request.args.get("pagina", 1, type=int)
    if not 1 <= pagina <= paginas:
        abort(404)
    filas = informe["resultados"][(pagina - 1) * por_pagina:pagina * por_pagina]
    return render_template("informe_prueba.html", titulo="Resultado de la prueba", informe=informe,
                           identificador=identificador, filas=filas, pagina=pagina, paginas=paginas)


@web.post("/pruebas/<identificador>/eliminar")
def eliminar_prueba(identificador):
    ruta = simulaciones.ruta_informe(sistema(), identificador)
    try:
        ruta.unlink()
    except OSError:
        abort(503, "No se pudo eliminar el informe de prueba. Revisa los permisos de la carpeta.")
    flash("Se eliminó el archivo de esta prueba.")
    return redirect(url_for("web.pruebas_registros"), code=303)


@web.get("/<tipo>")
def listado(tipo):
    datos = sistema()["datos"]
    parametros = filtros()
    if tipo == "aulas":
        return render_template("index.html", titulo="Aulas", aulas=servicios.consultar_aulas(sistema(), parametros))
    if tipo == "historial":
        return render_template("listado.html", titulo="Historial", tipo=tipo, columnas=("fecha", "accion", "detalle"),
                               filas=listas.consultar_movimientos(datos[tipo], parametros.get("q", "")))
    if tipo not in CAMPOS:
        abort(404)
    filas, columnas = datos[tipo], CAMPOS[tipo]
    extra = {}
    if tipo == "horarios":
        aula = parametros.get("aula", datos["aulas"][0]["id"] if datos["aulas"] else "")
        filas = sorted((h for h in filas if h["aula"] == aula), key=lambda h: (h["inicio"], h["dia"]))
        semana = {}
        for clase in filas:
            bloque = semana.setdefault(clase["inicio"][:2] + ":00", {})
            bloque.setdefault(clase["dia"], []).append(clase)
        extra.update(semana=semana, aula=aula)
    elif tipo == "reservas":
        if parametros.get("estado"):
            filas = [r for r in filas if r["estado"] == parametros["estado"]]
        filas = sorted(filas, key=lambda r: (r["fecha"], r["inicio"]))
        columnas += ("estado",)
    elif tipo == "solicitudes":
        cola = servicios.listar_solicitudes(sistema())
        filas = cola["pendientes"] + cola["atendidas"]
        columnas += ("orden", "estado", "resultado")
        extra["proxima"] = cola["proxima"]
    elif tipo == "edificios":
        extra["mapa"] = servicios.consultar_ruta(sistema(), parametros)
    return render_template("listado.html", titulo=tipo.capitalize(), tipo=tipo,
                           filas=filas, columnas=columnas, **extra)


@web.get("/aulas/<codigo>/detalle")
def detalle(codigo):
    datos = sistema()["datos"]
    aula = servicios.obtener(sistema(), "aulas", codigo)
    estado = horarios.disponibilidad(codigo, horarios.ahora_nicaragua(), datos["horarios"], datos["reservas"])
    return render_template("detalle.html", titulo=aula["nombre"], aula=aula, estado=estado,
                           clases=sorted((h for h in datos["horarios"] if h["aula"] == codigo),
                                         key=lambda h: (h["dia"], h["inicio"])),
                           reservas=[r for r in datos["reservas"] if r["aula"] == codigo and r["estado"] == "activa"])


def guardar(tipo, codigo):
    entrada = {c: request.form.get(c, "").strip() for c in CAMPOS[tipo]}
    for campo in NUMEROS.intersection(entrada):
        try:
            entrada[campo] = int(entrada[campo])
        except ValueError:
            raise ValueError(f"{campo.capitalize()} debe ser un entero.") from None
    if tipo == "aulas":
        entrada["equipamiento"] = [v.strip() for v in entrada["equipamiento"].split(",") if v.strip()]
        return servicios.guardar_aula(sistema(), entrada, codigo)
    if tipo in ("horarios", "reservas"):
        return servicios.guardar_evento(sistema(), tipo, entrada, codigo)
    if tipo == "solicitudes":
        return servicios.crear_solicitud(sistema(), entrada)
    return servicios.guardar_catalogo(sistema(), tipo, entrada, codigo)


@web.route("/<tipo>/nuevo", methods=["GET", "POST"])
@web.route("/<tipo>/<codigo>/editar", methods=["GET", "POST"])
def formulario(tipo, codigo=None):
    if tipo not in CAMPOS or (codigo and tipo == "solicitudes"):
        abort(404)
    valores = dict(servicios.obtener(sistema(), tipo, codigo)) if codigo else {}
    if tipo == "aulas":
        valores["equipamiento"] = ", ".join(valores.get("equipamiento", []))
    error, estado = None, 200
    if request.method == "POST":
        valores = request.form
        try:
            guardar(tipo, codigo)
            return volver(tipo, "Registro guardado.")
        except (ValueError, LookupError, FileExistsError) as exc:
            error = str(exc)
            estado = 409 if isinstance(exc, FileExistsError) else 400
    titulo = ("Editar" if codigo else "Registrar") + " · " + tipo.capitalize()
    return render_template("formulario.html", titulo=titulo, tipo=tipo, codigo=codigo,
                           valores=valores, error=error), estado


@web.route("/<tipo>/<codigo>/eliminar", methods=["GET", "POST"])
def eliminar(tipo, codigo):
    if tipo not in CAMPOS or tipo == "solicitudes":
        abort(404)
    registro = servicios.obtener(sistema(), tipo, codigo)
    if request.method == "POST":
        if tipo == "reservas":
            servicios.cancelar_reserva(sistema(), codigo)
            return volver(tipo, "Reserva cancelada.")
        servicios.eliminar_registro(sistema(), tipo, codigo)
        return volver(tipo, "Registro eliminado.")
    titulo = "Cancelar reserva" if tipo == "reservas" else "Eliminar registro"
    return render_template("confirmar.html", titulo=titulo, tipo=tipo, registro=registro)


@web.post("/solicitudes/atender")
def atender():
    solicitud = servicios.procesar_solicitud(sistema())
    return volver("solicitudes", f"Solicitud {solicitud['estado']}. {solicitud['resultado']}")


@web.post("/edificios/conexiones")
def conexion():
    accion = request.form.get("accion")
    if accion not in ("conectar", "desconectar"):
        abort(400)
    servicios.modificar_conexion(sistema(), request.form, eliminar=accion == "desconectar")
    return volver("edificios", "Conexión actualizada.")
