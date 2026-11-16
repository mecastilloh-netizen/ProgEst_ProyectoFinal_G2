// Acceso centralizado a Flask: misma dirección que la página, sin servicios externos.
const BASE = '/api';

export async function api(ruta, metodo = 'GET', datos) {
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), 15000);
  try {
    const respuesta = await fetch(BASE + ruta, {
      method: metodo, signal: control.signal, cache: 'no-store',
      headers: datos === undefined ? {} : {'Content-Type': 'application/json'},
      body: datos === undefined ? undefined : JSON.stringify(datos)
    });
    const resultado = await respuesta.json();
    if (!respuesta.ok) throw new Error(resultado.error || 'No se pudo completar la operación.');
    return resultado;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('El servidor tarda demasiado. Comprueba la terminal y vuelve a intentar.');
    if (error instanceof TypeError) throw new Error('Sin conexión con Flask. Inicia python main.py y vuelve a intentar.');
    throw error;
  } finally {
    clearTimeout(temporizador);
  }
}

export function consulta(filtros) {
  const parametros = new URLSearchParams();
  for (const [clave, valor] of Object.entries(filtros)) if (valor !== '' && valor != null) parametros.set(clave, valor);
  return parametros.size ? '?' + parametros.toString() : '';
}
