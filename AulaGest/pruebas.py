"""Pruebas unittest aisladas: estructuras, reglas, API y persistencia temporal."""
import json
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import arboles
import archivos
import grafos
import horarios
import listas
import monticulos
from servidor import crear_app

# FunctionTestCase permite usar unittest sin definir clases propias.
comprobar = unittest.TestCase()


@contextmanager
def entorno():
    with tempfile.TemporaryDirectory(prefix="aulagest-pruebas-") as carpeta:
        app = crear_app(carpeta)
        app.testing = True
        yield app.test_client(), Path(carpeta), app


def aula_prueba():
    return {"id": "Z999", "nombre": "Aula temporal", "edificio": "A", "piso": 3,
            "capacidad": 40, "tipo": "Teórica", "equipamiento": ["Pizarra"]}


def reserva_prueba(**cambios):
    return {"aula": "A101", "docente": "D01", "fecha": "2030-01-06", "inicio": "10:00",
            "fin": "11:00", "motivo": "Prueba temporal", "asistentes": 20, **cambios}


def test_insertar_buscar_arbol():
    raiz = None
    for codigo in ["B102", "A101", "C201", "B101"]:
        raiz = arboles.insertar_aula(raiz, {"id": codigo})
    comprobar.assertEqual(arboles.buscar_aula(raiz, "A101"), {"id": "A101"})
    comprobar.assertIsNone(arboles.buscar_aula(raiz, "INEXISTENTE"))
    comprobar.assertEqual([a["id"] for a in arboles.recorrido_inorden(raiz)], ["A101", "B101", "B102", "C201"])


def test_reconstruir_arbol():
    aulas = [{"id": f"A{i:04}"} for i in range(1500)]
    raiz = arboles.reconstruir_arbol(aulas)
    comprobar.assertEqual(len(arboles.recorrido_inorden(raiz)), 1500)
    comprobar.assertEqual(arboles.buscar_aula(raiz, "A1499"), aulas[-1])


def test_grafo_y_bfs():
    grafo = {}
    grafos.agregar_vertice(grafo, "A")
    for a, b in [("A", "B"), ("B", "C"), ("A", "D"), ("D", "C")]:
        grafos.conectar_vertices(grafo, a, b)
    comprobar.assertIn("A", grafos.consultar_vecinos(grafo, "B"))
    comprobar.assertEqual(len(grafos.mostrar_conexiones(grafo)), 4)
    comprobar.assertEqual(grafos.buscar_ruta_bfs(grafo, "A", "C"), ["A", "B", "C"])
    comprobar.assertEqual(grafos.buscar_ruta_bfs(grafo, "A", "A"), ["A"])
    comprobar.assertEqual(grafos.buscar_ruta_bfs(grafo, "X", "C"), [])
    grafos.eliminar_conexion(grafo, "A", "B")
    comprobar.assertNotIn("A", grafos.consultar_vecinos(grafo, "B"))
    comprobar.assertEqual(grafos.buscar_ruta_bfs(grafo, "A", "C"), ["A", "D", "C"])


def test_monticulo_prioridad_fifo():
    cola = []
    for identificador, prioridad, orden in [("S1", 3, 1), ("S2", 1, 2), ("S3", 1, 3)]:
        monticulos.agregar_solicitud(cola, {"id": identificador, "prioridad": prioridad, "orden": orden})
    comprobar.assertEqual(monticulos.consultar_proxima(cola), "S2")
    comprobar.assertEqual(monticulos.mostrar_pendientes(cola), ["S2", "S3", "S1"])
    comprobar.assertEqual([monticulos.atender_solicitud(cola) for _ in range(3)], ["S2", "S3", "S1"])
    comprobar.assertIsNone(monticulos.atender_solicitud(cola))


def test_listas_historial():
    historial = []
    listas.agregar_registro(historial, "Crear", "Aula A101", "2030-01-01")
    listas.agregar_registro(historial, "Editar", "Aula B101", "2030-01-02")
    comprobar.assertEqual(len(listas.filtrar_registros(historial, "a101")), 1)
    comprobar.assertEqual(listas.operaciones_recientes(historial, 1)[0]["accion"], "Editar")
    comprobar.assertEqual(listas.operaciones_recientes(historial, 0), [])


def test_intervalos_y_conflictos():
    comprobar.assertTrue(horarios.se_superponen("08:00", "10:00", "09:00", "11:00"))
    comprobar.assertFalse(horarios.se_superponen("08:00", "10:00", "10:00", "11:00"))
    comprobar.assertTrue(horarios.se_superponen("08:00", "12:00", "09:00", "10:00"))
    for inicio, fin in [("10:00", "10:00"), ("11:00", "10:00"), ("25:00", "26:00"), ("8:00", "09:00")]:
        with comprobar.assertRaises(ValueError):
            horarios.validar_intervalo(inicio, fin)
    h = {"id": "H1", "dia": 0, "aula": "A101", "inicio": "08:00", "fin": "10:00"}
    comprobar.assertEqual(len(horarios.detectar_conflictos({**h, "inicio": "09:00"}, [h], [])), 1)
    comprobar.assertEqual(horarios.detectar_conflictos({**h, "dia": 1}, [h], []), [])
    comprobar.assertEqual(horarios.detectar_conflictos({**h, "aula": "B101"}, [h], []), [])


def test_disponibilidad_consecutiva_y_proxima():
    h = [{"id": "H1", "aula": "A101", "dia": 0, "inicio": "08:00", "fin": "09:00"},
         {"id": "H2", "aula": "A101", "dia": 0, "inicio": "09:00", "fin": "10:00"}]
    momento = datetime(2030, 1, 7, 8, 50, tzinfo=horarios.ZONA)
    estado = horarios.disponibilidad("A101", momento, h, [])
    comprobar.assertEqual(estado["liberacion"], "10:00")
    comprobar.assertEqual(estado["estado"], "ocupada")
    comprobar.assertEqual(estado["minutos_restantes"], 10)
    comprobar.assertEqual(estado["proxima"]["inicio"], "09:00")
    estado = horarios.disponibilidad("A101", momento.replace(hour=9, minute=45), h, [])
    comprobar.assertEqual(estado["estado"], "por_liberarse")
    estado = horarios.disponibilidad("A101", momento.replace(hour=10, minute=0), h, [])
    comprobar.assertEqual(estado["estado"], "disponible")
    comprobar.assertEqual(estado["proxima"]["fecha"], "2030-01-14")
    reserva = {"id": "R1", "aula": "A101", "fecha": "2030-01-07", "inicio": "11:00", "fin": "12:00", "estado": "activa"}
    estado = horarios.disponibilidad("A101", momento.replace(hour=10, minute=0), h, [reserva])
    comprobar.assertEqual(estado["proxima"]["id"], "R1")
    comprobar.assertEqual(estado["proxima_clase"]["fecha"], "2030-01-14")


def test_guardar_cargar_json():
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "aulas.json"
        archivos.guardar_datos(ruta, [aula_prueba()])
        comprobar.assertEqual(archivos.cargar_datos(ruta, "aulas"), [aula_prueba()])
        comprobar.assertIn("Teórica", ruta.read_text(encoding="utf-8"))
        comprobar.assertEqual(list(Path(carpeta).glob("*.tmp")), [])


def test_json_danado_se_conserva():
    with entorno() as (_, carpeta, __):
        ruta = carpeta / "aulas.json"
        ruta.write_text('{"dañado":', encoding="utf-8")
        original = ruta.read_bytes()
        with comprobar.assertRaisesRegex(ValueError, "conservado"):
            crear_app(carpeta)
        comprobar.assertEqual(ruta.read_bytes(), original)


def test_estructura_incorrecta_se_conserva():
    with entorno() as (_, carpeta, __):
        ruta = carpeta / "aulas.json"
        archivos.guardar_datos(ruta, [{"id": "A101"}])
        original = ruta.read_bytes()
        with comprobar.assertRaises(ValueError):
            crear_app(carpeta)
        comprobar.assertEqual(ruta.read_bytes(), original)


def test_api_y_frontend():
    with entorno() as (cliente, _, __):
        for endpoint in ("resumen", "aulas", "horarios", "reservas", "docentes", "asignaturas", "edificios", "solicitudes", "rutas", "historial"):
            respuesta = cliente.get("/api/" + endpoint)
            comprobar.assertEqual(respuesta.status_code, 200, endpoint)
            comprobar.assertTrue(respuesta.is_json)
        with cliente.get("/") as respuesta:
            comprobar.assertEqual(respuesta.status_code, 200)
        for recurso in ("js/app.js", "js/api.js", "js/aulas.js", "js/horarios.js", "js/reservas.js", "js/componentes.js", "css/estilos.css", "css/componentes.css", "css/responsive.css", "assets/icons/aulagest.svg"):
            with cliente.get("/web/" + recurso) as respuesta:
                comprobar.assertEqual(respuesta.status_code, 200, recurso)
        comprobar.assertEqual(cliente.get("/api/aulas/NO-EXISTE").status_code, 404)
        comprobar.assertEqual(cliente.get("/api/inexistente").status_code, 404)


def test_crud_aula_persistencia_arbol():
    with entorno() as (cliente, carpeta, _):
        comprobar.assertEqual(cliente.post("/api/aulas", json=aula_prueba()).status_code, 201)
        comprobar.assertEqual(cliente.post("/api/aulas", json=aula_prueba()).status_code, 409)
        comprobar.assertTrue(any(a["id"] == "Z999" for a in archivos.cargar_datos(carpeta / "aulas.json")))
        reiniciado = crear_app(carpeta).test_client()
        comprobar.assertEqual(reiniciado.get("/api/aulas/Z999").json["capacidad"], 40)
        comprobar.assertEqual(reiniciado.put("/api/aulas/Z999", json={**aula_prueba(), "capacidad": 45}).status_code, 200)
        comprobar.assertEqual(reiniciado.get("/api/aulas/Z999").json["capacidad"], 45)
        comprobar.assertEqual(reiniciado.delete("/api/aulas/Z999").status_code, 200)
        comprobar.assertEqual(reiniciado.get("/api/aulas/Z999").status_code, 404)
        comprobar.assertGreaterEqual(len(reiniciado.get("/api/historial").json), 3)


def test_proteger_referencias():
    with entorno() as (cliente, _, __):
        for tipo, codigo in [("aulas", "A101"), ("docentes", "D01"), ("asignaturas", "AS01"), ("edificios", "A")]:
            comprobar.assertEqual(cliente.delete(f"/api/{tipo}/{codigo}").status_code, 409)
        aula = cliente.get("/api/aulas/A101").json
        comprobar.assertEqual(cliente.put("/api/aulas/A101", json={**aula, "capacidad": 1}).status_code, 400)
        comprobar.assertEqual(cliente.put("/api/aulas/A101", json={**aula, "id": "A100"}).status_code, 400)


def test_reservas_persisten_y_cancelacion():
    with entorno() as (cliente, carpeta, _):
        respuesta = cliente.post("/api/reservas", json=reserva_prueba())
        comprobar.assertEqual(respuesta.status_code, 201)
        identificador = respuesta.json["id"]
        reiniciado = crear_app(carpeta).test_client()
        comprobar.assertIn(identificador, [r["id"] for r in reiniciado.get("/api/reservas").json])
        comprobar.assertEqual(reiniciado.post("/api/reservas", json=reserva_prueba()).status_code, 409)
        comprobar.assertEqual(reiniciado.put("/api/reservas/" + identificador, json=reserva_prueba(fin="12:00")).status_code, 200)
        comprobar.assertEqual(reiniciado.delete("/api/reservas/" + identificador).status_code, 200)
        comprobar.assertEqual(reiniciado.post("/api/reservas", json=reserva_prueba()).status_code, 201)
        comprobar.assertEqual(reiniciado.put("/api/reservas/" + identificador, json=reserva_prueba()).status_code, 400)


def test_conflicto_semanal_reserva_en_ambos_sentidos():
    with entorno() as (cliente, _, __):
        comprobar.assertEqual(cliente.post("/api/reservas", json=reserva_prueba(fecha="2030-01-07", inicio="08:00", fin="09:00")).status_code, 409)
        comprobar.assertEqual(cliente.post("/api/reservas", json=reserva_prueba(fecha="2030-01-07", inicio="18:00", fin="19:00")).status_code, 201)
        clase = {"aula": "A101", "docente": "D01", "dia": 0, "asignatura": "AS01", "asistentes": 20, "inicio": "18:30", "fin": "19:30"}
        comprobar.assertEqual(cliente.post("/api/horarios", json=clase).status_code, 409)
        comprobar.assertEqual(cliente.post("/api/horarios", json={**clase, "inicio": "19:00", "fin": "20:00"}).status_code, 201)


def test_editar_eliminar_horarios():
    with entorno() as (cliente, _, __):
        clase = {"aula": "A101", "docente": "D01", "dia": 0, "asignatura": "AS01", "asistentes": 20, "inicio": "20:00", "fin": "21:00"}
        respuesta = cliente.post("/api/horarios", json=clase)
        comprobar.assertEqual(respuesta.status_code, 201)
        url = "/api/horarios/" + respuesta.json["id"]
        comprobar.assertEqual(cliente.put(url, json={**clase, "fin": "22:00"}).status_code, 200)
        comprobar.assertEqual(cliente.delete(url).status_code, 200)
        comprobar.assertEqual(cliente.delete(url).status_code, 404)


def test_validaciones_entrada():
    with entorno() as (cliente, _, __):
        invalidas = [{"asistentes": 500}, {"fecha": "2030-02-30"}, {"fecha": "07/01/2030"},
                     {"inicio": "11:00", "fin": "10:00"}, {"inicio": "9:00"}, {"asistentes": True}, {"asistentes": 0}]
        for cambios in invalidas:
            comprobar.assertEqual(cliente.post("/api/reservas", json=reserva_prueba(**cambios)).status_code, 400, cambios)
        for cambios in ({"aula": "X"}, {"docente": "X"}):
            comprobar.assertEqual(cliente.post("/api/reservas", json=reserva_prueba(**cambios)).status_code, 404)
        for prioridad in [0, 6, True, "1"]:
            comprobar.assertEqual(cliente.post("/api/solicitudes", json=reserva_prueba(prioridad=prioridad)).status_code, 400)
        comprobar.assertEqual(cliente.post("/api/aulas", json=[]).status_code, 400)
        comprobar.assertEqual(cliente.post("/api/aulas", data='{mal', content_type="application/json").status_code, 400)
        comprobar.assertEqual(cliente.post("/api/aulas", json=aula_prueba(), headers={"Origin": "https://externo.example"}).status_code, 403)


def test_filtros_intervalo():
    with entorno() as (cliente, _, __):
        aulas = cliente.get("/api/aulas?edificio=A&piso=1&capacidad=40").json
        comprobar.assertEqual({a["id"] for a in aulas}, {"A102", "A103"})
        ocupada = cliente.get("/api/aulas?fecha=2030-01-07&hora=08:00&q=A101").json[0]
        comprobar.assertEqual(ocupada["estado"], "ocupada")
        comprobar.assertEqual(cliente.get("/api/aulas?fecha=2030-01-07&inicio=08:00&fin=09:00&q=A101").json, [])
        comprobar.assertEqual(len(cliente.get("/api/aulas?fecha=2030-01-07&inicio=09:00&fin=10:00&q=A101").json), 1)
        for parametros in ("capacidad=no", "fecha=incorrecta", "inicio=08:00", "hora=24:00"):
            comprobar.assertEqual(cliente.get("/api/aulas?" + parametros).status_code, 400)


def test_solicitudes_prioridad_reinicio_y_rechazo():
    with entorno() as (cliente, carpeta, _):
        # Prioridad 1 adelanta a los ejemplos de prioridades 2, 3 y 4.
        s1 = cliente.post("/api/solicitudes", json=reserva_prueba(prioridad=1)).json
        s2 = cliente.post("/api/solicitudes", json=reserva_prueba(prioridad=1)).json
        reiniciado = crear_app(carpeta).test_client()
        comprobar.assertEqual(reiniciado.get("/api/solicitudes").json["proxima"], s1["id"])
        aprobada = reiniciado.post("/api/solicitudes/atender").json
        comprobar.assertEqual(aprobada["id"], s1["id"])
        comprobar.assertEqual(aprobada["estado"], "aprobada")
        comprobar.assertTrue(any(r.get("solicitud") == s1["id"] for r in reiniciado.get("/api/reservas").json))
        rechazada = reiniciado.post("/api/solicitudes/atender").json
        comprobar.assertEqual(rechazada["id"], s2["id"])
        comprobar.assertEqual(rechazada["estado"], "rechazada")
        comprobar.assertIn("no está disponible", rechazada["resultado"])
        comprobar.assertEqual(crear_app(carpeta).test_client().get("/api/solicitudes").json["atendidas"][-1]["id"], s2["id"])


def test_catalogos_y_conexiones():
    with entorno() as (cliente, carpeta, _):
        for tipo, registro in [("docentes", {"id": "DTEST", "nombre": "Docente ficticio", "especialidad": "Sistemas"}),
                               ("asignaturas", {"id": "ASTEST", "nombre": "Asignatura ficticia", "creditos": 3}),
                               ("edificios", {"id": "C", "nombre": "Pruebas", "descripcion": "Edificio temporal"})]:
            comprobar.assertEqual(cliente.post("/api/" + tipo, json=registro).status_code, 201)
            comprobar.assertEqual(cliente.put(f"/api/{tipo}/{registro['id']}", json={**registro, "nombre": "Modificado"}).status_code, 200)
            comprobar.assertEqual(cliente.delete(f"/api/{tipo}/{registro['id']}").status_code, 200)
        comprobar.assertEqual(cliente.post("/api/conexiones", json={"origen": "A", "destino": "A"}).status_code, 400)
        comprobar.assertTrue(cliente.get("/api/rutas?origen=A101&destino=B101").json["ruta"])
        comprobar.assertEqual(cliente.delete("/api/conexiones", json={"origen": "A", "destino": "B"}).status_code, 200)
        comprobar.assertEqual(crear_app(carpeta).test_client().get("/api/rutas?origen=A101&destino=B101").json["ruta"], [])
        comprobar.assertEqual(cliente.post("/api/conexiones", json={"origen": "A", "destino": "B"}).status_code, 200)
        comprobar.assertTrue(cliente.get("/api/rutas?origen=A101&destino=B101").json["ruta"])


def test_recuperacion_transaccion_interrumpida():
    with entorno() as (_, carpeta, __):
        actuales = archivos.cargar_todo(carpeta)
        cambios = {"aulas": actuales["aulas"] + [aula_prueba()], "historial": []}
        guardar_original = archivos.guardar_datos

        def guardar_con_fallo(ruta, registros):
            if Path(ruta).name == "historial.json":
                raise OSError("Fallo de disco simulado")
            guardar_original(ruta, registros)

        with patch("archivos.guardar_datos", side_effect=guardar_con_fallo):
            with comprobar.assertRaises(OSError):
                archivos.guardar_cambios(carpeta, cambios)
        comprobar.assertTrue((carpeta / "transaccion.json").exists())
        recuperados = archivos.cargar_todo(carpeta)
        comprobar.assertIn("Z999", [a["id"] for a in recuperados["aulas"]])
        comprobar.assertFalse((carpeta / "transaccion.json").exists())


def test_escritura_atomica_preserva_original():
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "prueba.json"
        archivos.guardar_datos(ruta, [1, 2])
        with patch("archivos.os.replace", side_effect=OSError("Fallo simulado")):
            with comprobar.assertRaises(OSError):
                archivos.guardar_datos(ruta, [3, 4])
        comprobar.assertEqual(archivos.cargar_datos(ruta), [1, 2])


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(funcion, description=nombre)
                              for nombre, funcion in sorted(globals().items()) if nombre.startswith("test_"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
