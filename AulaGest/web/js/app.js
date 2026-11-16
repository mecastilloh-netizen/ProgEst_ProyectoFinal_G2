// Coordinación de vistas, formularios y actualización periódica; JavaScript nativo.
import {api, consulta} from './api.js';
import {escapar as e, icono, tabla, opciones, vacio, acciones, notificar, formulario,
  confirmar, dias, prioridades, fechaBonita} from './componentes.js';
import {estadisticas, filtrosAulas, tarjetasAulas, detallesAula} from './aulas.js';
import {calendario} from './horarios.js';
import {listaReservas, listaSolicitudes} from './reservas.js';

const secciones = {dashboard:'Dashboard',aulas:'Aulas',horarios:'Horarios',reservas:'Reservas',docentes:'Docentes',asignaturas:'Asignaturas',edificios:'Edificios',solicitudes:'Solicitudes',historial:'Historial'};
const descripciones = {
  dashboard:'Una mirada a tus espacios y a la actividad de hoy.',aulas:'Encuentra el espacio adecuado para cada actividad.',
  horarios:'Organiza las clases y aprovecha cada hora de tu campus.',reservas:'Un espacio para cada actividad, sin cruces de horario.',
  docentes:'Las personas que hacen posible el aprendizaje.',asignaturas:'Organiza la oferta académica de tu campus.',
  edificios:'Conoce los espacios y las conexiones de tu campus.',solicitudes:'Cada solicitud, en el orden que corresponde.',
  historial:'Consulta los movimientos y cambios realizados en AulaGest.'
};
let datos = {}, vista = 'dashboard', filtros = {}, aulaCalendario = '', filtroReservas = '', textoHistorial = '';
let cargando = false, listo = false, desfaseReloj = 0;
const contenido = document.querySelector('#contenido');
const hoy = () => datos.resumen?.ahora.slice(0,10) || new Intl.DateTimeFormat('en-CA',{timeZone:'America/Managua'}).format(new Date());

function actualizarEstado(conectado) {
  const elemento = document.querySelector('#estado-sistema');
  elemento.classList.toggle('offline',!conectado);
  elemento.innerHTML = `<i></i> ${conectado ? 'Sistema activo' : 'Sin conexión'}`;
}

async function cargar(render = true) {
  if (cargando) return false;
  cargando = true;
  try {
    const nombres = ['resumen','aulas','edificios','docentes','asignaturas','horarios','reservas','solicitudes','historial','rutas'];
    const resultados = await Promise.all(nombres.map(nombre => api('/'+nombre)));
    const siguientes = Object.fromEntries(nombres.map((n,i)=>[n,resultados[i]]));
    siguientes.aulasFiltradas = Object.values(filtros).some(Boolean) ? await api('/aulas'+consulta(filtros)) : siguientes.aulas;
    datos = siguientes;
    desfaseReloj = new Date(datos.resumen.ahora).getTime()-Date.now();
    if (!datos.aulas.some(a=>a.id===aulaCalendario)) aulaCalendario = datos.aulas[0]?.id || '';
    listo = true;
    actualizarEstado(true);
    if (render) mostrar();
    return true;
  } catch (error) {
    actualizarEstado(false);
    if (!listo) contenido.innerHTML = `<div class="panel">${vacio('No pudimos conectar con AulaGest',error.message)}<div class="modal-footer"><button class="button primary" id="reintentar">Reintentar</button></div></div>`;
    throw error;
  } finally { cargando = false; }
}

function encabezado() {
  const crear = {aulas:'Nueva aula',horarios:'Agregar clase',reservas:'Nueva reserva',docentes:'Nuevo docente',asignaturas:'Nueva asignatura',edificios:'Nuevo edificio',solicitudes:'Nueva solicitud'};
  const botones = vista === 'dashboard'
    ? `<button class="button" data-ir="horarios">${icono('horarios')} Ver horarios</button><button class="button primary" data-nuevo="reservas">${icono('plus')} Nueva reserva</button>`
    : crear[vista] ? `<button class="button primary" data-nuevo="${vista}">${icono('plus')} ${crear[vista]}</button>` : '';
  return `<div class="page-heading"><div><p class="eyebrow">${vista==='dashboard'?'TU CAMPUS, EN TIEMPO REAL':'ADMINISTRACIÓN ACADÉMICA'}</p><h1>${vista==='dashboard'?'Vista general':secciones[vista]}</h1><p class="subtitle">${descripciones[vista]}</p></div><div class="heading-actions">${botones}</div></div>`;
}

function vistaAulas() {
  const inicio = vista === 'dashboard';
  return `${inicio ? `<div class="welcome"><span>${icono('edificios')}</span><div><h2>Todo listo para un nuevo día de aprendizaje</h2><p>Consulta la disponibilidad del campus y organiza tus actividades desde un solo lugar.</p></div><span class="live">Actualización cada 30 s</span></div>${estadisticas(datos.resumen)}` : ''}
    <div class="section-heading"><div><h2>${inicio?'Disponibilidad de aulas':'Espacios del campus'} <small>${datos.aulasFiltradas.length} aulas</small></h2><p>${inicio?'El espacio que necesitas, cuando lo necesitas.':'Administra los detalles, la capacidad y el equipamiento.'}</p></div><div class="legend"><span><i></i> Disponible</span><span><i class="red"></i> Ocupada</span><span><i class="amber"></i> Libre en ≤ 30 min</span></div></div>
    ${filtrosAulas(datos.edificios,filtros)}${tarjetasAulas(datos.aulasFiltradas,datos,!inicio)}`;
}

function vistaCatalogo(tipo) {
  const docente = tipo==='docentes';
  return `<div class="panel"><div class="panel-heading"><div><h2>${docente?'Directorio docente':'Catálogo de asignaturas'}</h2><p>${datos[tipo].length} registros · Información de ejemplo ficticia</p></div></div>${tabla(['Código','Nombre',docente?'Especialidad':'Créditos','Acciones'], datos[tipo].map(r=>`<tr><td><span class="tag">${e(r.id)}</span></td><td><strong>${e(r.nombre)}</strong></td><td>${e(docente?r.especialidad:r.creditos)}</td><td>${acciones(tipo,r.id)}</td></tr>`))}</div>`;
}

function vistaEdificios() {
  return `<div class="building-grid">${datos.edificios.map(b=>`<article class="panel building-card"><span class="building-icon">${icono('edificios')}</span><p class="eyebrow">EDIFICIO ${e(b.id)}</p><h3>${e(b.nombre)}</h3><p>${e(b.descripcion)}</p><span class="tag">${datos.aulas.filter(a=>a.edificio===b.id).length} aulas</span><span class="tag">${datos.aulas.filter(a=>a.edificio===b.id).reduce((s,a)=>s+a.capacidad,0)} plazas</span>${acciones('edificios',b.id)}</article>`).join('')}</div>
    <section class="panel panel-pad"><div class="section-heading" style="margin-top:0"><div><h2>Encuentra tu camino</h2><p>Ruta con menos conexiones a través de edificios y pasillos.</p></div>${icono('route')}</div><form id="ruta-form" class="route-form"><label>Origen<select name="origen">${opciones(datos.rutas.vertices.map(v=>({id:v,nombre:v})),datos.aulas[0]?.id)}</select></label><label>Destino<select name="destino">${opciones(datos.rutas.vertices.map(v=>({id:v,nombre:v})),datos.aulas.at(-1)?.id)}</select></label><button class="button primary" type="submit">${icono('route')} Buscar ruta</button></form><div id="resultado-ruta" class="route-result" aria-live="polite"><span class="muted">Selecciona dos lugares para consultar cómo llegar.</span></div></section>
    <div class="section-heading"><div><h2>Conexiones del campus</h2><p>Pasillos de doble sentido. Las aulas se conectan automáticamente a su piso.</p></div><button class="button" id="editar-conexiones">${icono('plus')} Conectar edificios</button></div><div class="panel panel-pad"><div class="connections" style="margin-top:0">${datos.edificios.flatMap(b=>b.conexiones.filter(c=>b.id<c).map(c=>`<span>Edificio ${e(b.id)} ↔ Edificio ${e(c)} <button class="icon-button danger" data-desconectar="${e(b.id)}" data-destino="${e(c)}" aria-label="Eliminar conexión ${e(b.id)} ${e(c)}">${icono('close')}</button></span>`)).join('') || '<p class="muted">No hay conexiones entre edificios.</p>'}</div><details class="detail-section"><summary>Ver todas las conexiones (${datos.rutas.conexiones.length})</summary><div class="connections connection-list">${datos.rutas.conexiones.map(([a,b])=>`<span>${e(a)} ↔ ${e(b)}</span>`).join('')}</div></details></div>`;
}

function vistaHistorial() {
  const registros = datos.historial.filter(r=>(r.accion+' '+r.detalle).toLocaleLowerCase().includes(textoHistorial.toLocaleLowerCase()));
  return `<div class="panel"><div class="panel-heading"><div><h2>Registro de actividad</h2><p>Los cambios se conservan al reiniciar el sistema.</p></div><form id="filtro-historial" class="route-form"><input name="q" value="${e(textoHistorial)}" placeholder="Buscar movimiento…" aria-label="Buscar movimiento"><button class="button" type="submit">Buscar</button></form></div>${tabla(['Fecha','Acción','Detalle'],registros.map(r=>`<tr><td class="nowrap">${fechaBonita(r.fecha)}<small>${new Date(r.fecha).toLocaleTimeString('es-NI',{timeZone:'America/Managua'})}</small></td><td><strong>${e(r.accion)}</strong></td><td>${e(r.detalle)}</td></tr>`))}</div>`;
}

function mostrar() {
  if (!listo) return;
  document.querySelector('#ubicacion').textContent = secciones[vista];
  document.title = `${secciones[vista]} · AulaGest`;
  document.querySelectorAll('nav a').forEach(a=>{
    const activa = a.dataset.vista===vista;
    a.classList.toggle('active',activa);
    if (activa) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current');
  });
  let cuerpo;
  if (vista==='dashboard' || vista==='aulas') cuerpo = vistaAulas();
  else if (vista==='horarios') cuerpo = datos.aulas.length ? calendario(datos,aulaCalendario) : `<div class="panel">${vacio('Primero agrega un aula','Necesitas un aula para comenzar a programar clases.')}</div>`;
  else if (vista==='reservas') cuerpo = listaReservas(datos,filtroReservas);
  else if (vista==='solicitudes') cuerpo = listaSolicitudes(datos);
  else if (vista==='edificios') cuerpo = vistaEdificios();
  else if (vista==='historial') cuerpo = vistaHistorial();
  else cuerpo = vistaCatalogo(vista);
  contenido.innerHTML = encabezado()+cuerpo;
  const calendarioScroll = contenido.querySelector('.calendar-scroll');
  if (calendarioScroll) calendarioScroll.scrollTop = 64*6.5;
}

function navegar() {
  const seleccion = location.hash.slice(1);
  vista = Object.hasOwn(secciones,seleccion) ? seleccion : 'dashboard';
  document.querySelector('#sidebar').classList.remove('open');
  document.querySelector('#menu').setAttribute('aria-expanded','false');
  mostrar();
}

async function despuesDeGuardar(mensaje) {
  notificar(mensaje);
  try { await cargar(); }
  catch { notificar('El cambio se guardó, pero no se pudo actualizar la vista. Reintenta la consulta.',true); }
}

function editar(tipo, id) {
  const valores = id ? {...datos[tipo].find(r=>r.id===id)} : {};
  let campos = [];
  const campoCodigo = {nombre:'id',etiqueta:'Código',fijo:!!id,maxlength:24,patron:'[A-Za-z0-9_\\-]+',ayuda:id?'El código conserva las referencias del registro.':'Letras, números o guiones. Ejemplo: A301.'};
  const campoNombre = {nombre:'nombre',etiqueta:'Nombre'};
  const selector = (nombre,etiqueta,registros,extra={}) => ({nombre,etiqueta,opciones:registros.map(r=>({id:r.id,nombre:r.nombre})),...extra});
  if (tipo==='aulas') {
    valores.equipamiento = valores.equipamiento?.join(', ') || '';
    campos = [campoCodigo,campoNombre,selector('edificio','Edificio',datos.edificios.map(b=>({id:b.id,nombre:`${b.id} · ${b.nombre}`}))),
      {nombre:'piso',etiqueta:'Piso',tipo:'number',min:0,max:100,valor:1},
      {nombre:'capacidad',etiqueta:'Capacidad',tipo:'number',min:1,max:2000,valor:35},
      {nombre:'tipo',etiqueta:'Tipo de aula',valor:'Teórica',maxlength:50},
      {nombre:'equipamiento',etiqueta:'Equipamiento',ancho:true,opcional:true,maxlength:1200,ayuda:'Separa los elementos con comas: Proyector, Pizarra, Computadoras.'}];
  } else if (['docentes','asignaturas','edificios'].includes(tipo)) {
    campos = [campoCodigo,campoNombre];
    if (tipo==='docentes') campos.push({nombre:'especialidad',etiqueta:'Especialidad',ancho:true});
    if (tipo==='asignaturas') campos.push({nombre:'creditos',etiqueta:'Créditos',tipo:'number',min:1,max:20,valor:4});
    if (tipo==='edificios') campos.push({nombre:'descripcion',etiqueta:'Descripción',tipo:'textarea',ancho:true});
  } else {
    if (!datos.aulas.length || !datos.docentes.length || (tipo==='horarios' && !datos.asignaturas.length)) {
      notificar('Registra primero aulas, docentes y las asignaturas necesarias.',true); return;
    }
    campos = [selector('aula','Aula',datos.aulas,{valor:aulaCalendario}),selector('docente','Docente',datos.docentes)];
    if (tipo==='horarios') campos.push(selector('asignatura','Asignatura',datos.asignaturas),
      {nombre:'dia',etiqueta:'Día de la semana',numerico:true,opciones:dias.map((d,i)=>({id:i,nombre:d}))});
    else campos.push({nombre:'fecha',etiqueta:'Fecha',tipo:'date',valor:hoy()}, {nombre:'motivo',etiqueta:'Motivo de la actividad',maxlength:300});
    campos.push({nombre:'inicio',etiqueta:'Hora inicial',tipo:'time',valor:'16:00'}, {nombre:'fin',etiqueta:'Hora final',tipo:'time',valor:'17:00'},
      {nombre:'asistentes',etiqueta:'Número de asistentes',tipo:'number',min:1,max:2000,valor:20});
    if (tipo==='solicitudes') campos.push({nombre:'prioridad',etiqueta:'Prioridad',numerico:true,valor:3,opciones:prioridades.map((p,i)=>({id:i+1,nombre:`${i+1} · ${p}`}))});
  }
  const singular = {aulas:'aula',docentes:'docente',asignaturas:'asignatura',edificios:'edificio',horarios:'clase semanal',reservas:'reserva',solicitudes:'solicitud'};
  const ayuda = tipo==='solicitudes' ? 'La solicitud se agrega a la cola. La disponibilidad se verifica cuando se atiende.' : tipo==='horarios' ? 'La clase se repetirá cada semana. El servidor comprueba los cruces con clases y reservas.' : tipo==='reservas' ? 'Reserva extraordinaria para una fecha específica. El aula debe estar libre durante todo el intervalo.' : '';
  formulario(`${id?'Editar':'Registrar'} ${singular[tipo]}`,campos,valores,async entrada=>{
    if (tipo==='aulas') entrada.equipamiento = entrada.equipamiento.split(',').map(s=>s.trim()).filter(Boolean);
    await api(`/${tipo}${id?'/'+encodeURIComponent(id):''}`,id?'PUT':'POST',entrada);
    await despuesDeGuardar('Los cambios se guardaron correctamente.');
  },ayuda);
}

async function ejecutarClick(evento) {
  const boton = evento.target.closest('button');
  if (!boton) return;
  if (boton.dataset.nuevo) editar(boton.dataset.nuevo);
  if (boton.dataset.editar) editar(boton.dataset.editar,boton.dataset.id);
  if (boton.dataset.ir) location.hash = boton.dataset.ir;
  if (boton.dataset.detalle) detallesAula(await api('/aulas/'+encodeURIComponent(boton.dataset.detalle)),datos);
  if (boton.dataset.eliminar) {
    const tipo = boton.dataset.eliminar, id = boton.dataset.id;
    confirmar(tipo==='reservas'?'Cancelar reserva':'Eliminar registro',tipo==='reservas'?'La reserva dejará de ocupar el aula. Se conservará su registro como cancelado.':`Se eliminará ${id}. Si tiene registros asociados, el servidor impedirá la operación.`,async()=>{
      await api(`/${tipo}/${encodeURIComponent(id)}`,'DELETE');
      await despuesDeGuardar(tipo==='reservas'?'Reserva cancelada.':'Registro eliminado.');
    },tipo==='reservas'?'Cancelar reserva':'Eliminar');
  }
  if (boton.id==='atender-solicitud') {
    const siguiente = datos.solicitudes.pendientes[0];
    if (!siguiente) return;
    confirmar('Atender siguiente solicitud',`${siguiente.motivo} · Aula ${siguiente.aula}. Se comprobará la disponibilidad: si hay un conflicto, quedará rechazada con el motivo registrado.`,async()=>{
      const resultado = await api('/solicitudes/atender','POST',{});
      await despuesDeGuardar(`Solicitud ${resultado.estado}. ${resultado.resultado}`);
    },'Comprobar y atender');
  }
  if (boton.id==='editar-conexiones') {
    formulario('Conectar edificios',[{nombre:'origen',etiqueta:'Edificio de origen',opciones:datos.edificios},{nombre:'destino',etiqueta:'Edificio de destino',opciones:datos.edificios}],{},async entrada=>{
      await api('/conexiones','POST',entrada); await despuesDeGuardar('Conexión guardada en ambos sentidos.');
    });
  }
  if (boton.dataset.desconectar) confirmar('Eliminar conexión','Las aulas y los edificios se conservarán; solo se retirará este paso entre edificios.',async()=>{
    await api('/conexiones','DELETE',{origen:boton.dataset.desconectar,destino:boton.dataset.destino});
    await despuesDeGuardar('Conexión eliminada.');
  },'Eliminar conexión');
  if (boton.id==='limpiar-filtros') {
    filtros = {}; document.querySelector('#busqueda-global input').value=''; await cargar();
  }
  if (boton.id==='reintentar') await cargar();
}

contenido.addEventListener('click',evento=>ejecutarClick(evento).catch(error=>notificar(error.message,true)));
contenido.addEventListener('change',evento=>{
  if (evento.target.id==='aula-calendario') { aulaCalendario=evento.target.value; mostrar(); }
  if (evento.target.id==='filtro-reservas') { filtroReservas=evento.target.value; mostrar(); }
});
contenido.addEventListener('submit',async evento=>{
  evento.preventDefault();
  const valores = Object.fromEntries(new FormData(evento.target));
  try {
    if (evento.target.id==='filtros-aulas') {
      const siguientes = {...valores,q:filtros.q || ''};
      const aulas = await api('/aulas'+consulta(siguientes));
      filtros = siguientes; datos.aulasFiltradas = aulas; mostrar();
    }
    if (evento.target.id==='ruta-form') {
      const resultado = await api('/rutas'+consulta(valores));
      document.querySelector('#resultado-ruta').innerHTML = resultado.ruta.length ? resultado.ruta.map(lugar=>`<span class="route-node">${e(lugar)}</span>`).join(icono('arrow')) : '<span class="muted">No existe una ruta entre estos lugares. Revisa las conexiones de los edificios.</span>';
    }
    if (evento.target.id==='filtro-historial') { textoHistorial=valores.q; mostrar(); }
  } catch (error) { notificar(error.message,true); }
});

document.querySelector('#navegacion').innerHTML = Object.entries(secciones).map(([clave,nombre])=>`<a href="#${clave}" data-vista="${clave}">${icono(clave)}<span>${nombre}</span></a>`).join('');
document.querySelector('#busqueda-global').onsubmit = async evento=>{
  evento.preventDefault();
  filtros.q = new FormData(evento.target).get('q').trim();
  location.hash='aulas';
  try { await cargar(); } catch (error) { notificar(error.message,true); }
};
document.querySelector('#menu').onclick = ()=>{
  const abierto = document.querySelector('#sidebar').classList.toggle('open');
  document.querySelector('#menu').setAttribute('aria-expanded',String(abierto));
};
document.addEventListener('click',evento=>{
  if (!evento.target.closest('#sidebar') && !evento.target.closest('#menu')) {
    document.querySelector('#sidebar').classList.remove('open');
    document.querySelector('#menu').setAttribute('aria-expanded','false');
  }
});
window.addEventListener('hashchange',navegar);
function reloj() {
  const momento = new Date(Date.now()+desfaseReloj);
  document.querySelector('#fecha-actual').textContent = momento.toLocaleDateString('es-NI',{day:'numeric',month:'short',year:'numeric',timeZone:'America/Managua'});
  document.querySelector('#hora-actual').textContent = momento.toLocaleTimeString('es-NI',{hour:'2-digit',minute:'2-digit',second:'2-digit',timeZone:'America/Managua'});
}
setInterval(reloj,1000); reloj(); navegar();
cargar().catch(error=>notificar(error.message,true));
setInterval(()=>{
  // Evita interrumpir escritura, edición, selección de una ruta o lectura del calendario.
  if (document.hidden || document.querySelector('#modal').open || ['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName)) return;
  cargar(vista==='dashboard' || vista==='aulas').catch(()=>{});
},30000);
