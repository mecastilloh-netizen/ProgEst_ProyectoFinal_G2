"""Adaptador Flask: rutas HTTP delgadas que delegan las reglas a servicios.py."""
from pathlib import Path
from threading import RLock
from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException
import servicios
import listas


def crear_app(carpeta_datos=None):
    base = Path(__file__).resolve().parent
    app = Flask(__name__, static_folder=str(base / "web"), static_url_path="/web")
    app.json.ensure_ascii = False
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    sistema = servicios.iniciar_sistema(carpeta_datos or base / "datos")
    app.config["SISTEMA"] = sistema
    bloqueo = RLock()

    @app.before_request
    def proteger_estado():
        # Un proceso local; evita que dos peticiones pierdan cambios entre sí.
        bloqueo.acquire()
        g.bloqueado = True
        if request.path.startswith("/api/") and request.method in ("POST", "PUT", "DELETE"):
            if sistema.get("error_escritura"):
                return jsonify(error="Guardado interrumpido. Reinicie el servidor para recuperar el diario JSON."), 503
            origen = request.headers.get("Origin")
            if origen and origen.rstrip("/") != request.host_url.rstrip("/"):
                return jsonify(error="Las modificaciones deben realizarse desde AulaGest local."), 403

    @app.teardown_request
    def liberar_estado(error=None):
        if getattr(g, "bloqueado", False):
            bloqueo.release()

    @app.after_request
    def cabeceras(respuesta):
        if request.path.startswith("/api/"):
            respuesta.headers["Cache-Control"] = "no-store"
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        return respuesta

    @app.errorhandler(Exception)
    def error_json(error):
        if isinstance(error, FileExistsError):
            estado = 409
        elif isinstance(error, LookupError):
            estado = 404
        elif isinstance(error, ValueError):
            estado = 400
        elif isinstance(error, HTTPException):
            return jsonify(error=error.description), error.code
        elif isinstance(error, OSError):
            sistema["error_escritura"] = True
            app.logger.exception("Error al guardar JSON")
            return jsonify(error="No se pudo guardar en disco. Revise permisos y espacio; reinicie para recuperar cambios."), 503
        else:
            app.logger.exception("Error inesperado")
            return jsonify(error="Error interno. Consulte la terminal del servidor."), 500
        return jsonify(error=str(error)), estado

    def entrada():
        datos = request.get_json()
        if not isinstance(datos, dict):
            raise ValueError("El cuerpo JSON debe ser un objeto.")
        return datos

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/resumen")
    def resumen():
        return jsonify(servicios.resumen(sistema))

    @app.route("/api/aulas", methods=["GET", "POST"])
    def aulas():
        if request.method == "POST":
            return jsonify(servicios.guardar_aula(sistema, entrada())), 201
        return jsonify(servicios.consultar_aulas(sistema, request.args))

    @app.route("/api/aulas/<identificador>", methods=["GET", "PUT", "DELETE"])
    def aula(identificador):
        if request.method == "PUT":
            return jsonify(servicios.guardar_aula(sistema, entrada(), identificador))
        if request.method == "DELETE":
            return jsonify(servicios.eliminar_registro(sistema, "aulas", identificador))
        servicios.obtener(sistema, "aulas", identificador)
        return jsonify(next(a for a in servicios.consultar_aulas(sistema, {}) if a["id"] == identificador))

    @app.route("/api/horarios", methods=["GET", "POST"])
    @app.route("/api/reservas", methods=["GET", "POST"])
    def eventos():
        tipo = request.path.rsplit("/", 1)[-1]
        if request.method == "POST":
            return jsonify(servicios.guardar_evento(sistema, tipo, entrada())), 201
        registros = sistema["datos"][tipo]
        for campo in ("aula", "fecha", "estado"):
            if request.args.get(campo):
                registros = [r for r in registros if r.get(campo) == request.args[campo]]
        return jsonify(registros)

    @app.route("/api/horarios/<identificador>", methods=["PUT", "DELETE"])
    @app.route("/api/reservas/<identificador>", methods=["PUT", "DELETE"])
    def evento(identificador):
        tipo = request.path.split("/")[2]
        if request.method == "PUT":
            return jsonify(servicios.guardar_evento(sistema, tipo, entrada(), identificador))
        if tipo == "reservas":
            return jsonify(servicios.cancelar_reserva(sistema, identificador))
        return jsonify(servicios.eliminar_registro(sistema, tipo, identificador))

    @app.route("/api/docentes", methods=["GET", "POST"])
    @app.route("/api/asignaturas", methods=["GET", "POST"])
    @app.route("/api/edificios", methods=["GET", "POST"])
    def catalogos():
        tipo = request.path.rsplit("/", 1)[-1]
        if request.method == "POST":
            return jsonify(servicios.guardar_catalogo(sistema, tipo, entrada())), 201
        return jsonify(sistema["datos"][tipo])

    @app.route("/api/docentes/<identificador>", methods=["PUT", "DELETE"])
    @app.route("/api/asignaturas/<identificador>", methods=["PUT", "DELETE"])
    @app.route("/api/edificios/<identificador>", methods=["PUT", "DELETE"])
    def catalogo(identificador):
        tipo = request.path.split("/")[2]
        if request.method == "PUT":
            return jsonify(servicios.guardar_catalogo(sistema, tipo, entrada(), identificador))
        return jsonify(servicios.eliminar_registro(sistema, tipo, identificador))

    @app.route("/api/solicitudes", methods=["GET", "POST"])
    def solicitudes():
        if request.method == "POST":
            return jsonify(servicios.crear_solicitud(sistema, entrada())), 201
        return jsonify(servicios.listar_solicitudes(sistema))

    @app.post("/api/solicitudes/atender")
    def atender():
        return jsonify(servicios.procesar_solicitud(sistema))

    @app.get("/api/rutas")
    def rutas():
        return jsonify(servicios.consultar_ruta(sistema, request.args))

    @app.route("/api/conexiones", methods=["POST", "DELETE"])
    def conexiones():
        return jsonify(servicios.modificar_conexion(sistema, entrada(), request.method == "DELETE"))

    @app.get("/api/historial")
    def historial():
        return jsonify(listas.consultar_movimientos(sistema["datos"]["historial"], request.args.get("q", "")))

    return app
