# AulaGest V1

Prototipo universitario funcional para administrar aulas, horarios semanales, reservas extraordinarias y solicitudes con prioridad. Interfaz en español, HTML generado por Python con Flask y almacenamiento JSON local. Los nombres y registros iniciales son ficticios.

## Ejecutar

Requiere **Python 3.10 o superior**. Probado con Python 3.13.18 y Flask 3.1.3.

Desde la carpeta `AulaGest/`:

```bash
pip install -r requirements.txt
python main.py
```

Abre **http://127.0.0.1:5000** en el navegador. Mantén la terminal abierta; `Ctrl+C` detiene el servidor. Abre la dirección de Flask, no el archivo HTML directamente.

Solo Flask es una dependencia directa. Sus dependencias internas se instalan automáticamente con pip. No se necesitan Node, bases de datos, cuentas externas ni una conexión a Internet durante el uso.

### En esta computadora Windows

Ya se preparó el entorno virtual `AulaGest/.venv/`. Desde PowerShell, dentro de `AulaGest/`, funciona incluso si `python` no está en `PATH`:

```powershell
.\.venv\Scripts\python.exe main.py
```

También puedes abrir **`iniciar.bat`** con doble clic. El lanzador usa el entorno virtual local y muestra la terminal para detener el servidor. No instala paquetes ni cambia configuraciones del equipo.

Para preparar un entorno nuevo en otra computadora:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

El entorno virtual es local a la máquina; no debe copiarse como parte de una entrega ni agregarse a Git. Si el puerto está ocupado, usa `python main.py --puerto 5001` y abre `http://127.0.0.1:5001`.

## Qué puedes hacer

| Sección | Funciones conectadas al backend |
| --- | --- |
| Dashboard | Cinco estadísticas, tabla de aulas, estado actual, actividad, liberación y tiempo restante. |
| Aulas | Crear, editar, eliminar, buscar por código o nombre, consultar horarios y equipamiento. |
| Horarios | Calendario recurrente de lunes a sábado por aula; crear, editar y eliminar clases. |
| Reservas | Crear, modificar y cancelar actividades con fecha específica; consultar activas y canceladas. |
| Docentes | Registrar, editar y eliminar docentes ficticios. |
| Asignaturas | Registrar, editar y eliminar asignaturas y créditos. |
| Edificios | CRUD de edificios, conexiones de doble sentido, listado de adyacencias y rutas BFS. |
| Solicitudes | Crear solicitudes, consultar la cola y atender la siguiente según prioridad y llegada. |
| Historial | Ver y buscar movimientos persistentes, del más reciente al más antiguo. |

Flask genera cada página en el servidor con las plantillas HTML de `web/`. La presentación usa [Bootstrap 5.3](https://getbootstrap.com/docs/5.3/getting-started/introduction/) con una copia local de su CSS y licencia en `web/assets/bootstrap/`. Los enlaces y filtros hacen peticiones GET. Los formularios envían los cambios por POST y muestran los errores de validación junto a los datos introducidos.

### Disponibilidad y filtros

- Filtra por edificio, piso, capacidad mínima y estado. El filtro «Ocupadas» incluye las aulas próximas a liberarse.
- En «Filtrar aulas» selecciona una fecha y una hora para consultar el estado. Si omites la fecha se usa hoy; si omites la hora se usa la hora actual de Nicaragua.
- Para buscar un aula libre durante un intervalo, llena **ambas** horas «Libre desde» y «Libre hasta» y aplica el filtro. Las filas reflejan el estado en la hora consultada, y la selección del aula garantiza que no tiene ocupaciones en el intervalo solicitado.
- Las estadísticas superiores corresponden siempre al momento actual, aunque el listado esté filtrado por otra fecha.
- Los estados se muestran con texto. «Por liberarse» indica que faltan 30 minutos o menos.
- Si hay actividades consecutivas, la liberación corresponde al final de la cadena. El tiempo restante indica el de la actividad actual. La siguiente actividad puede empezar inmediatamente después.
- El detalle de un aula consulta su estado **actual**, sus clases semanales y sus reservas activas.
- La hora y la disponibilidad corresponden al momento de cargar o consultar la página. Recarga para actualizarlas.

### Reglas de horarios y reservas

Las clases tienen `dia` de 0 a 5 (lunes a sábado) y se repiten todas las semanas. Las reservas y solicitudes tienen `fecha` en formato `AAAA-MM-DD`, incluyendo domingos.

Las horas usan `HH:MM`, desde `00:00` hasta `23:59`. Se exige `inicio < fin`. Una actividad que cruza medianoche debe dividirse en dos registros; no se admite `24:00`.

Los intervalos son **[inicio, fin)**: una clase de 08:00 a 09:00 y otra de 09:00 a 10:00 son compatibles. El cruce se comprueba así:

```python
inicio_a < fin_b and inicio_b < fin_a
```

Se comprueban los conflictos del aula entre clases, entre reservas y entre ambos tipos. Crear o editar una clase también comprueba las reservas existentes. Las reservas canceladas dejan de bloquear el espacio.

Se rechazan códigos duplicados, referencias inexistentes, fechas y horas incorrectas, prioridades fuera de 1–5, cantidades no enteras y actividades que superan la capacidad. Reducir la capacidad de un aula tampoco puede dejar actividades asociadas con capacidad insuficiente.

No se puede cambiar el identificador de un registro editándolo. Eliminar un aula con horarios, reservas —incluidas canceladas— o solicitudes asociadas se impide explícitamente. Se aplica la misma protección a docentes, asignaturas y edificios. Se conserva así la trazabilidad de los registros.

### Solicitudes

Prioridades: 1 emergencia académica, 2 examen, 3 clase regular, 4 actividad extracurricular y 5 otra solicitud. El montículo almacena `(prioridad, orden, id)`; `orden` es un contador persistente que resuelve empates por llegada.

Una solicitud puede entrar en cola aunque exista un conflicto de horario. Al atenderla se vuelve a validar disponibilidad y capacidad. Si cumple, se crea la reserva y queda aprobada; si no, queda rechazada con un motivo visible. No se asigna automáticamente otra aula. Para cambiar una solicitud atendida se debe registrar una nueva; la anterior conserva su resultado.

## Archivos y responsabilidades

```text
AulaGest/
├── main.py                  # Entrada, puerto y carpeta de datos opcionales
├── servidor.py              # HTTP/Flask y respuestas de errores
├── servicios.py             # Reglas de negocio y coordinación de los módulos
├── grafos.py                # Adyacencias y búsqueda BFS
├── listas.py                # Historial y filtros de movimientos
├── arboles.py               # ABB con diccionarios, sin clases
├── monticulos.py            # Cola de prioridad estable con heapq
├── horarios.py              # Fechas, intervalos, conflictos y disponibilidad
├── archivos.py              # Toda la lectura/escritura JSON y datos iniciales
├── pruebas.py               # 23 pruebas unittest aisladas
├── verificar_http.py        # Prueba de dos procesos reales de Flask
├── requirements.txt
├── README.md
├── INFORME_VERIFICACION.md
├── iniciar.bat
├── .gitignore
├── datos/
│   ├── aulas.json
│   ├── docentes.json
│   ├── asignaturas.json
│   ├── horarios.json
│   ├── reservas.json
│   ├── edificios.json
│   ├── solicitudes.json
│   └── historial.json
├── paginas.py               # Rutas de páginas y formularios Flask
└── web/
    ├── base.html, index.html, listado.html, detalle.html
    ├── formulario.html, confirmar.html, mapa.html, error.html, macros.html
    └── assets/icons/aulagest.svg
```

`servicios.py` se añade para mantener las rutas Flask pequeñas y evitar repetir validaciones en ellas. `historial.json` se añade porque también se conservan las acciones al reiniciar. `verificar_http.py` comprueba el proceso real, además del cliente de pruebas de Flask. No hay Python ni JSON de datos dentro de `web/`.

Flujo de una operación:

```text
Formulario HTML → Flask (paginas.py) → servicios.py
                                                    ↓
                                 estructuras + horarios + archivos
                                                    ↓
                                         JSON en datos/
```

El estado principal es un diccionario de listas. El árbol, grafo y montículo se reconstruyen al iniciar. El árbol y grafo se sincronizan al cambiar aulas; el grafo también al cambiar edificios o conexiones. Las solicitudes usan `heappush` y `heappop` sobre una copia de la cola y la confirman después del guardado. No se definen clases propias; las pruebas usan `unittest.FunctionTestCase`.

### Persistencia y recuperación

Los datos iniciales son **2 edificios, 12 aulas, 6 docentes, 8 asignaturas, 72 clases semanales, 3 reservas y 3 solicitudes pendientes**. Las fechas de ejemplo se calculan únicamente al crear los archivos por primera vez. No se regeneran al reiniciar. El historial empieza vacío.

`archivos.py` verifica listas, campos obligatorios, tipos, identificadores únicos, intervalos y valores básicos; `servicios.py` comprueba las referencias entre colecciones al cargar. Los datos se escriben en UTF-8, con indentación.

Cada escritura crea un temporal en la misma carpeta, escribe, vacía el búfer y reemplaza el original con `os.replace`. Una operación que afecta varias colecciones guarda primero `datos/transaccion.json`, con las versiones nuevas. Después reemplaza los archivos afectados y elimina ese diario. Si se interrumpe, el próximo arranque completa la operación desde el diario. Un error de disco durante una petición bloquea nuevas modificaciones hasta reiniciar, para no mezclar estados.

**Un archivo ilegible o dañado nunca se sustituye por una lista vacía.** Se informa el nombre y se conserva. Para recuperarlo:

1. Detén el servidor y copia toda la carpeta `datos/` a un respaldo.
2. Lee el error de la terminal. Corrige el JSON señalado o restaura una copia válida, respetando los campos y referencias.
3. Si existe `transaccion.json`, consérvalo: permite completar un guardado pendiente. Un diario inválido también debe recuperarse manualmente.
4. Vuelve a iniciar y ejecuta las pruebas. No edites JSON manualmente mientras Flask está funcionando.

El bloqueo de peticiones protege operaciones concurrentes dentro de **un proceso** de Flask. No ejecutes dos instancias sobre la misma carpeta de datos. Las pruebas usan directorios temporales independientes.

### Zona horaria

El backend intenta usar `ZoneInfo('America/Managua')`. Algunos equipos Windows no incluyen la base IANA; en ese caso usa un respaldo de UTC−06:00 con el nombre `America/Managua`, sin instalar otra dependencia. Flask muestra la hora local de Nicaragua en el HTML. El respaldo está pensado para fechas contemporáneas, no para conversiones históricas con cambios de horario. La [documentación oficial de zoneinfo](https://docs.python.org/3/library/zoneinfo.html#data-sources) explica la disponibilidad de datos de zona en Windows.

## API REST

Las respuestas usan JSON; los errores tienen forma `{"error": "mensaje claro"}`. Los listados devuelven arrays, salvo resumen, solicitudes y rutas. Creación: 201; consulta/edición/cancelación: 200; datos inválidos: 400; inexistentes: 404; duplicados/conflictos/referencias: 409; error de disco: 503. Flask devuelve 413 si el cuerpo supera 64 KiB y 415 si no se envía JSON cuando corresponde.

| Ruta | Métodos | Uso |
| --- | --- | --- |
| `/api/resumen` | GET | Conteos actuales y hora del servidor. |
| `/api/aulas` | GET, POST | Consultar y crear aulas. |
| `/api/aulas/<id>` | GET, PUT, DELETE | Detalle actual, editar, eliminar. |
| `/api/horarios` | GET, POST | Clases semanales; filtrar por `aula`. |
| `/api/horarios/<id>` | PUT, DELETE | Editar o eliminar una clase. |
| `/api/reservas` | GET, POST | Reservas; filtrar por `aula`, `fecha`, `estado`. |
| `/api/reservas/<id>` | PUT, DELETE | Editar o cancelar, conservando el registro. |
| `/api/docentes`, `/api/asignaturas`, `/api/edificios` | GET, POST | Listar o crear elementos de catálogo. |
| `/api/docentes/<id>`, `/api/asignaturas/<id>`, `/api/edificios/<id>` | PUT, DELETE | Editar o eliminar si no existen referencias. |
| `/api/solicitudes` | GET, POST | Cola ordenada, atendidas y próxima; crear solicitud. |
| `/api/solicitudes/atender` | POST | Atender la siguiente y devolver el resultado. |
| `/api/rutas` | GET | Vértices, aristas, vecinos del origen y ruta BFS. |
| `/api/conexiones` | POST, DELETE | Conectar o desconectar edificios. |
| `/api/historial` | GET | Movimientos recientes primero; filtrar por `q`. |

Filtros de `/api/aulas`: `q`, `edificio`, `piso`, `capacidad`, `estado`, `fecha`, `hora`, `inicio`, `fin`. Ejemplo: `/api/aulas?edificio=A&capacidad=35&fecha=2030-01-07&inicio=09:00&fin=10:00`. Ruta: `/api/rutas?origen=A101&destino=B201`.

Ejemplo de cuerpo para POST `/api/aulas` (PUT utiliza el mismo formato y conserva `id`):

```json
{"id":"A301","nombre":"Aula A301","edificio":"A","piso":3,"capacidad":35,"tipo":"Teórica","equipamiento":["Proyector","Pizarra"]}
```

Ejemplo para POST `/api/reservas`:

```json
{"aula":"A101","docente":"D01","fecha":"2030-01-06","inicio":"10:00","fin":"11:00","motivo":"Taller de programación","asistentes":25}
```

Para una solicitud se usa el mismo cuerpo y se añade `"prioridad": 2`. Para un horario se reemplazan `fecha` y `motivo` por `"dia": 0` y `"asignatura": "AS01"`. Los identificadores de eventos y solicitudes se generan en el servidor. Los edificios reciben `id`, `nombre` y `descripcion`; las conexiones se administran con `{"origen":"A","destino":"B"}`.

## Estructuras y complejidad asintótica

`n`: elementos de la estructura; `h`: altura del árbol; `H`: horarios; `R`: reservas; `A`: aulas; `V/E`: vértices/aristas; `B`: bytes JSON; `k`: eventos de un aula en el día. Las operaciones de diccionario se consideran O(1) **promedio**; su peor caso teórico puede ser O(n) por colisiones.

| Módulo / función | Tiempo | Explicación |
| --- | --- | --- |
| `arboles.crear_nodo` | O(1) | Guarda referencias en un diccionario. |
| `arboles.insertar_aula`, `buscar_aula` | O(h) | Promedio O(log n) con una forma equilibrada; peor O(n) degenerado. No es un árbol autoequilibrado. |
| `arboles.recorrido_inorden` | O(n) | Visita cada nodo una vez, pila O(h). |
| `arboles.reconstruir_arbol` | O(n log n) | Ordena y luego construye por mitades en O(n); altura O(log n). |
| `grafos.agregar_vertice`, `conectar_vertices`, `eliminar_conexion` | O(1) promedio | Diccionarios de adyacencia con vecinos como claves. |
| `grafos.consultar_vecinos` | O(grado(v)) | Copia los vecinos en una lista. |
| `grafos.buscar_ruta_bfs` | O(V + E) | Cola FIFO, visitados y reconstrucción por padres; memoria O(V). |
| `grafos.mostrar_conexiones`, `construir_grafo` | O(V + E) | Enumeración o construcción de adyacencias. |
| `listas.agregar_registro` | O(1) amortizado | `append`, sin incluir serialización. |
| `listas.filtrar_registros` | O(n·m) | Examina los n textos de longitud máxima m. |
| `listas.operaciones_recientes` | O(min(n, límite)) | Copia e invierte solo la porción final. |
| `monticulos.agregar_solicitud`, `atender_solicitud` | O(log n) | `heappush` y `heappop`. |
| `monticulos.consultar_proxima` | O(1) | Lee la raíz. |
| `monticulos.reconstruir_monticulo` | O(n) | `heapify` de las solicitudes pendientes. |
| `monticulos.mostrar_pendientes` | O(n log n) | Ordena una copia para mostrar toda la cola. |
| `horarios.se_superponen` | O(1) | Dos comparaciones de horas normalizadas. |
| `horarios.detectar_conflictos` | O(H + R) | Recorre clases y reservas una vez. |
| `horarios.disponibilidad` | O(H + R + k log k) | Filtra, ordena los eventos diarios y encuentra la siguiente actividad. |
| `archivos.guardar_datos`, `cargar_datos` | O(B) | Serialización/lectura proporcional al tamaño del archivo. |
| `servicios.consultar_aulas` | O(A·(H + R + k log k)) como cota | Calcula disponibilidad para cada aula que supera los filtros iniciales. |

Las complejidades del montículo y árbol **no representan el costo completo de una petición HTTP**. Para confirmar sin perder cambios se copian listas y se serializan las colecciones afectadas y el historial. Agregar una solicitud completa implica O(n) de copia y O(B) de disco, además de O(log n) del montículo. Reconstruir el árbol tras cambiar aulas cuesta O(A log A); se prioriza claridad académica sobre optimización para volúmenes grandes.

## Pruebas y verificación

```bash
python pruebas.py
python verificar_http.py
```

En el entorno Windows preparado:

```powershell
.\.venv\Scripts\python.exe pruebas.py
.\.venv\Scripts\python.exe verificar_http.py
```

Las **23 pruebas** incluyen árbol e inexistentes, inorden, BFS, eliminación de aristas, prioridades y FIFO, listas, intervalos consecutivos, liberación continua, JSON UTF-8, conservación de corrupción, API/recursos, CRUD, referencias, capacidad, reservas y reinicio, filtros, validaciones y recuperación del diario. Usan `TemporaryDirectory`; no modifican `datos/` del proyecto.

`verificar_http.py` inicia Flask en un puerto libre con datos temporales, consulta HTML y los diez endpoints de lectura, crea un aula y una reserva, comprueba el JSON, termina el proceso, inicia otro y comprueba la persistencia. Cierra ambos procesos y limpia su directorio temporal.

Las pruebas de interfaz consultan las páginas y envían formularios directamente a Flask. Comprueban las altas, los errores, la cancelación de reservas y la atención de solicitudes.

## Cómo reconstruir un módulo eliminado

Primero intenta restaurarlo desde una copia o Git. Si necesitas reescribirlo, respeta los siguientes contratos. Los datos son listas de diccionarios; no cambies las claves del JSON ni las exportaciones usadas por los importadores.

| Archivo | Contrato que debe exponer |
| --- | --- |
| `arboles.py` | `crear_nodo(aula)`, `insertar_aula(raiz,aula)`, `buscar_aula(raiz,codigo)`, `recorrido_inorden(raiz)`, `reconstruir_arbol(aulas)`. Nodo: `clave`, `aula`, `izquierda`, `derecha`; vacío: `None`. Buscar inexistente devuelve `None`. |
| `grafos.py` | `agregar_vertice(g,v)`, `conectar_vertices(g,a,b)`, `eliminar_conexion(g,a,b)`, `consultar_vecinos(g,v)`, `buscar_ruta_bfs(g,a,b)`, `mostrar_conexiones(g)`, `construir_grafo(edificios,aulas)`. Grafo `{vertice: {vecino: True}}`; ruta inexistente: `[]`. |
| `listas.py` | `agregar_registro(historial,accion,detalle,fecha)`, `filtrar_registros(historial,texto)`, `consultar_movimientos(historial,texto)`, `operaciones_recientes(historial,limite)`. Movimientos contienen `id`, `accion`, `detalle`, `fecha`. |
| `monticulos.py` | `PRIORIDADES`, `agregar_solicitud(cola,s)`, `consultar_proxima(cola)`, `atender_solicitud(cola)`, `mostrar_pendientes(cola)`, `reconstruir_monticulo(solicitudes)`. Entradas `(prioridad,orden,id)`; consultas y extracción devuelven ids o `None`. |
| `horarios.py` | `ZONA`, `DIAS`, `ahora_nicaragua()`, `validar_fecha(texto)`, `minutos(hora)`, `validar_intervalo(inicio,fin)`, `se_superponen(a,b,c,d)`, `mismo_dia(a,b)`, `detectar_conflictos(nuevo,horarios,reservas,excluir_id=None)`, `eventos_del_dia(aula,fecha,horarios,reservas)`, `disponibilidad(aula,momento,horarios,reservas)`. Exclusión: tupla `(horario/reserva,id)`; disponibilidad: `estado`, `actual`, `liberacion`, `minutos_restantes`, `proxima`. |
| `archivos.py` | `COLECCIONES`, `CAMPOS`, `verificar_estructura(datos,nombre)`, `cargar_datos(ruta,nombre=None)`, `guardar_datos(ruta,datos)`, `crear_archivos_si_no_existen(carpeta,iniciales)`, `guardar_cambios(carpeta,cambios)`, `cargar_todo(carpeta)`, `datos_iniciales()`. Errores legibles; nunca descartar corrupción. |
| `servicios.py` | Mantener las funciones invocadas por `servidor.py`: `iniciar_sistema`, `obtener`, `guardar_aula`, `eliminar_registro`, `guardar_catalogo`, `guardar_evento`, `cancelar_reserva`, `crear_solicitud`, `listar_solicitudes`, `procesar_solicitud`, `consultar_aulas`, `resumen`, `consultar_ruta`, `modificar_conexion`. Reciben `sistema` como primer argumento. Usar `ValueError` para validaciones, `LookupError` para inexistentes y `FileExistsError` para conflictos. |
| `servidor.py` | `crear_app(carpeta_datos=None)` devuelve Flask. Restaurar las rutas de la tabla REST, JSON y la exclusión mutua de peticiones. No trasladar validaciones aquí. |
| `main.py` | `main()` y llamada protegida por `if __name__ == '__main__'`. Debe iniciar `crear_app`, escuchar en loopback y admitir `--puerto` y `--datos`. |
| `paginas.py` y `web/*.html` | Rutas Flask y plantillas de páginas, formularios y consultas. Delegan validación y persistencia en las funciones de servicios. |
| `pruebas.py` | Funciones `test_*` y `load_tests` que construye una suite de `unittest.FunctionTestCase`; usar temporales. |
| `verificar_http.py` | `main()` verifica dos arranques y cierra procesos en `finally`; nunca apuntar a datos principales. |

Reconstruye primero los módulos independientes (árbol, grafo, listas y montículo), luego horarios/archivos, después servicios y Flask, y finalmente las vistas. Ejecuta `python pruebas.py` después de restaurar cada contrato y `python verificar_http.py` al terminar.

## Límites de esta versión

- Prototipo de un solo proceso local, sin usuarios, autenticación, roles ni despliegue público. El servidor de desarrollo de Flask escucha únicamente en `127.0.0.1`, con debug desactivado.
- Los conflictos se comprueban por aula. No se comprueba que un docente pueda desplazarse entre dos clases ni la simultaneidad del mismo docente en aulas distintas.
- Las clases se repiten indefinidamente: no hay semestres, vacaciones, excepciones ni fechas de vigencia. Por eso una reserva guardada de cualquier fecha del mismo día semanal puede impedir crear una clase incompatible.
- Se permiten registros de fechas pasadas para practicar consultas históricas. No hay política de plazos o cancelaciones.
- El grafo representa conectividad; BFS minimiza conexiones, no distancia física ni accesibilidad. Los pasillos y enlaces de las aulas se derivan del edificio y piso. Se pueden administrar los enlaces entre edificios.
- JSON y reconstrucción de índices son adecuados para el tamaño académico de ejemplo. No hay bloqueo entre procesos ni sincronización de ediciones manuales externas.
- Los formularios y tablas usan Bootstrap local y funcionan sin JavaScript.

Referencia del servidor: [guía oficial de Flask](https://flask.palletsprojects.com/en/stable/quickstart/). Las funciones de negocio y estructuras se implementan directamente en los módulos del proyecto.
