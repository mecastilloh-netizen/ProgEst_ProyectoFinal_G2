"""Árbol binario de búsqueda de aulas, construido con diccionarios, sin clases."""


def crear_nodo(aula):
    # O(1): cada nodo conserva una referencia al aula.
    return {"clave": aula["id"], "aula": aula, "izquierda": None, "derecha": None}
   
    """
    Crea un nodo del árbol binario de búsqueda para almacenar un aula.
    """


def insertar_aula(raiz, aula):
    # O(h): promedio O(log n), peor O(n) si el árbol está degenerado.
    if raiz is None:
        return crear_nodo(aula)
    actual = raiz
    while True:
        if aula["id"] == actual["clave"]:
            actual["aula"] = aula
            return raiz
        lado = "izquierda" if aula["id"] < actual["clave"] else "derecha"
        if actual[lado] is None:
            actual[lado] = crear_nodo(aula)
            return raiz
        actual = actual[lado]
        
    """
    Inserta un aula en el árbol binario de búsqueda.
    """


def buscar_aula(raiz, codigo):
    # O(h), con los mismos casos que insertar_aula; memoria O(1).
    while raiz:
        if codigo == raiz["clave"]:
            return raiz["aula"]
        raiz = raiz["izquierda" if codigo < raiz["clave"] else "derecha"]
    return None

    """
    Busca un aula dentro del árbol utilizando su código identificador.
    """


def recorrido_inorden(raiz):
    # O(n), pila O(h). Iterativo para soportar árboles muy desbalanceados.
    resultado, pila = [], []
    while raiz or pila:
        while raiz:
            pila.append(raiz)
            raiz = raiz["izquierda"]
        raiz = pila.pop()
        resultado.append(raiz["aula"])
        raiz = raiz["derecha"]
    return resultado

    """
    Recorre el árbol en orden: izquierda, raíz y derecha.
    """

def reconstruir_arbol(aulas):
    # Ordenar O(n log n); construir por mitades O(n), altura O(log n).
    ordenadas = sorted(aulas, key=lambda aula: aula["id"])

    def construir(inicio, fin):
        if inicio >= fin:
            return None
        medio = (inicio + fin) // 2
        nodo = crear_nodo(ordenadas[medio])
        nodo["izquierda"] = construir(inicio, medio)
        nodo["derecha"] = construir(medio + 1, fin)
        return nodo

    return construir(0, len(ordenadas))

    """
    Reconstruye un árbol binario balanceado a partir de una lista de aulas.

    Ordena los registros y utiliza una construcción recursiva
    para seleccionar los elementos centrales.

    Parámetros:
        aulas: Lista de diccionarios con información de aulas.

    Retorna:
        La raíz del árbol reconstruido.
    """