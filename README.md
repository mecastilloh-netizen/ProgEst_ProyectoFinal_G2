<div align="center">

<!-- Banner estilo GitHub -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:1e3a8a,100:2563eb&height=200&section=header&text=AulaGest&fontSize=55&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Sistema%20de%20Administraci%C3%B3n%20y%20Reserva%20de%20Aulas%20Universitarias&descAlignY=60&descSize=16" width="100%" />

**Proyecto Integrador | Estructuras de Datos Dinámicas — Grupo 1**

[![Python](https://img.shields.io/badge/Python-3.x-1e3a8a?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask_API_REST-0f172a?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![JavaScript](https://img.shields.io/badge/Frontend-Vanilla_JS_ES6-ca8a04?style=for-the-badge&logo=javascript&logoColor=white)](https://developer.mozilla.org/)
[![JSON](https://img.shields.io/badge/Persistencia-JSON_At%C3%B3mico-0d9488?style=for-the-badge&logo=json&logoColor=white)](https://www.json.org/)

<br/>

> *Plataforma web local diseñada para optimizar la gestión integral de espacios universitarios mediante estructuras de datos dinámicas, validación de conflictos en tiempo real y atención priorizada.*

</div>

---

## 📋 Descripción General

**AulaGest** es una aplicación web local desarrollada en **Python (Flask)** y **JavaScript vanilla** con persistencia en archivos **JSON**. Permite gestionar de manera integral:
* La disponibilidad en vivo de aulas universitarias.
* Horarios recurrentes de **lunes a sábado** y reservas extraordinarias.
* Catálogo de docentes y asignaturas.
* Conectividad espacial entre edificios y cálculo de rutas.
* Cola dinámica de atención de solicitudes por nivel de urgencia.

---

## ✨ Funcionalidades Principales

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>📊 Dashboard en Tiempo Real</h3>
      <ul>
        <li>Estadísticas generales del campus al instante.</li>
        <li>Estado vivo de cada aula: 🟢 <b>Disponible</b>, 🔴 <b>Ocupada</b> o 🟡 <b>Próxima a liberarse</b> ($\le 30$ min).</li>
        <li>Reloj sincronizado en tiempo real.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🗓️ Gestión de Aulas y Horarios</h3>
      <ul>
        <li>Operaciones CRUD completas (creación, edición, eliminación y búsqueda de aulas).</li>
        <li>Calendario semanal recurrente estructurado de <b>lunes a sábado</b>.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>⚡ Reservas y Control de Conflictos</h3>
      <ul>
        <li>Validación automática de cruces de horario en intervalos semiabiertos <code>[inicio, fin)</code>.</li>
        <li>Verificación estricta de capacidad máxima por aula.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🚨 Cola de Atención por Prioridad</h3>
      <ul>
        <li>Ordenamiento dinámico desde <b>Emergencia académica (1)</b> hasta <b>Otra solicitud (5)</b>.</li>
        <li>Desempate justo respetando el orden cronológico de llegada.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🗺️ Mapa y Rutas entre Edificios</h3>
      <ul>
        <li>Modelado de conexiones bidireccionales entre edificios, pasillos y aulas.</li>
        <li>Cálculo automático de la ruta más corta.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>📜 Historial Persistente</h3>
      <ul>
        <li>Auditoría completa y trazabilidad de todos los movimientos realizados en el sistema.</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🧠 Núcleo Algorítmico y Estructuras de Datos

El motor lógico del sistema implementa **cuatro estructuras de datos dinámicas** diseñadas para garantizar eficiencia computacional, acompañadas de su análisis de complejidad asintótica:

| Estructura de Datos | Módulo | Implementación y Propósito en AulaGest | Complejidad Temporal |
| :--- | :---: | :--- | :--- |
| 🌳 **Árbol Binario de Búsqueda (ABB)** | `arboles.py` | Indexación y búsqueda rápida de aulas por código (`id`), recorridos *inorden* y reconstrucción balanceada por mitades. | • **Búsqueda / Inserción:** $O(h)$ *(promedio $O(\log n)$)*<br>• **Recorrido Inorden:** $O(n)$ |
| 🕸️ **Grafo No Dirigido** | `grafos.py` | Representación mediante diccionarios de adyacencia para edificios, pasillos por piso y aulas. Búsqueda de rutas con **BFS (Búsqueda en Anchura)**. | • **Conexión / Consulta:** $O(1)$ promedio<br>• **Ruta más corta (BFS):** $O(V + E)$ |
| ⏳ **Cola de Prioridad (Min-Heap)** | `monticulos.py` | Implementada con `heapq` usando tuplas `(prioridad, orden, id)` para atender emergencias primero y desempatar por orden de llegada. | • **Inserción / Atención:** $O(\log n)$<br>• **Consulta próxima:** $O(1)$ |
| 📋 **Lista Dinámica** | `listas.py` | Registro secuencial e historial persistente de movimientos, filtrado por palabras clave y consulta de operaciones recientes. | • **Inserción (`append`):** $O(1)$ amortizado<br>• **Filtrado:** $O(n \cdot m)$ |

---

## 🏗️ Diseño del Proyecto

```text
📦 AulaGest/
 ┣ 📂 datos/                   # Almacenamiento local persistente en formato JSON
 ┣ 📂 web/                     # Interfaz de usuario (HTML5, CSS3, JavaScript ES6)
 ┣ 📜 main.py                  # Punto de entrada y configuración de puerto
 ┣ 📜 servidor.py              # API REST con Flask y manejo de errores HTTP
 ┣ 📜 servicios.py             # Reglas de negocio, validaciones y sincronización
 ┣ 📜 arboles.py               # Árbol Binario de Búsqueda (ABB) de aulas
 ┣ 📜 grafos.py                # Grafo de adyacencia y algoritmo BFS
 ┣ 📜 monticulos.py            # Cola de prioridad (Min-Heap) para solicitudes
 ┣ 📜 listas.py                # Gestión de historial y filtros dinámicos
 ┣ 📜 horarios.py              # Lógica de fechas, intervalos y detección de conflictos
 ┣ 📜 archivos.py              # Persistencia atómica en JSON y recuperación
 ┣ 📜 pruebas.py               # Suite de 22 pruebas unitarias aisladas
 ┣ 📜 verificar_http.py        # Pruebas de integración HTTP end-to-end
 ┗ 📜 requirements.txt         # Dependencias del proyecto (Flask)
