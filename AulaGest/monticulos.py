"""Cola de prioridad estable con heapq: menor número se atiende primero."""
import heapq

PRIORIDADES = {1: "Emergencia académica", 2: "Examen", 3: "Clase regular",
               4: "Actividad extracurricular", 5: "Otra solicitud"}


def agregar_solicitud(monticulo, solicitud):
    # O(log n). El contador persistente resuelve empates por orden de llegada.
    heapq.heappush(monticulo, (solicitud["prioridad"], solicitud["orden"], solicitud["id"]))


def consultar_proxima(monticulo):
    return monticulo[0][2] if monticulo else None  # O(1).


def atender_solicitud(monticulo):
    return heapq.heappop(monticulo)[2] if monticulo else None  # O(log n).


def mostrar_pendientes(monticulo):
    # O(n log n); ordenar una copia NO destruye la cola original.
    return [elemento[2] for elemento in sorted(monticulo)]


def reconstruir_monticulo(solicitudes):
    # O(n): heapify es lineal, a diferencia de n inserciones independientes.
    monticulo = [(s["prioridad"], s["orden"], s["id"])
                 for s in solicitudes if s["estado"] == "pendiente"]
    heapq.heapify(monticulo)
    return monticulo
