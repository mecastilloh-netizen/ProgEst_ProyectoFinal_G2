// Dashboard, filtros, tarjetas y consulta detallada de las aulas.
import {escapar as e, icono, opciones, estado, vacio, tabla, acciones, abrirModal, horaBonita, fechaBonita, dias} from './componentes.js';

export function filtrosAulas(edificios, filtros) {
  return `<form id="filtros-aulas" class="filters"><div class="filter-main">
    <label>Edificio<select name="edificio"><option value="">Todos los edificios</option>${opciones(edificios.map(x=>({id:x.id,nombre:`Edificio ${x.id}`})),filtros.edificio)}</select></label>
    <label>Piso<input name="piso" type="number" min="0" max="100" placeholder="Todos los pisos" value="${e(filtros.piso)}"></label>
    <label>Capacidad mínima<input name="capacidad" type="number" min="0" max="2000" placeholder="Cualquier capacidad" value="${e(filtros.capacidad)}"></label>
    <label>Disponibilidad<select name="estado"><option value="">Todos los estados</option>${opciones([{id:'disponible',nombre:'Disponibles'},{id:'ocupada',nombre:'Ocupadas'},{id:'por_liberarse',nombre:'Por liberarse'}], filtros.estado)}</select></label>
    <button class="button primary" type="submit">${icono('search')} Filtrar</button><button class="icon-button" type="button" id="limpiar-filtros" title="Limpiar filtros" aria-label="Limpiar filtros">${icono('refresh')}</button>
    </div><details ${filtros.fecha || filtros.inicio || filtros.hora ? 'open' : ''}><summary>Consultar otra fecha, hora o intervalo</summary><div class="interval">
    <label>Fecha<input name="fecha" type="date" value="${e(filtros.fecha)}"></label><label>Estado a las<input name="hora" type="time" value="${e(filtros.hora)}"></label>
    <label>Libre desde<input name="inicio" type="time" value="${e(filtros.inicio)}"></label><label>Libre hasta<input name="fin" type="time" value="${e(filtros.fin)}"></label></div></details>
    ${filtros.q ? `<p class="filters-note">Búsqueda: “${e(filtros.q)}”</p>` : ''}
    ${filtros.fecha || filtros.hora || filtros.inicio ? `<p class="filters-note">Consulta: ${e(filtros.fecha || 'hoy')} · ${e(filtros.hora || 'hora actual')}${filtros.inicio ? ` · aulas libres entre ${e(filtros.inicio)} y ${e(filtros.fin)}` : ''}. Las estadísticas superiores corresponden al momento actual.</p>` : ''}</form>`;
}

export function tarjetasAulas(aulas, datos, gestionar = false) {
  if (!aulas.length) return `<div class="panel">${vacio('No encontramos aulas con esos filtros', 'Prueba con otro edificio, capacidad o intervalo de tiempo.')}</div>`;
  return `<div class="rooms">${aulas.map(aula => {
    const actual = aula.actual;
    const titulo = actual ? actual.tipo_registro === 'horario' ? datos.asignaturas.find(a=>a.id===actual.asignatura)?.nombre : actual.motivo : 'Lista para tu próxima actividad';
    return `<article class="room"><div class="room-top"><span class="room-icon">${icono(aula.tipo === 'Laboratorio' ? 'dashboard' : 'aulas')}</span>${estado(aula.estado)}</div>
      <h3>${e(aula.nombre)}</h3><p class="room-location">Edificio ${e(aula.edificio)} <span>·</span> Piso ${aula.piso}</p>
      <div class="room-capacity">${icono('docentes')} ${aula.capacidad} estudiantes <span>${e(aula.tipo)}</span></div>
      <div class="room-activity ${actual ? '' : 'available'}"><strong>${e(titulo || 'Actividad académica')}</strong><p>${actual ? `Disponible a las ${horaBonita(aula.liberacion)}` : aula.proxima ? `Próxima actividad: ${fechaBonita(aula.proxima.fecha)} · ${horaBonita(aula.proxima.inicio)}` : 'Sin actividades programadas'}</p></div>
      <div class="room-bottom"><button class="link" data-detalle="${e(aula.id)}">Ver detalles ${icono('arrow')}</button>${gestionar ? acciones('aulas',aula.id) : `<span class="room-next">${actual ? `${aula.minutos_restantes} min de actividad` : 'Sin ocupación'}</span>`}</div></article>`;
  }).join('')}</div>`;
}

export function estadisticas(resumen) {
  const tarjetas = [
    ['Total de aulas', resumen.total, 'aulas', '', 'Espacios en el campus'],
    ['Disponibles', resumen.disponibles, 'check', 'green', 'Listas para utilizar'],
    ['Ocupadas', resumen.ocupadas, 'clock', 'red', 'Con una actividad en curso'],
    ['Reservas de hoy', resumen.reservas_hoy, 'reservas', '', 'Actividades extraordinarias'],
    ['Solicitudes', resumen.pendientes, 'solicitudes', 'amber', 'Pendientes de atención']
  ];
  return `<div class="stats">${tarjetas.map(([titulo,valor,icon,color,pie])=>`<article class="stat"><div class="stat-top">${titulo}<span class="stat-icon ${color}">${icono(icon)}</span></div><div class="stat-value">${valor}</div><div class="stat-foot">${pie}</div></article>`).join('')}</div>`;
}

export function detallesAula(aula, datos) {
  const horarios = datos.horarios.filter(h=>h.aula===aula.id).sort((a,b)=>a.dia-b.dia||a.inicio.localeCompare(b.inicio));
  const reservas = datos.reservas.filter(r=>r.aula===aula.id && r.estado==='activa').sort((a,b)=>(a.fecha+a.inicio).localeCompare(b.fecha+b.inicio));
  const nombre = (tipo,id) => e(datos[tipo].find(x=>x.id===id)?.nombre || id);
  const filas = horarios.map(h=>`<tr><td>${dias[h.dia]}<small>${h.inicio}–${h.fin}</small></td><td>${nombre('asignaturas',h.asignatura)}<small>${nombre('docentes',h.docente)}</small></td></tr>`);
  abrirModal(aula.nombre, `<div class="modal-body"><p class="form-intro">Estado actual del aula · Hora de Nicaragua</p>${estado(aula.estado)}<dl class="detail-grid"><div><dt>Ubicación</dt><dd>Edificio ${e(aula.edificio)} · Piso ${aula.piso}</dd></div><div><dt>Capacidad</dt><dd>${aula.capacidad} estudiantes</dd></div><div><dt>Disponible</dt><dd>${aula.liberacion ? horaBonita(aula.liberacion) : 'Ahora'}</dd></div><div><dt>Clase / reserva actual</dt><dd>${aula.actual ? `${aula.minutos_restantes} minutos restantes` : 'Ninguna'}</dd></div></dl>
    ${aula.proxima ? `<p class="form-intro">Próxima actividad: ${aula.proxima.tipo_registro === 'horario' ? nombre('asignaturas',aula.proxima.asignatura) : e(aula.proxima.motivo)} · ${fechaBonita(aula.proxima.fecha)} · ${horaBonita(aula.proxima.inicio)}</p>` : ''}
    ${aula.proxima_clase && aula.proxima?.tipo_registro !== 'horario' ? `<p class="form-intro">Próxima clase: ${nombre('asignaturas',aula.proxima_clase.asignatura)} · ${fechaBonita(aula.proxima_clase.fecha)} · ${horaBonita(aula.proxima_clase.inicio)}</p>` : ''}
    <div>${aula.equipamiento.map(eq=>`<span class="tag">${e(eq)}</span>`).join('')}</div><section class="detail-section"><h3>Horario académico semanal</h3>${tabla(['Día y hora','Asignatura y docente'],filas)}</section>
    <section class="detail-section"><h3>Reservas con fecha específica</h3>${reservas.length ? reservas.map(r=>`<p><strong>${e(r.motivo)}</strong> · ${fechaBonita(r.fecha)} · ${r.inicio}–${r.fin}</p>`).join('') : '<p>Sin reservas activas.</p>'}</section></div>`, '<div class="modal-footer"><button class="button" data-cerrar>Cerrar</button></div>');
}
