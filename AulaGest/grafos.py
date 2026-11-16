"""Grafo no dirigido de edificios, pasillos y aulas; rutas por BFS."""
from collections import deque


def agregar_vertice(grafo, vertice):
    # O(1) promedio mediante diccionario.
    grafo.setdefault(vertice, {})


def conectar_vertices(grafo, origen, destino):
    # O(1) promedio: los vecinos también se almacenan en diccionarios.
    if origen == destino:
        raise ValueError("Una conexión necesita dos lugares distintos.")
    agregar_vertice(grafo, origen)
    agregar_vertice(grafo, destino)
    grafo[origen][destino] = True
    grafo[destino][origen] = True


def eliminar_conexion(grafo, origen, destino):
    # O(1) promedio.
    grafo.get(origen, {}).pop(destino, None)
    grafo.get(destino, {}).pop(origen, None)


def consultar_vecinos(grafo, vertice):
    return list(grafo.get(vertice, {}))  # O(grado del vértice).


def buscar_ruta_bfs(grafo, origen, destino):
    # O(V + E), memoria O(V). Guardar padres evita copiar rutas en cada paso.
    if origen not in grafo or destino not in grafo:
        return []
    cola, padres = deque([origen]), {origen: None}
    while cola:
        actual = cola.popleft()
        if actual == destino:
            ruta = []
            while actual is not None:
                ruta.append(actual)
                actual = padres[actual]
            return ruta[::-1]
        for vecino in grafo[actual]:
            if vecino not in padres:
                padres[vecino] = actual
                cola.append(vecino)
    return []


def mostrar_conexiones(grafo):
    # O(V + E); cada arista no dirigida aparece una sola vez.
    return [[a, b] for a in grafo for b in grafo[a] if a < b]


def construir_grafo(edificios, aulas):
    grafo = {}
    for edificio in edificios:
        origen = "Edificio " + edificio["id"]
        agregar_vertice(grafo, origen)
        for otro in edificio.get("conexiones", []):
            conectar_vertices(grafo, origen, "Edificio " + otro)
    for aula in aulas:
        pasillo = f"Pasillo {aula['edificio']} · piso {aula['piso']}"
        conectar_vertices(grafo, "Edificio " + aula["edificio"], pasillo)
        conectar_vertices(grafo, pasillo, aula["id"])
    return grafo
