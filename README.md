# AulaGest — Sistema de Administración y Reserva de Aulas Universitarias

**Proyecto Integrador | Estructuras de Datos Dinámicas**  
**Grupo 2**

---

## Integrantes del Equipo

* **Ángel Corrales**
* **Martín Castillo** (`@mecastilloh-netizen`)
* **Manuel Canales**
* **Jeremy Coca**

---

## Descripción del Proyecto

**AulaGest** es una aplicación web local desarrollada en **Python (Flask)** y **JavaScript vanilla** con persistencia en archivos **JSON**. Permite gestionar de manera integral la disponibilidad de aulas universitarias, horarios recurrentes de lunes a sábado, reservas extraordinarias, catálogo de docentes/asignaturas, conectividad entre edificios y una cola de atención de solicitudes por prioridad.

### Funcionalidades Principales
* **Dashboard en tiempo real:** Estadísticas generales, estado actual de cada aula (disponible, ocupada o próxima a liberarse en $\le 30$ min) y reloj sincronizado.
* **Gestión de Aulas y Horarios:** Creación, edición, eliminación y búsqueda de aulas, junto con un calendario semanal recurrente[cite: 1].
* **Reservas y Detección de Conflictos:** Validación automática de cruces de horario en intervalos `[inicio, fin)` y control de capacidad máxima[cite: 1].
* **Atención de Solicitudes con Prioridad:** Cola dinámica que ordena peticiones desde *Emergencia académica (1)* hasta *Otra solicitud (5)*, respetando el orden de llegada en caso de empate[cite: 1].
* **Mapa y Rutas entre Edificios:** Conexiones bidireccionales entre edificios, pasillos y aulas con cálculo de ruta más corta[cite: 1].
* **Historial Persistente:** Auditoría de todos los movimientos realizados en el sistema[cite: 1].

---

## Estructuras de Datos Dinámicas Implementadas

El núcleo lógico del sistema implementa cuatro estructuras de datos fundamentales con análisis de complejidad asintótica:

| Estructura | Módulo | Implementación y Uso en el Sistema | Complejidad Temporal |
| :--- | :--- | :--- | :--- |
| **Árbol Binario de Búsqueda (ABB)** | `arboles.py` | Indexación y búsqueda rápida de aulas por código (`id`), además de recorridos *inorden* y reconstrucción balanceada por mitades[cite: 1]. | Búsqueda/Inserción: $O(h)$ ($O(\log n)$ promedio) <br> Inorden: $O(n)$[cite: 1] |
| **Grafo No Dirigido** | `grafos.py` | Representación mediante diccionarios de adyacencia para modelar edificios, pasillos por piso y aulas[cite: 1]. Cálculo de rutas mediante **BFS (Búsqueda en Anchura)**[cite: 1]. | Conexión/Consulta: $O(1)$ promedio <br> Ruta BFS: $O(V + E)$[cite: 1] |
| **Cola de Prioridad (Min-Heap)** | `monticulos.py` | Implementada con `heapq` usando tuplas `(prioridad, orden, id)` para atender solicitudes urgentes primero y desempatar por orden de llegada[cite: 1]. | Inserción/Atención: $O(\log n)$ <br> Consulta próxima: $O(1)$[cite: 1] |
| **Lista Dinámica** | `listas.py` | Registro secuencial e historial persistente de movimientos, filtrado por palabras clave y consulta de operaciones recientes[cite: 1]. | Inserción (`append`): $O(1)$ amortizado <br> Filtrado: $O(n \cdot m)$[cite: 1] |

---

## Arquitectura del Proyecto

```text
AulaGest/
├── main.py                  # Punto de entrada y configuración de puerto[cite: 1]
├── servidor.py              # API REST con Flask y manejo de errores HTTP[cite: 1]
├── servicios.py             # Reglas de negocio, validaciones y sincronización[cite: 1]
├── arboles.py               # Árbol Binario de Búsqueda (ABB) de aulas[cite: 1]
├── grafos.py                # Grafo de adyacencia y algoritmo BFS[cite: 1]
├── monticulos.py            # Cola de prioridad para solicitudes[cite: 1]
├── listas.py                # Gestión de historial y filtros[cite: 1]
├── horarios.py              # Lógica de fechas, intervalos y detección de conflictos[cite: 1]
├── archivos.py              # Persistencia atómica en JSON y recuperación[cite: 1]
├── pruebas.py               # Suite de 22 pruebas unitarias aisladas[cite: 1]
├── verificar_http.py        # Pruebas de integración HTTP end-to-end[cite: 1]
├── requirements.txt         # Dependencias del proyecto (Flask)[cite: 1]
├── datos/                   # Almacenamiento local en formato JSON[cite: 1]
└── web/                     # Interfaz de usuario (HTML5, CSS3, JavaScript ES6)[cite: 1]
