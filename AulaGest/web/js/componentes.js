// Utilidades de presentación, iconos SVG y formularios accesibles compartidos.
export function escapar(valor = '') {
  return String(valor ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

const trazos = {
  dashboard:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  aulas:'M4 21h16 M6 21V4h12v17 M10 4V2 M14 4V2 M14 12h1',
  horarios:'M4 5h16v16H4z M8 3v4 M16 3v4 M4 10h16 M8 14h2 M14 14h2 M8 17h2',
  reservas:'M7 3h10v3h3v15H4V6h3 M9 3h6v4H9z M8 13l3 3 5-6',
  docentes:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M17 4a4 4 0 0 1 0 7 M22 21v-2a4 4 0 0 0-3-4',
  asignaturas:'M12 5C9 3 6 3 2 4v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1z M12 5v15',
  edificios:'M3 21h18 M5 21V3h10v18 M15 9h4v12 M8 7h1 M11 7h1 M8 11h1 M11 11h1 M9 21v-5h3v5',
  solicitudes:'M4 4h16v16H4z M8 8h8 M8 12h5 M8 16h2 M17 14v4 M15 16h4',
  historial:'M3 11a9 9 0 1 1 2 7 M3 4v7h7 M12 7v6l4 2',
  plus:'M12 5v14 M5 12h14', arrow:'M5 12h14 M14 7l5 5-5 5',
  check:'M5 12l4 4L19 6', clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 7v5l3 2',
  edit:'m4 16 12-12 4 4-12 12-5 1z M13 7l4 4',
  trash:'M3 6h18 M9 6V3h6v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7',
  close:'M6 6l12 12 M18 6 6 18', search:'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6',
  route:'M5 5h12a3 3 0 0 1 0 6H7a3 3 0 0 0 0 6h12 M16 14l3 3-3 3',
  refresh:'M20 7a9 9 0 1 0 1 8 M20 2v5h-5', info:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 11v6 M12 7h.01'
};
export const icono = nombre => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${trazos[nombre] || trazos.info}"/></svg>`;
export const nombresEstado = {disponible:'Disponible',ocupada:'Ocupada',por_liberarse:'Por liberarse',activa:'Activa',cancelada:'Cancelada',pendiente:'Pendiente',aprobada:'Aprobada',rechazada:'Rechazada'};
export const coloresEstado = {disponible:'green',ocupada:'red',por_liberarse:'amber',activa:'blue',cancelada:'red',pendiente:'amber',aprobada:'green',rechazada:'red'};
export const estado = valor => `<span class="badge ${coloresEstado[valor] || 'blue'}">${escapar(nombresEstado[valor] || valor)}</span>`;
export const dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
export const prioridades = ['Emergencia académica','Examen','Clase regular','Actividad extracurricular','Otra solicitud'];

export function fechaBonita(fecha) {
  return new Intl.DateTimeFormat('es-NI', {day:'numeric',month:'short',year:'numeric',timeZone:'America/Managua'}).format(new Date(fecha.length === 10 ? fecha + 'T12:00:00-06:00' : fecha));
}
export const horaBonita = hora => {
  if (!hora) return '—';
  const [h,m] = hora.split(':').map(Number);
  return `${h % 12 || 12}:${String(m).padStart(2,'0')} ${h < 12 ? 'a. m.' : 'p. m.'}`;
};
export function opciones(registros, valor = '', etiqueta = 'nombre') {
  return registros.map(r => `<option value="${escapar(r.id)}" ${String(r.id) === String(valor) ? 'selected' : ''}>${escapar(r[etiqueta])}</option>`).join('');
}
export function vacio(titulo, descripcion, icon = 'search') {
  return `<div class="empty">${icono(icon)}<h3>${escapar(titulo)}</h3><p>${escapar(descripcion)}</p></div>`;
}
export function tabla(cabeceras, filas) {
  if (!filas.length) return vacio('Todavía no hay registros', 'Los registros que agregues aparecerán aquí.');
  return `<div class="table-wrap"><table><thead><tr>${cabeceras.map(c => `<th scope="col">${escapar(c)}</th>`).join('')}</tr></thead><tbody>${filas.join('')}</tbody></table></div>`;
}
export function acciones(tipo, id, eliminar = true) {
  return `<div class="actions"><button class="icon-button" data-editar="${tipo}" data-id="${escapar(id)}" title="Editar ${escapar(id)}" aria-label="Editar ${escapar(id)}">${icono('edit')}</button>${eliminar ? `<button class="icon-button danger" data-eliminar="${tipo}" data-id="${escapar(id)}" title="${tipo === 'reservas' ? 'Cancelar reserva' : 'Eliminar'} ${escapar(id)}" aria-label="${tipo === 'reservas' ? 'Cancelar reserva' : 'Eliminar'} ${escapar(id)}">${icono('trash')}</button>` : ''}</div>`;
}
export function notificar(mensaje, error = false) {
  const elemento = document.createElement('div');
  elemento.className = 'toast' + (error ? ' error' : '');
  elemento.textContent = mensaje;
  document.querySelector('#notificaciones').append(elemento);
  setTimeout(() => elemento.remove(), error ? 10000 : 5500);
}
export function abrirModal(titulo, contenido, pie = '') {
  const modal = document.querySelector('#modal');
  modal.innerHTML = `<div class="modal-head"><h2 id="modal-titulo">${escapar(titulo)}</h2><button class="icon-button" data-cerrar aria-label="Cerrar diálogo">${icono('close')}</button></div>${contenido}${pie}`;
  modal.querySelectorAll('[data-cerrar]').forEach(b => b.onclick = () => modal.close());
  if (!modal.open) modal.showModal();
  return modal;
}

export function formulario(titulo, campos, valores, guardar, introduccion = '') {
  const controles = campos.map(campo => {
    const valor = valores[campo.nombre] ?? campo.valor ?? '';
    const atributos = `id="campo-${campo.nombre}" name="${campo.nombre}" ${campo.opcional ? '' : 'required'} ${campo.fijo ? 'readonly' : ''}`;
    let control;
    if (campo.opciones) control = `<select ${atributos}>${opciones(campo.opciones, valor)}</select>`;
    else if (campo.tipo === 'textarea') control = `<textarea ${atributos} maxlength="${campo.maxlength || 300}">${escapar(valor)}</textarea>`;
    else control = `<input ${atributos} type="${campo.tipo || 'text'}" value="${escapar(valor)}" ${campo.min != null ? `min="${campo.min}"` : ''} ${campo.max != null ? `max="${campo.max}"` : ''} ${campo.tipo === 'number' ? 'step="1"' : ''} maxlength="${campo.maxlength || 120}" ${campo.patron ? `pattern="${campo.patron}"` : ''}>`;
    return `<div class="field ${campo.ancho ? 'wide' : ''}"><label for="campo-${campo.nombre}">${escapar(campo.etiqueta)}${control}</label>${campo.ayuda ? `<small>${escapar(campo.ayuda)}</small>` : ''}</div>`;
  }).join('');
  const modal = abrirModal(titulo, `<form id="formulario-edicion"><div class="modal-body">${introduccion ? `<p class="form-intro">${escapar(introduccion)}</p>` : ''}<div class="form-grid">${controles}</div><div class="form-error" role="alert"></div></div><div class="modal-footer"><button type="button" class="button" data-cerrar>Cancelar</button><button type="submit" class="button primary">${icono('check')} Guardar</button></div></form>`);
  modal.querySelector('form').onsubmit = async evento => {
    evento.preventDefault();
    const boton = evento.submitter;
    boton.disabled = true;
    const datos = Object.fromEntries(new FormData(evento.target));
    for (const campo of campos) if (campo.tipo === 'number' || campo.numerico) datos[campo.nombre] = Number(datos[campo.nombre]);
    try {
      await guardar(datos);
      modal.close();
    } catch (error) {
      modal.querySelector('.form-error').textContent = error.message;
      modal.querySelector('.form-error').scrollIntoView({block:'nearest'});
    } finally { boton.disabled = false; }
  };
}

export function confirmar(titulo, mensaje, ejecutar, textoBoton = 'Confirmar') {
  const modal = abrirModal(titulo, `<div class="modal-body"><p class="form-intro">${escapar(mensaje)}</p><div class="form-error" role="alert"></div></div>`, `<div class="modal-footer"><button class="button" data-cerrar>Volver</button><button class="button danger" id="confirmar-accion">${escapar(textoBoton)}</button></div>`);
  modal.querySelector('#confirmar-accion').onclick = async evento => {
    evento.currentTarget.disabled = true;
    try { await ejecutar(); modal.close(); }
    catch (error) { modal.querySelector('.form-error').textContent = error.message; }
    finally { modal.querySelector('#confirmar-accion').disabled = false; }
  };
}
