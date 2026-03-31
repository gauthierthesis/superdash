// ── Sécurité : échappement HTML ───────────────────────
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function safeUrl(url) {
  try {
    const u = new URL(url);
    return (u.protocol === 'https:' || u.protocol === 'http:') ? url : '#';
  } catch { return '#'; }
}

// ── Constantes ────────────────────────────────────────
const WIDGETS = ['widget-twitter','widget-weather','widget-tram','widget-calendar','widget-todo'];
const LABELS  = {'widget-twitter':'Actualités IA','widget-weather':'Météo','widget-tram':'Tram','widget-calendar':'Calendrier','widget-todo':'Tâches'};

// ── Préférences localStorage ──────────────────────────
function loadPrefs(){ try{return JSON.parse(localStorage.getItem('dash_prefs')||'{}')}catch{return{}} }
function savePrefs(p){ localStorage.setItem('dash_prefs',JSON.stringify(p)) }

// ── Horloge ───────────────────────────────────────────
function updateClock(){
  const n=new Date();
  document.getElementById('clock').textContent=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');
  const days=['Dimanche','Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'];
  const mths=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
  document.getElementById('date-display').textContent=`${days[n.getDay()]} ${n.getDate()} ${mths[n.getMonth()]} ${n.getFullYear()}`;
}
setInterval(updateClock,1000); updateClock();

// ── Système modulable ─────────────────────────────────
function toggleWidget(id){
  const el=document.getElementById(id);
  const p=loadPrefs();
  p[id+'_hidden']=el.classList.toggle('widget-hidden');
  savePrefs(p); refreshToggles(); refreshConfigRows();
}
function resizeWidget(id,size){
  document.getElementById(id).dataset.size=size;
  const p=loadPrefs(); p[id+'_size']=size; savePrefs(p); refreshConfigRows();
}
function setLayout(name){
  document.getElementById('main-grid').className='layout-'+name;
  const p=loadPrefs(); p['layout']=name; savePrefs(p);
  document.querySelectorAll('.btn-layout').forEach(b=>b.classList.remove('active'));
  const b=document.getElementById('btn-layout-'+name); if(b)b.classList.add('active');
}

// Boutons rapides header
function buildToggles(){
  document.getElementById('widget-toggles').innerHTML=WIDGETS.map(id=>{
    const h=document.getElementById(id).classList.contains('widget-hidden');
    return `<button class="widget-toggle ${h?'off-toggle':''}" id="htoggle-${id}" onclick="toggleWidget('${id}')"><span class="dot"></span>${esc(LABELS[id])}</button>`;
  }).join('');
}
function refreshToggles(){
  WIDGETS.forEach(id=>{
    const b=document.getElementById('htoggle-'+id); if(!b)return;
    b.classList.toggle('off-toggle',document.getElementById(id).classList.contains('widget-hidden'));
  });
}

// Panel config
function openConfig() { document.getElementById('config-panel').classList.add('open'); refreshConfigRows(); }
function closeConfig(){ document.getElementById('config-panel').classList.remove('open'); }
function refreshConfigRows(){
  document.getElementById('config-rows').innerHTML=WIDGETS.map(id=>{
    const el=document.getElementById(id);
    const hidden=el.classList.contains('widget-hidden');
    const size=el.dataset.size||'m';
    return `<div class="config-row">
      <div><div class="config-row-label">${esc(LABELS[id])}</div><div class="config-row-sub">${hidden?'Masqué':'Visible'} · Taille ${esc(size.toUpperCase())}</div></div>
      <div class="config-row-right">
        <button class="size-btn ${size==='s'?'active':''}" onclick="resizeWidget('${id}','s');refreshConfigRows()">S</button>
        <button class="size-btn ${size==='m'?'active':''}" onclick="resizeWidget('${id}','m');refreshConfigRows()">M</button>
        <button class="size-btn ${size==='l'?'active':''}" onclick="resizeWidget('${id}','l');refreshConfigRows()">L</button>
        <button class="toggle-sw ${hidden?'':'on'}" onclick="toggleWidget('${id}');refreshConfigRows()"></button>
      </div>
    </div>`;
  }).join('');
}

// Appliquer les prefs sauvegardées
(function(){
  const p=loadPrefs();
  WIDGETS.forEach(id=>{ if(p[id+'_hidden'])document.getElementById(id).classList.add('widget-hidden'); if(p[id+'_size'])document.getElementById(id).dataset.size=p[id+'_size']; });
  if(p.layout)setLayout(p.layout); else document.getElementById('btn-layout-auto').classList.add('active');
  buildToggles();
})();
document.getElementById('config-panel').addEventListener('click',function(e){if(e.target===this)closeConfig();});

// ── Météo ─────────────────────────────────────────────
const WMO={0:'Ciel dégagé',1:'Peu nuageux',2:'Partiellement nuageux',3:'Couvert',45:'Brouillard',48:'Brouillard givrant',51:'Bruine légère',53:'Bruine',55:'Bruine forte',61:'Pluie légère',63:'Pluie',65:'Pluie forte',71:'Neige légère',73:'Neige',75:'Neige forte',80:'Averses légères',81:'Averses',82:'Averses fortes',95:'Orage',96:'Orage avec grêle',99:'Orage violent'};
function wIcon(c,anim=true){
  const h=new Date().getHours(),n=h<6||h>=21;
  if(!anim){if(c===0)return n?'🌙':'☀️';if(c<=2)return n?'🌙':'🌤';if(c<=3)return'☁️';if(c<=55)return'🌦';if(c<=67)return'🌧';if(c<=77)return'❄️';if(c<=82)return'🌧';return'⛈';}
  if(c===0&&n)return`<div class="icon-night">🌙</div>`;
  if(c===0)return`<div class="icon-sun"></div>`;
  if(c<=2)return`<div class="icon-partly"><div class="partly-sun"></div><div class="partly-cloud"></div></div>`;
  if(c<=3)return`<div class="icon-cloud"><div class="cloud-body"></div></div>`;
  if(c<=55)return`<div class="icon-rain"><div class="rain-cloud"></div><div class="rain-drops"><div class="rain-drop"></div><div class="rain-drop"></div><div class="rain-drop"></div><div class="rain-drop"></div><div class="rain-drop"></div></div></div>`;
  if(c<=77)return`<div class="icon-snow"><div class="snow-cloud"></div><div class="snow-flakes"><div class="snow-flake">❄</div><div class="snow-flake">❄</div><div class="snow-flake">❄</div><div class="snow-flake">❄</div></div></div>`;
  if(c>=95)return`<div class="icon-thunder"><div class="thunder-cloud"></div><div class="thunder-bolt">⚡</div></div>`;
  return`<div class="icon-rain"><div class="rain-cloud"></div><div class="rain-drops"><div class="rain-drop"></div><div class="rain-drop"></div><div class="rain-drop"></div></div></div>`;
}
async function loadWeather(){
  try{
    const d=await(await fetch('/api/weather')).json();
    if(!d.temp&&d.temp!==0){document.getElementById('weather-status').classList.add('error');return;}
    const fc=d.forecast.map(f=>`<div class="forecast-day"><div class="forecast-label">${esc(f.day)}</div><div class="forecast-icon">${wIcon(f.code,false)}</div><div class="forecast-temps"><span class="forecast-max">${esc(String(f.max))}°</span><span class="forecast-min"> ${esc(String(f.min))}°</span></div></div>`).join('');
    document.getElementById('weather-data').innerHTML=`<div class="weather-main"><div><div class="weather-temp">${esc(String(d.temp))}°</div><div class="weather-feels">Ressenti ${esc(String(d.feels_like))}°</div><div class="weather-desc">${esc(WMO[d.code]||'Variable')}</div></div><div class="weather-icon-wrap">${wIcon(d.code)}</div></div><div class="weather-stats"><div class="weather-stat"><span class="weather-stat-icon">💧</span><span class="weather-stat-val">${esc(String(d.humidity))}%</span></div><div class="weather-stat"><span class="weather-stat-icon">💨</span><span class="weather-stat-val">${esc(String(d.wind))} km/h</span></div></div><div class="weather-forecast">${fc}</div>`;
    document.getElementById('weather-status').classList.remove('off','error');
  }catch{document.getElementById('weather-status').classList.add('error');}
}
loadWeather(); setInterval(loadWeather,600000);

// ── Tram ──────────────────────────────────────────────
function minClass(m){return m<=4?'urgent':m<=7?'warning':'ok';}
async function loadTram(){
  const container=document.getElementById('tram-data');
  const dot=document.getElementById('tram-status');
  const stopHdr=`<p class="tram-stop-name">Albert I — Jardin des plantes</p>`;
  try{
    const data=await(await fetch('/api/tram')).json();
    if(data.error){
      const isNoStop=data.error.includes('stop_ids');
      container.innerHTML=stopHdr+`<div class="tram-banner">⚠ ${isNoStop?'Stop IDs à reconfigurer — ':''}Données temps réel indisponibles.<br>Consultez <a href="https://www.tam-voyages.com" target="_blank" rel="noopener">tam-voyages.com</a> pour les horaires.</div>`;
      dot.classList.add('error'); return;
    }
    if(!Array.isArray(data)||!data.length){
      container.innerHTML=stopHdr+`<p class="loading">Aucun passage dans l'heure</p>`;
      dot.classList.remove('error'); return;
    }
    dot.classList.remove('error');
    container.innerHTML=stopHdr+data.map(p=>{
      const cls=minClass(p.minutes);
      const lbl=p.minutes===0?'À quai':`${esc(String(p.minutes))} min`;
      return`<div class="tram-passage"><div class="tram-left"><div class="tram-line-badge" style="background:${esc(p.color)}">${esc(p.line)}</div><div><div class="tram-direction">${esc(p.direction)}</div><div class="${p.realtime?'tram-realtime':'tram-theoretical'}">${p.realtime?'● temps réel':'○ théorique'}</div></div></div><div><div class="tram-minutes ${cls}">${lbl}</div><div class="tram-time-label">${esc(p.time)}</div></div></div>`;
    }).join('');
  }catch{
    dot.classList.add('error');
    container.innerHTML=stopHdr+`<div class="tram-banner">⚠ Erreur de connexion au serveur.<br>Consultez <a href="https://www.tam-voyages.com" target="_blank" rel="noopener">tam-voyages.com</a> pour les horaires.</div>`;
  }
}
loadTram(); setInterval(loadTram,30000);

// ── Actualités ────────────────────────────────────────
async function loadNews(){
  try{
    const arts=await(await fetch('/api/news')).json();
    if(!arts.length){document.getElementById('news-feed').innerHTML=`<p class="loading">Aucun article récent</p>`;return;}
    document.getElementById('news-status').classList.remove('off');
    document.getElementById('news-feed').innerHTML=arts.map(a=>`<a class="news-item" href="${safeUrl(a.link)}" target="_blank" rel="noopener noreferrer"><div class="news-icon">${esc(a.icon)}</div><div class="news-content"><div class="news-source-row"><span class="news-source">${esc(a.source)}</span><span class="news-time">${esc(a.time)}</span></div><div class="news-title">${esc(a.title)}</div><div class="news-summary">${esc(a.summary)}</div></div></a>`).join('');
  }catch{document.getElementById('news-status').classList.add('error');}
}
loadNews(); setInterval(loadNews,120000);

// ── Calendrier ────────────────────────────────────────
async function loadCalendar(){try{renderCal(await(await fetch('/api/events')).json());}catch{renderCal([]);}}
function renderCal(evts){
  const now=new Date();
  let h=`<div class="cal-events-title">À venir</div>`;
  h+=evts.length?evts.slice(0,5).map(e=>`<div class="cal-event-item"><div class="cal-event-dot"></div><div style="flex:1"><div class="cal-event-title">${esc(e.title)}</div><div class="cal-event-time">${esc(e.date)}</div></div><button class="cal-event-del" onclick="delEvt('${esc(e.id)}')">×</button></div>`).join(''):`<p class="loading">Aucun événement</p>`;
  const mon=new Date(now); mon.setDate(now.getDate()-((now.getDay()+6)%7));
  h+=`<hr class="cal-divider"><div class="cal-week-title">Cette semaine</div><div class="cal-week-grid">`;
  ['Lu','Ma','Me','Je','Ve','Sa','Di'].forEach(d=>h+=`<div class="cal-week-day-name">${d}</div>`);
  for(let i=0;i<7;i++){const d=new Date(mon);d.setDate(mon.getDate()+i);h+=`<div class="cal-week-day ${d.toDateString()===now.toDateString()?'today':''}">${d.getDate()}</div>`;}
  h+=`</div><button class="cal-add-btn" onclick="openModal()">+ Ajouter un événement</button>`;
  document.getElementById('calendar-body').innerHTML=h;
}
async function delEvt(id){await fetch(`/api/events/${encodeURIComponent(id)}`,{method:'DELETE'});loadCalendar();}
loadCalendar(); setInterval(loadCalendar,60000);

// ── Modal ─────────────────────────────────────────────
function openModal(){
  document.getElementById('modal-overlay').classList.add('open');
  const n=new Date(); n.setMinutes(Math.ceil(n.getMinutes()/15)*15);
  document.getElementById('event-date').value=new Date(n.getTime()-n.getTimezoneOffset()*60000).toISOString().slice(0,16);
  document.getElementById('event-title').focus();
}
function closeModal(){document.getElementById('modal-overlay').classList.remove('open');document.getElementById('event-title').value='';}
async function saveEvent(){
  const t=document.getElementById('event-title').value.trim(),d=document.getElementById('event-date').value;
  if(!t||!d)return;
  await fetch('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t,date:d})});
  closeModal(); loadCalendar();
}
document.getElementById('modal-overlay').addEventListener('click',function(e){if(e.target===this)closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeModal();closeConfig();}});

// ── Todo ──────────────────────────────────────────────
let todos=[];
async function loadTodos(){try{todos=await(await fetch('/api/todos')).json();}catch{todos=[];}renderTodos();}
async function saveTodos(){await fetch('/api/todos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(todos)});}
function renderTodos(){
  const r=todos.filter(t=>!t.done).length;
  document.getElementById('todo-count').textContent=todos.length===0?'':r===0?'✓ Tout fait':`${r} restante${r>1?'s':''}`;
  document.getElementById('todo-list').innerHTML=todos.map((t,i)=>`<div class="todo-item ${t.done?'done':''}" onclick="toggleTodo(${i})"><div class="todo-checkbox"></div><span class="todo-text">${esc(t.text)}</span><span class="todo-delete" onclick="delTodo(event,${i})">×</span></div>`).join('');
}
function addTodo(){const inp=document.getElementById('todo-input'),txt=inp.value.trim().slice(0,500);if(!txt)return;todos.push({text:txt,done:false});inp.value='';saveTodos();renderTodos();}
function toggleTodo(i){todos[i].done=!todos[i].done;saveTodos();renderTodos();}
function delTodo(e,i){e.stopPropagation();todos.splice(i,1);saveTodos();renderTodos();}
document.getElementById('todo-input').addEventListener('keydown',e=>{if(e.key==='Enter')addTodo();});
loadTodos();
