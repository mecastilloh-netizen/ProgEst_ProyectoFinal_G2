// Calendario semanal: seis columnas, escala horaria y edición de bloques.
import {escapar as e, opciones, dias, icono, acciones, tabla} from './componentes.js';
const minutos = hora => Number(hora.slice(0,2))*60+Number(hora.slice(3));

export function calendario(datos, aulaSeleccionada) {
  const horarios = datos.horarios.filter(h=>h.aula===aulaSeleccionada);
  const nombre = (tipo,id) => e(datos[tipo].find(x=>x.id===id)?.nombre || id);
  return `<section class="panel"><div class="panel-heading"><div><h2>Semana académica</h2><p>Horario recurrente · Lunes a sábado</p></div><div class="calendar-toolbar"><label>Aula<select id="aula-calendario">${opciones(datos.aulas,aulaSeleccionada)}</select></label><span class="badge blue">Semanal</span></div></div>
    <div class="calendar-scroll"><div class="calendar"><div class="calendar-head"><div>HORA</div>${dias.map(d=>`<div>${d}</div>`).join('')}</div><div class="calendar-body"><div class="calendar-time">${Array.from({length:24},(_,i)=>`<span style="top:${i*64+8}px">${String(i).padStart(2,'0')}:00</span>`).join('')}</div>
    ${dias.map((_,dia)=>`<div class="day-column">${horarios.filter(h=>h.dia===dia).map(h=>`<button class="class-block" style="top:${minutos(h.inicio)/60*64}px;height:${(minutos(h.fin)-minutos(h.inicio))/60*64}px" data-editar="horarios" data-id="${e(h.id)}" title="${nombre('asignaturas',h.asignatura)} · ${nombre('docentes',h.docente)} · ${e(h.aula)} · ${h.inicio}–${h.fin}"><strong>${nombre('asignaturas',h.asignatura)}</strong><span>${nombre('docentes',h.docente)}</span><span>${e(h.aula)} · ${h.inicio}–${h.fin}</span></button>`).join('')}</div>`).join('')}</div></div></div><div class="calendar-foot">${icono('info')} Selecciona una clase para editarla. Las reservas con fecha específica se consultan en Reservas.</div></section>
    <div class="section-heading"><h2>Clases de ${e(aulaSeleccionada)} <small>${horarios.length} registros</small></h2></div><div class="panel">${tabla(['Día','Horario','Asignatura','Docente','Acciones'],horarios.sort((a,b)=>a.dia-b.dia||a.inicio.localeCompare(b.inicio)).map(h=>`<tr><td>${dias[h.dia]}</td><td class="nowrap">${h.inicio}–${h.fin}</td><td>${nombre('asignaturas',h.asignatura)}</td><td>${nombre('docentes',h.docente)}</td><td>${acciones('horarios',h.id)}</td></tr>`))}</div>`;
}
