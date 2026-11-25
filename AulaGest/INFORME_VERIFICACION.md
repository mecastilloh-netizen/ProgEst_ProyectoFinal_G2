# Verificación de AulaGest V1

Fecha: 23 de noviembre de 2026. Zona de referencia: America/Managua.

## Resultados observados

| Verificación | Resultado |
| --- | --- |
| Entorno local | Python 3.13.18, entorno virtual `.venv`, Flask 3.1.3 instalado. |
| `python pruebas.py` | 23 pruebas aprobadas; sin advertencias de archivos abiertos en la ejecución final. |
| `python verificar_http.py` | Aprobado: HTML y 10 endpoints GET mediante HTTP real. |
| Guardado de aula por HTTP | POST 201 y comprobación de su presencia en `aulas.json` temporal. |
| Reinicio del servidor | Segundo proceso encuentra el aula, la reserva y el historial creados en el primero. |
| Datos de prueba | Directorios temporales; los JSON principales conservan los datos ficticios iniciales. |
| Errores y conflictos | Pruebas de 400, 404, 409; protección de referencias, capacidad e intervalos. |
| Corrupción JSON | Archivos inválidos conservados; inicio rechazado con error claro. |
| Escritura interrumpida | Original preservado ante fallo de reemplazo; diario recuperado al volver a cargar. |
| Python | Compilación de los módulos sin errores de sintaxis. |
| Interfaz HTML | Los nueve apartados responden desde Flask. Las pruebas revisan el HTML y envían formularios con el cliente de Flask. |
| Formularios | Alta y edición de aulas, conflicto de reserva, cancelación, atención de solicitud y persistencia tras recargar. |

## Repetir las comprobaciones

Desde `AulaGest/`, ejecutar:

```powershell
.\.venv\Scripts\python.exe pruebas.py
.\.venv\Scripts\python.exe verificar_http.py
```

Para utilizar la aplicación después de verificarla:

```powershell
.\.venv\Scripts\python.exe main.py
```

Abrir `http://127.0.0.1:5000`. No se publica ningún servicio ni se requieren cuentas externas.
