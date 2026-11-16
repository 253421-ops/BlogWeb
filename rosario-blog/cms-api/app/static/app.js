/* Interfaz del CMS «Sigo intentándolo». JavaScript sin dependencias; habla con la API en /api (mismo origen). */
'use strict';
const API = '/api';
const LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M21 3a13 13 0 1 0 8 22A11 11 0 0 1 21 3z" fill="#f5c451"/></svg>';
const THEME_SLUG = 'tema-visual';
const DEFAULT_THEME = { scene: 'noche', accent: null, font: 'manuscrita', blog: 'tarjetas' };
const SCENES = {
  noche: { name: 'Noche estrellada', note: 'Cielo azul con luna, montañas, un pueblo y un campo de flores.', c: ['#050a24', '#10265e', '#4d86a8', '#1d3b22', '#f8e7a0', '#f5c451'] },
  atardecer: { name: 'Atardecer', note: 'El mismo paisaje con cielo morado y naranja.', c: ['#1b1140', '#7a3a86', '#ff9a5c', '#34402a', '#fff0c4', '#ffb36b'] },
  amanecer: { name: 'Amanecer', note: 'Cielo rosado y verdes suaves.', c: ['#1a2a5a', '#c46a9a', '#ffc9a3', '#3f6b4a', '#fff7e0', '#ff8fa3'] },
};
const FONT_NAMES = { manuscrita: 'Manuscrita (cuento)', clasica: 'Clásica (serif)', moderna: 'Moderna (sans)' };

const S = {
  token: localStorage.getItem('tk') || '', user: null, blogs: [], blog: null, menu: '', dirty: localStorage.getItem('dirty') === '1', view: 'login', posts: [], pages: [], cats: [], builds: [],
  edit: null, siteUrl: '', flash: '', sel: 0, building: false, theme: { ...DEFAULT_THEME }, themePage: null, metrics: null, q: '', pendingG: false, modal: null,
};
const $ = (s, r = document) => r.querySelector(s);
const esc = (t) => String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const markDirty = () => { S.dirty = true; localStorage.setItem('dirty', '1'); };
const fmtDate = (d) => (d || '').slice(0, 10);

const SECTIONS = ['Dibujos', 'Proyectos', 'Pensamientos', 'Innovación textil'];
const missingSections = () => SECTIONS.filter((n) => !S.cats.some((c) => c.name.toLowerCase() === n.toLowerCase()));
function shrink(file, max = 1400) {                                   // reduce la foto antes de subirla: pesa menos y carga rápido
  return new Promise((res, rej) => {
    const im = new Image(), url = URL.createObjectURL(file);
    im.onload = () => { const k = Math.min(1, max / Math.max(im.width, im.height)), c = document.createElement('canvas'); c.width = Math.round(im.width * k); c.height = Math.round(im.height * k);
      c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); URL.revokeObjectURL(url); c.toBlob((b) => (b ? res(b) : rej(new Error('No se pudo reducir la imagen'))), 'image/jpeg', 0.85); };
    im.onerror = () => rej(new Error('Ese archivo no es una imagen')); im.src = url;
  });
}

/* ---------- red ---------- */
async function api(method, path, body, form) {
  const opt = { method, headers: {} };
  if (S.token) opt.headers.Authorization = 'Bearer ' + S.token;
  if (form) opt.body = form; else if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
  const r = await fetch(API + path, opt);
  if (r.status === 204) return null;
  let data = null; try { data = await r.json(); } catch (e) { /* sin cuerpo */ }
  if (r.status === 401 && S.token) { logout('Tu sesión terminó. Entra de nuevo.'); throw new Error('401'); }
  if (!r.ok) throw new Error((data && (data.message || (Array.isArray(data.detail) && data.detail[0] && data.detail[0].msg))) || 'Error ' + r.status);
  return data;
}

/* ---------- avisos ---------- */
function toast(msg, action, ms = 5000) {
  const box = $('#toast'), el = document.createElement('div'); while (box.children.length >= 1) box.firstChild.remove();
  el.innerHTML = `<span>${esc(msg)}</span>`;
  if (action) { const b = document.createElement('button'); b.textContent = action.label; b.onclick = () => { action.fn(); el.remove(); }; el.append(b); }
  box.append(el); setTimeout(() => el.remove(), ms);
}

/* ---------- sesión ---------- */
function logout(msg) { localStorage.removeItem('tk'); S.token = ''; S.user = null; S.view = 'login'; S.flash = msg || ''; render(); }
async function boot() {
  try { const c = await fetch(API + '/config').then((r) => r.json()); S.siteUrl = c.siteUrl || ''; } catch (e) { /* sin config */ }
  if (!S.token) return render();
  try { S.user = await api('GET', '/auth/me'); S.blogs = await api('GET', '/blogs'); } catch (e) { return; }
  const saved = Number(localStorage.getItem('blog'));
  S.blog = S.blogs.find((b) => b.id === saved) || S.blogs[0] || null;
  if (!S.blog) { S.view = 'onboarding'; return render(); }
  await go(localStorage.getItem('view') || 'posts');
}

/* ---------- navegación ---------- */
const MENU = [
  ['docs', 'Documentos', [['posts', 'Entradas', 'g e'], ['pages', 'Páginas', 'g p']]],
  ['tpl', 'Plantillas', [['look', 'Diseño del sitio', 'g a']]],
  ['met', 'Métricas', [['perf', 'Resumen de visitas', 'g r']]],
];
const groupOf = (v) => ({ posts: 'docs', 'edit-post': 'docs', pages: 'docs', 'edit-page': 'docs', look: 'tpl', perf: 'met' }[v]);
async function go(view, extra) {
  S.view = view; S.flash = (extra && extra.flash) || ''; S.sel = 0;
  if (['posts', 'pages', 'look', 'perf'].includes(view)) localStorage.setItem('view', view);
  render(true);
  try {
    if (view === 'posts') { await loadPosts(); await loadBuilds(); }
    if (view === 'pages' || view === 'look') await loadPages();
    if (view === 'perf') { await loadBuilds(); S.metrics = null; render(); S.metrics = await api('GET', `/blogs/${S.blog.id}/metrics`).catch((e) => ({ error: e.message })); }
  } catch (e) { if (e.message !== '401') S.flash = e.message; }
  render();
}
async function loadPosts() { const r = await api('GET', `/blogs/${S.blog.id}/posts?limit=100`); S.posts = r.items; S.cats = await api('GET', `/blogs/${S.blog.id}/categories`); }
async function loadBuilds() { S.builds = await api('GET', `/blogs/${S.blog.id}/builds?limit=6`).catch(() => []); }
async function loadPages() {
  const all = await api('GET', `/blogs/${S.blog.id}/pages`);
  S.themePage = all.find((p) => p.slug === THEME_SLUG) || null;
  S.pages = all.filter((p) => p.slug !== THEME_SLUG);
  try { S.theme = { ...DEFAULT_THEME, ...JSON.parse((S.themePage && S.themePage.content) || '{}') }; } catch (e) { S.theme = { ...DEFAULT_THEME }; }
}

/* ---------- publicar sitio ---------- */
async function buildSite() {
  if (S.building) return; S.building = true; render();
  try {
    await api('POST', '/build', { blogId: S.blog.id });
    toast('¡Listo! Tu sitio se está actualizando (tarda unos segundos).', S.siteUrl ? { label: 'Ver sitio', fn: () => window.open(S.siteUrl, '_blank') } : null, 9000);
    S.dirty = false; localStorage.removeItem('dirty'); await loadBuilds();
  } catch (e) { toast('No se pudo construir el sitio: ' + e.message); }
  S.building = false; render();
}

/* ---------- markdown mínimo para la vista previa ---------- */
function md(src) {
  const inline = (t) => esc(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  const out = []; let list = false;
  for (const raw of String(src || '').split('\n')) {
    const l = raw.trimEnd(); const li = /^\s*[-*]\s+(.*)/.exec(l);
    if (li) { if (!list) { out.push('<ul>'); list = true; } out.push('<li>' + inline(li[1]) + '</li>'); continue; }
    if (list) { out.push('</ul>'); list = false; }
    if (/^###\s/.test(l)) out.push('<h3>' + inline(l.slice(4)) + '</h3>');
    else if (/^##\s/.test(l)) out.push('<h2>' + inline(l.slice(3)) + '</h2>');
    else if (/^#\s/.test(l)) out.push('<h1>' + inline(l.slice(2)) + '</h1>');
    else if (/^>\s?/.test(l)) out.push('<blockquote>' + inline(l.replace(/^>\s?/, '')) + '</blockquote>');
    else if (l.trim()) out.push('<p>' + inline(l) + '</p>');
  }
  if (list) out.push('</ul>');
  return out.join('') || '<p style="color:var(--mute)">La vista previa aparece aquí mientras escribes…</p>';
}

/* ---------- vistas ---------- */
function shell(inner) {
  const menu = MENU.map(([k, name, items]) => `<div class="dd"><button class="ddb" data-act="menu" data-k="${k}" aria-haspopup="true" aria-expanded="${S.menu === k}" ${groupOf(S.view) === k ? 'aria-current="page"' : ''}>${name} <span aria-hidden="true">▾</span></button>
    ${S.menu === k ? `<div class="ddm" role="menu">${items.map(([v, n, h]) => `<button role="menuitem" data-act="go" data-v="${v}">${n}<kbd>${h}</kbd></button>`).join('')}</div>` : ''}</div>`).join('');
  return `<div class="bar"><span>Sesión: ${esc(S.user && S.user.email)}</span><span><a href="/docs" target="_blank" rel="noopener">API</a>${S.siteUrl ? `<a href="${esc(S.siteUrl)}" target="_blank" rel="noopener">Ver sitio</a>` : ''}<button data-act="help">Atajos ?</button><button data-act="logout">Cerrar sesión</button></span></div>
  <div class="shell"><header class="head"><div class="brand">${LOGO}<div>${esc(S.blog ? S.blog.name : 'Sigo intentándolo')}<small>panel</small></div></div>
  <nav class="tabs" aria-label="Menú">${menu}</nav>
  <div class="pub">${S.dirty && !S.building ? '<span class="dirty">● Hay cambios sin publicar</span>' : ''}<button class="btn fill" data-act="build" ${S.building ? 'disabled' : ''}>${S.building ? '<span class="spin"></span> Construyendo…' : '✦ Publicar sitio'}</button></div></header>
  <main id="main" tabindex="-1">${S.flash ? `<div class="flash" role="alert">${esc(S.flash)}</div>` : ''}${inner}</main></div>`;
}

function vLogin() {
  return `<div class="login"><div class="brand">${LOGO}Sigo intentándolo</div><div class="card"><h2>Entrar al panel</h2><p class="sub">Aquí escribes y publicas tu blog.</p>${S.flash ? `<div class="flash">${esc(S.flash)}</div>` : ''}
  <form data-form="login"><label for="em">Correo</label><input id="em" type="email" autocomplete="username" required autofocus><label for="pw">Contraseña</label><input id="pw" type="password" autocomplete="current-password" required>
  <p style="margin:18px 0 0"><button class="btn fill" type="submit">Entrar</button></p></form></div></div>`;
}
function vOnboarding() {
  return `<div class="login"><div class="brand">${LOGO}Bienvenida</div><div class="card"><h2>Crea tu blog</h2><p class="sub">Sólo necesitas un nombre. Lo puedes cambiar después.</p>
  <form data-form="blog"><label for="bn">Nombre del blog</label><input id="bn" type="text" value="Sigo intentándolo" required autofocus><label for="bd">Descripción <small>opcional</small></label><input id="bd" type="text" placeholder="Una guía honesta de alguien que sigue intentándolo.">
  <p style="margin:18px 0 0"><button class="btn fill" type="submit">Crear blog</button></p></form></div></div>`;
}

function vPosts() {
  const q = S.q.toLowerCase(), list = S.posts.filter((p) => !q || p.title.toLowerCase().includes(q));
  const pub = S.posts.filter((p) => p.status === 'published').length;
  const rows = list.map((p, i) => `<tr tabindex="0" data-i="${i}" data-id="${p.id}" class="${i === S.sel ? 'sel' : ''}"><td><div class="t">${esc(p.title)}</div></td>
    <td><span class="pill ${p.status === 'published' ? 'p' : 'd'}">${p.status === 'published' ? 'Publicada' : 'Borrador'}</span></td><td>${fmtDate(p.updatedAt)}</td>
    <td class="act"><button class="btn ghost sm" data-act="edit" data-id="${p.id}">Editar</button> <button class="btn ghost sm" data-act="del" data-id="${p.id}">Borrar</button></td></tr>`).join('');
  return `<div class="page-h"><div><div class="crumb">Documentos</div><h1>Entradas</h1></div><button class="btn rose" data-act="new">+ Nueva entrada <kbd>n</kbd></button></div>
  <p class="sub">${S.posts.length} en total · ${pub} publicadas. Guardar no publica el sitio: cuando termines, pulsa <b>Publicar sitio</b>.</p>
  ${S.posts.length > 6 ? `<div style="margin-bottom:12px"><input type="text" id="q" placeholder="Buscar…  ( / )" value="${esc(S.q)}" aria-label="Buscar entrada"></div>` : ''}
  <div class="card" style="padding:0">${list.length ? `<table><thead><tr><th>Título</th><th>Estado</th><th>Actualizada</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
    : `<div class="empty"><h2>${S.posts.length ? 'Nada coincide' : 'Aún no hay entradas'}</h2><p>${S.posts.length ? 'Prueba con otra palabra.' : 'Escribe la primera: es más fácil de lo que parece.'}</p>${S.posts.length ? '' : '<button class="btn fill" data-act="new">Escribir mi primera entrada</button>'}</div>`}</div>`;
}

function vEdit() {
  const e = S.edit, isPost = e.mode === 'post';
  const catOpts = '<option value="">Sin categoría</option>' + S.cats.map((c) => `<option value="${c.id}" ${e.categoryId === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('');
  return `<p style="margin:22px 0 0"><button class="btn ghost sm" data-act="cancel">← Volver <kbd>Esc</kbd></button></p>
  <div class="page-h"><h1>${e.id ? 'Editar' : 'Nueva'} ${isPost ? 'entrada' : 'página'}</h1></div>
  <div id="recover"></div>
  <div class="split"><form data-form="edit"><label for="f-title">Título</label><input id="f-title" type="text" data-f="title" value="${esc(e.title)}" required maxlength="200" autofocus>
    <label for="f-content">Contenido <small>## Subtítulo · **negritas** · - lista · &gt; cita</small></label><p class="toolrow"><button class="btn ghost sm" type="button" data-act="pickimg">🖼 Insertar imagen</button><input type="file" id="imgfile" accept="image/*" hidden><small id="imgmsg"></small></p><textarea id="f-content" data-f="content">${esc(e.content)}</textarea>
    ${isPost ? `<label for="f-cat">¿Dónde aparece? <small>elige una sección de la portada o déjalo en «Sin categoría» para el blog</small></label><div style="display:flex;gap:8px;flex-wrap:wrap"><select id="f-cat" data-f="categoryId">${catOpts}</select>${missingSections().length ? '<button class="btn ghost sm" type="button" data-act="addsections">＋ Crear secciones de la portada</button>' : ''}</div>` : '<p class="sub">Para tu foto y texto de «Sobre mí»: crea una página con dirección <b>sobre-mi</b> y pon la imagen arriba.</p>'}
    <label class="chk" style="margin-top:16px"><input type="checkbox" data-f="status" ${e.status === 'published' ? 'checked' : ''}> Publicar en el blog <small>(si no, queda como borrador)</small></label>
    <details style="margin-top:14px"><summary>Más opciones</summary>
      ${isPost ? `<label for="f-excerpt">Resumen <small>aparece en las tarjetas</small></label><input id="f-excerpt" type="text" data-f="excerpt" value="${esc(e.excerpt)}">
      <label for="newcat">Otra categoría</label><div style="display:flex;gap:8px"><input type="text" id="newcat" placeholder="Nueva…" style="max-width:150px" aria-label="Nueva categoría"><button class="btn ghost sm" type="button" data-act="addcat">Crear</button></div>` :
      `<label for="f-type">Tipo</label><select id="f-type" data-f="type"><option value="page" ${e.type === 'page' ? 'selected' : ''}>Página</option><option value="landing" ${e.type === 'landing' ? 'selected' : ''}>Texto de la portada</option></select>`}
      <label for="f-slug">Dirección (slug)</label><input id="f-slug" type="text" data-f="slug" value="${esc(e.slug)}" placeholder="se genera del título"></details>
    <p style="margin-top:20px;display:flex;gap:10px;flex-wrap:wrap"><button class="btn fill" type="submit">Guardar <kbd>Ctrl S</kbd></button><button class="btn" type="button" data-act="savebuild">Guardar y publicar sitio <kbd>Ctrl ↵</kbd></button></p></form>
  <div class="card preview" aria-live="polite"><div class="crumb">Vista previa</div><h1 id="pv-t">${esc(e.title)}</h1><div id="pv">${md(e.content)}</div></div></div>`;
}

function vPages() {
  const rows = S.pages.map((p) => `<tr tabindex="0"><td><div class="t">${esc(p.title)}</div><div class="s">${p.type === 'landing' ? 'Portada' : 'Página'} · /${esc(p.slug)}</div></td><td><span class="pill ${p.status === 'published' ? 'p' : 'd'}">${p.status === 'published' ? 'Publicada' : 'Borrador'}</span></td><td>${fmtDate(p.updatedAt)}</td>
    <td class="act"><button class="btn ghost sm" data-act="editpage" data-id="${p.id}">Editar</button> <button class="btn ghost sm" data-act="delpage" data-id="${p.id}">Borrar</button></td></tr>`).join('');
  return `<div class="page-h"><div><div class="crumb">CMS</div><h1>Páginas</h1></div><button class="btn rose" data-act="newpage">+ Nueva página</button></div>
  <p class="hint"><span>💡</span><span>La <b>portada</b> es el texto de bienvenida del inicio. Las demás páginas (Sobre mí, Proyectos…) aparecen en el menú inferior del sitio.</span></p>
  <div class="card" style="padding:0">${S.pages.length ? `<table><thead><tr><th>Título</th><th>Estado</th><th>Actualizada</th><th></th></tr></thead><tbody>${rows}</tbody></table>` : '<div class="empty"><h2>Aún no hay páginas</h2><p>Crea una portada para que el inicio tenga tu voz.</p></div>'}</div>`;
}

function vLook() {
  const t = S.theme;
  const thumb = (c) => `<span class="thumb" style="background:radial-gradient(circle at 78% 24%,${c[4]} 0 7%,transparent 8%),linear-gradient(${c[0]},${c[1]} 55%,${c[2]} 70%,${c[3]} 71%)"></span>`;
  const scenes = Object.entries(SCENES).map(([k, v]) => `<label><input type="radio" name="scene" value="${k}" data-t="scene" ${t.scene === k ? 'checked' : ''}><span class="opt">${thumb(v.c)}<b>${v.name}</b><small>${v.note}</small></span></label>`).join('');
  const lay = (k, n, svg) => `<label><input type="radio" name="blog" value="${k}" data-t="blog" ${t.blog === k ? 'checked' : ''}><span class="opt">${svg}<b>${n}</b></span></label>`;
  const cards = '<svg viewBox="0 0 120 56"><rect x="4" y="6" width="34" height="44" rx="6" fill="currentColor" opacity=".7"/><rect x="43" y="6" width="34" height="44" rx="6" fill="currentColor" opacity=".5"/><rect x="82" y="6" width="34" height="44" rx="6" fill="currentColor" opacity=".35"/></svg>';
  const list = '<svg viewBox="0 0 120 56"><rect x="4" y="5" width="112" height="13" rx="6" fill="currentColor" opacity=".7"/><rect x="4" y="22" width="112" height="13" rx="6" fill="currentColor" opacity=".5"/><rect x="4" y="39" width="112" height="13" rx="6" fill="currentColor" opacity=".35"/></svg>';
  const acc = t.accent || SCENES[t.scene].c[5];
  return `<div class="page-h"><div><div class="crumb">Plantillas</div><h1>Diseño del sitio</h1></div><button class="btn fill" data-act="savethemebuild">Guardar y publicar sitio</button></div>
  <p class="sub">Elige una plantilla y listo: el CMS genera el CSS de tu portada y de tu blog. No tienes que escribir nada de código.</p>
  <div class="card"><h3>Plantilla del sitio</h3><div class="tpl three" style="margin-top:10px">${scenes}</div></div>
  <div class="split" style="margin-top:16px"><div class="card"><h3>Listado del blog</h3><div class="tpl" style="margin-top:10px">${lay('tarjetas', 'Tarjetas', cards)}${lay('lista', 'Lista', list)}</div></div>
  <div class="card"><h3>Letra y color</h3><label for="ft">Letra de los títulos</label><select id="ft" data-t="font">${Object.entries(FONT_NAMES).map(([k, n]) => `<option value="${k}" ${t.font === k ? 'selected' : ''}>${n}</option>`).join('')}</select>
  <label for="ac">Color de acento <small>botones y detalles</small></label><div style="display:flex;gap:10px;align-items:center"><input id="ac" type="color" data-t="accent" value="${acc}" style="width:54px;height:40px;padding:0;border:0;background:none"><button class="btn ghost sm" data-act="resetaccent">Usar el de la plantilla</button></div></div></div>
  <details class="card" style="margin-top:16px"><summary>¿Cómo se mete el CSS? (para entenderlo)</summary><ol style="line-height:1.8"><li>Tú eliges plantilla, letra y color aquí.</li><li>Al pulsar <b>Publicar sitio</b>, el CMS convierte tus elecciones en un bloque de CSS (variables de color y letra) y lo manda al generador junto con tus entradas.</li><li>El generador ya trae el diseño del sitio (portada, blog, paisaje). Sólo le pone tus colores y escribe los archivos <code>style.css</code> y las páginas HTML.</li></ol>
  <p><button class="btn ghost sm" data-act="showcss">Ver el CSS que genera el CMS</button></p><div id="cssbox"></div></details>`;
}

const mins = (s) => (s >= 60 ? Math.floor(s / 60) + ' min ' + (s % 60) + ' s' : s + ' s');
function vPerf() {
  const m = S.metrics;
  let body;
  if (!m) body = '<div class="card empty"><span class="spin"></span><p>Consultando el servicio de métricas…</p></div>';
  else if (m.error) body = `<div class="flash">No se pudieron consultar las métricas (${esc(m.error)}). Revisa que el servicio de métricas esté despierto y vuelve a intentar.</div>`;
  else {
    const days = (m.porDia || []).slice(-14), max = Math.max(1, ...days.map((d) => d.views));
    const pages = (m.paginas || []).slice(0, 6), pmax = Math.max(1, ...pages.map((p) => p.views));
    const dev = m.dispositivos || {};
    body = `<div class="stats"><div class="card stat"><div class="n">${m.visitas}</div><div class="l">Visitas a páginas</div></div><div class="card stat"><div class="n">${m.visitantesUnicos}</div><div class="l">Visitantes únicos</div></div>
    <div class="card stat"><div class="n">${m.sesiones}</div><div class="l">Sesiones</div></div><div class="card stat"><div class="n">${mins(m.tiempoMedioSeg || 0)}</div><div class="l">Tiempo medio en página</div></div><div class="card stat"><div class="n">${((m.reboteBp || 0) / 100).toFixed(0)}%</div><div class="l">Rebote (se fueron sin explorar)</div></div></div>
    <div class="split"><div class="card"><h3>Vistas por día</h3><div class="chart" role="img" aria-label="Vistas por día">${days.map((d) => `<i style="height:${Math.max(3, d.views / max * 100)}%" data-t="${esc(d.day)}: ${d.views}"></i>`).join('')}</div><div class="axis"><span>${days[0] ? esc(days[0].day) : ''}</span><span>${days.length ? esc(days[days.length - 1].day) : ''}</span></div></div>
    <div class="card"><h3>Páginas más vistas</h3><div class="bars" style="margin-top:10px">${pages.length ? pages.map((p) => `<div><span>${esc(p.path)}</span><b style="width:${p.views / pmax * 100}%"></b><span>${p.views}</span></div>`).join('') : '<span style="color:var(--mute)">Aún no hay visitas.</span>'}</div>
    <p class="help" style="margin-top:14px">Escritorio ${dev.desktop || 0} · Móvil ${dev.mobile || 0} · Tablet ${dev.tablet || 0}</p></div></div>
    ${m.simulated ? '<p class="help">Los datos son simulados porque el CMS no tiene configurada la dirección de métricas.</p>' : ''}`;
  }
  const bl = S.builds.map((b) => `<tr><td>#${b.id}</td><td><span class="pill ${b.status === 'success' ? 'p' : 'd'}">${b.status === 'success' ? 'Correcto' : b.status === 'failed' ? 'Falló' : 'En curso'}</span></td><td>${fmtDate(b.createdAt)}</td><td>${esc(b.message || (b.result && b.result.status) || '')}</td></tr>`).join('');
  return `<div class="page-h"><div><div class="crumb">CMS</div><h1>Rendimiento</h1></div>${S.siteUrl ? `<a class="btn" href="${esc(S.siteUrl)}" target="_blank" rel="noopener">Abrir mi sitio ↗</a>` : ''}</div>
  <p class="hint"><span>📈</span><span>Estas cifras las cuenta el servicio de <b>métricas</b> cuando alguien visita tu sitio. Si el sitio es nuevo, empiezan en cero.</span></p>${body}
  <div class="card" style="padding:0;margin-top:18px"><div style="padding:14px 18px 0"><h3>Últimas publicaciones del sitio</h3></div>${S.builds.length ? `<table><thead><tr><th>Build</th><th>Estado</th><th>Fecha</th><th>Detalle</th></tr></thead><tbody>${bl}</tbody></table>` : '<div class="empty">Aún no has publicado el sitio.</div>'}</div>`;
}

function render(keepScroll) {
  const app = $('#app');
  let html;
  if (S.view === 'login') html = vLogin();
  else if (S.view === 'onboarding') html = vOnboarding();
  else if (!S.blog) html = vLogin();
  else html = shell({ posts: vPosts, 'edit-post': vEdit, 'edit-page': vEdit, pages: vPages, look: vLook, perf: vPerf }[S.view]());
  app.innerHTML = html + modalHtml();
  if (!keepScroll) { /* mantiene la posición al volver a dibujar */ }
  if (S.view === 'edit-post' || S.view === 'edit-page') checkRecover();
  const first = $('[autofocus]'); if (first) first.focus();
  if (S.modal) { const i = $('#pi'); if (i) { i.focus(); } }
}

/* ---------- ventanas: atajos y buscador de acciones ---------- */
const ACTIONS = [
  ['Nueva entrada', 'n', () => newPost()], ['Ir a Entradas', 'g e', () => go('posts')], ['Ir a Páginas', 'g p', () => go('pages')],
  ['Ir a Apariencia', 'g a', () => go('look')], ['Ir a Rendimiento', 'g r', () => go('perf')], ['Publicar sitio', 'Ctrl ↵', () => buildSite()],
  ['Ver atajos', '?', () => { S.modal = 'help'; render(); }], ['Cerrar sesión', '', () => logout()],
];
let palFilter = '', palIdx = 0;
function modalHtml() {
  if (!S.modal) return '';
  if (S.modal === 'help') return `<div class="modal" data-act="closemodal"><div class="box" role="dialog" aria-label="Atajos de teclado"><h2>Atajos de teclado</h2><p class="sub">Puedes hacer todo sin el mouse.</p><div class="keys">
  <span><kbd>Ctrl</kbd> <kbd>K</kbd></span><span>Buscar cualquier acción</span><span><kbd>g</kbd> luego <kbd>e</kbd> <kbd>p</kbd> <kbd>a</kbd> <kbd>r</kbd></span><span>Ir a Entradas, Páginas, Apariencia o Rendimiento</span><span><kbd>n</kbd></span><span>Nueva entrada</span>
  <span><kbd>j</kbd> / <kbd>k</kbd></span><span>Moverte por la lista</span><span><kbd>Enter</kbd> o <kbd>e</kbd></span><span>Editar la entrada marcada</span><span><kbd>d</kbd></span><span>Borrar (con opción de deshacer)</span>
  <span><kbd>/</kbd></span><span>Buscar entradas</span><span><kbd>Ctrl</kbd> <kbd>S</kbd></span><span>Guardar</span><span><kbd>Ctrl</kbd> <kbd>Enter</kbd></span><span>Guardar y publicar el sitio</span><span><kbd>Esc</kbd></span><span>Cerrar o volver</span></div>
  <p style="margin-top:16px"><button class="btn" data-act="closemodal">Entendido</button></p></div></div>`;
  const items = ACTIONS.filter((a) => a[0].toLowerCase().includes(palFilter.toLowerCase()));
  palIdx = Math.min(palIdx, Math.max(0, items.length - 1));
  return `<div class="modal" data-act="closemodal"><div class="box pal" role="dialog" aria-label="Buscar acción"><input id="pi" type="text" placeholder="¿Qué quieres hacer?" value="${esc(palFilter)}" autocomplete="off">${items.map((a, i) => `<button data-act="runpal" data-n="${esc(a[0])}" class="${i === palIdx ? 'on' : ''}"><span>${a[0]}</span><kbd>${a[1] || '—'}</kbd></button>`).join('') || '<p class="sub">Sin resultados</p>'}</div></div>`;
}

/* ---------- edición ---------- */
const draftKey = () => `draft:${S.blog.id}:${S.edit.mode}:${S.edit.id || 'nuevo'}`;
function newPost() { S.edit = { mode: 'post', id: null, title: '', excerpt: '', content: '', categoryId: null, status: 'draft', slug: '' }; S.view = 'edit-post'; S.flash = ''; render(); }
async function editPost(id) {
  try { const p = await api('GET', `/blogs/${S.blog.id}/posts/${id}`); S.edit = { mode: 'post', id: p.id, title: p.title, excerpt: p.excerpt || '', content: p.content || '', categoryId: p.categoryId, status: p.status, slug: p.slug }; S.view = 'edit-post'; S.flash = ''; render(); } catch (e) { toast(e.message); }
}
function editPage(p) { S.edit = { mode: 'page', id: p ? p.id : null, title: p ? p.title : '', content: p ? p.content : '', type: p ? p.type : 'page', status: p ? p.status : 'draft', slug: p ? p.slug : '' }; S.view = 'edit-page'; S.flash = ''; render(); }
function checkRecover() {
  let d = null; try { d = JSON.parse(localStorage.getItem(draftKey()) || 'null'); } catch (e) { /* ignorado */ }
  const box = $('#recover'); if (!d || !box || (d.title === S.edit.title && d.content === S.edit.content)) return;
  box.innerHTML = `<div class="flash">Encontré cambios sin guardar de ${esc(new Date(d.at).toLocaleString('es-MX'))}. <button class="btn sm" data-act="recover">Recuperar</button> <button class="btn ghost sm" data-act="dropdraft">Descartar</button></div>`;
}
async function saveEdit(then) {
  const e = S.edit; if (!e.title.trim()) { toast('Escribe un título primero.'); return; }
  const base = e.mode === 'post' ? `/blogs/${S.blog.id}/posts` : `/blogs/${S.blog.id}/pages`;
  const body = e.mode === 'post' ? { title: e.title, excerpt: e.excerpt || null, content: e.content, categoryId: e.categoryId, status: e.status } : { title: e.title, content: e.content, type: e.type, status: e.status };
  if (e.slug) body.slug = e.slug;
  try {
    await api(e.id ? 'PUT' : 'POST', e.id ? `${base}/${e.id}` : base, body);
    clearTimeout(S.dt); localStorage.removeItem(draftKey()); markDirty();
    toast(e.status === 'published' ? 'Guardado y marcado como publicado.' : 'Guardado como borrador.');
    await go(e.mode === 'post' ? 'posts' : 'pages', { flash: '' });
    if (then) buildSite();
  } catch (err) { toast('No se pudo guardar: ' + err.message); }
}
function deletePost(id) {
  const i = S.posts.findIndex((p) => p.id === id); if (i < 0) return; const [gone] = S.posts.splice(i, 1); render();
  let undone = false; markDirty();
  toast('Entrada eliminada.', { label: 'Deshacer', fn: () => { undone = true; S.posts.splice(i, 0, gone); render(); } }, 6000);
  setTimeout(async () => { if (!undone) { try { await api('DELETE', `/blogs/${S.blog.id}/posts/${id}`); } catch (e) { toast('No se pudo borrar: ' + e.message); loadPosts().then(render); } } }, 6200);
}
async function saveTheme(then) {
  const body = { title: 'Tema visual', slug: THEME_SLUG, type: 'page', status: 'draft', content: JSON.stringify(S.theme) };
  try {
    const saved = S.themePage ? await api('PUT', `/blogs/${S.blog.id}/pages/${S.themePage.id}`, body) : await api('POST', `/blogs/${S.blog.id}/pages`, body);
    S.themePage = saved; markDirty(); toast('Tema guardado.'); if (then) buildSite();
  } catch (e) { toast('No se pudo guardar el tema: ' + e.message); }
}

/* ---------- eventos ---------- */
const H = {
  go: (d) => { S.menu = ''; go(d.v); }, logout: () => logout(), help: () => { S.modal = 'help'; render(); }, palette: () => { palFilter = ''; palIdx = 0; S.modal = 'pal'; render(); },
  closemodal: (d, ev) => { if (ev.target === ev.currentTarget) { S.modal = null; render(); } }, build: () => buildSite(), new: () => newPost(),
  edit: (d) => editPost(Number(d.id)), del: (d) => deletePost(Number(d.id)), cancel: () => { clearTimeout(S.dt); go(S.edit && S.edit.mode === 'page' ? 'pages' : 'posts'); },
  toggle: async (d) => { const p = S.posts.find((x) => x.id === Number(d.id)); const st = p.status === 'published' ? 'draft' : 'published'; try { await api('PATCH', `/blogs/${S.blog.id}/posts/${p.id}/status`, { status: st }); p.status = st; markDirty(); toast(st === 'published' ? 'Marcada como publicada. Pulsa «Publicar sitio» para verla en línea.' : 'Vuelta a borrador.'); await loadBuilds(); render(); } catch (e) { toast(e.message); } },
  savebuild: () => saveEdit(true), newpage: () => editPage(null), editpage: (d) => editPage(S.pages.find((p) => p.id === Number(d.id))),
  delpage: async (d) => { if (!confirm('¿Borrar esta página? Puedes volver a crearla, pero perderás su texto.')) return; try { await api('DELETE', `/blogs/${S.blog.id}/pages/${d.id}`); markDirty(); await go('pages'); toast('Página borrada.'); } catch (e) { toast(e.message); } },
  recover: () => { const d = JSON.parse(localStorage.getItem(draftKey())); Object.assign(S.edit, d.data); render(); toast('Cambios recuperados.'); }, dropdraft: () => { localStorage.removeItem(draftKey()); $('#recover').innerHTML = ''; },
  pickimg: () => $('#imgfile').click(),
  addsections: async () => { try { for (const n of missingSections()) S.cats.push(await api('POST', `/blogs/${S.blog.id}/categories`, { name: n })); render(); toast('Listo: ya puedes elegir Dibujos, Proyectos, Pensamientos o Innovación textil.'); } catch (e) { toast(e.message); } },
  addcat: async () => { const n = $('#newcat').value.trim(); if (!n) return; try { const c = await api('POST', `/blogs/${S.blog.id}/categories`, { name: n }); S.cats.push(c); S.edit.categoryId = c.id; render(); toast('Categoría creada.'); } catch (e) { toast(e.message); } },
  runpal: (d) => { const a = ACTIONS.find((x) => x[0] === d.n); S.modal = null; render(); if (a) a[2](); },
  resetaccent: () => { S.theme.accent = null; render(); },
  menu: (d) => { S.menu = S.menu === d.k ? '' : d.k; render(); setTimeout(() => { const f = $('.ddm button'); if (f) f.focus(); }, 0); },
  savetheme: () => saveTheme(false), savethemebuild: () => saveTheme(true),
  showcss: async () => { try { const r = await api('POST', '/theme/css', S.theme); $('#cssbox').innerHTML = `<div style="margin-top:10px"><p class="sub">Esto se envía al generador. Sólo contiene variables validadas.</p><pre class="css">${esc(r.css.replace(/;/g, ';\n  ').replace('{', '{\n  '))}</pre></div>`; } catch (e) { toast(e.message); } },
};
document.addEventListener('click', (ev) => { const a = ev.target.closest('[data-act]'); if (a && H[a.dataset.act]) { if (a.tagName === 'A') return; H[a.dataset.act](a.dataset, { target: ev.target, currentTarget: a }); } });
document.addEventListener('click', (ev) => { if (S.menu && !ev.target.closest('.dd')) { S.menu = ''; render(); } });
document.addEventListener('dblclick', (ev) => { const r = ev.target.closest('tr[data-id]'); if (r) editPost(Number(r.dataset.id)); });
document.addEventListener('submit', async (ev) => {
  const f = ev.target.dataset.form; if (!f) return; ev.preventDefault();
  if (f === 'login') {
    try { const r = await api('POST', '/auth/login', { email: $('#em').value, password: $('#pw').value }); S.token = r.accessToken; localStorage.setItem('tk', S.token); S.flash = ''; await boot(); } catch (e) { S.flash = e.message === 'Error 401' ? 'Correo o contraseña incorrectos.' : e.message; render(); }
  } else if (f === 'blog') {
    try { S.blog = await api('POST', '/blogs', { name: $('#bn').value, description: $('#bd').value || null }); localStorage.setItem('blog', S.blog.id); S.blogs = [S.blog]; await go('posts'); toast('¡Tu blog existe! Escribe tu primera entrada.'); } catch (e) { toast(e.message); }
  } else if (f === 'edit') saveEdit(false);
});
document.addEventListener('input', (ev) => {
  const t = ev.target;
  if (t.id === 'q') { S.q = t.value; const pos = t.selectionStart; render(); const q = $('#q'); q.focus(); q.setSelectionRange(pos, pos); return; }
  if (t.id === 'pi') { palFilter = t.value; palIdx = 0; const pos = t.selectionStart; render(); const i = $('#pi'); i.focus(); i.setSelectionRange(pos, pos); return; }
  if (t.dataset.f && S.edit) {
    const k = t.dataset.f; S.edit[k] = k === 'status' ? (t.checked ? 'published' : 'draft') : k === 'categoryId' ? (t.value ? Number(t.value) : null) : t.value;
    if (k === 'title') $('#pv-t').textContent = t.value; if (k === 'content') $('#pv').innerHTML = md(t.value);
    clearTimeout(S.dt); S.dt = setTimeout(() => localStorage.setItem(draftKey(), JSON.stringify({ at: Date.now(), data: { title: S.edit.title, excerpt: S.edit.excerpt, content: S.edit.content, categoryId: S.edit.categoryId, status: S.edit.status, slug: S.edit.slug } })), 600);
  }
});
document.addEventListener('change', async (ev) => {
  const t = ev.target;
  if (t.id === 'imgfile' && t.files[0] && S.edit) {
    const msg = $('#imgmsg'); msg.textContent = ' Subiendo…';
    try {
      const blob = await shrink(t.files[0]), fd = new FormData(); fd.append('file', blob, (t.files[0].name || 'imagen').replace(/\.[^.]+$/, '') + '.jpg');
      const m = await api('POST', `/blogs/${S.blog.id}/media`, undefined, fd);
      const ta = $('#f-content'), pos = ta.selectionStart || ta.value.length, md1 = `![${(t.files[0].name || '').replace(/\.[^.]+$/, '')}](${m.url})`;
      ta.value = ta.value.slice(0, pos) + (pos && ta.value[pos - 1] !== '\n' ? '\n\n' : '') + md1 + '\n\n' + ta.value.slice(pos);
      ta.dispatchEvent(new Event('input', { bubbles: true })); msg.textContent = ' ✓ Imagen puesta en el texto';
    } catch (e) { msg.textContent = ' ' + e.message; }
    t.value = ''; return;
  }
  if (!t.dataset.t) return;
  S.theme[t.dataset.t] = t.type === 'checkbox' ? t.checked : t.value; render();
});
document.addEventListener('keydown', (ev) => {
  const tag = (document.activeElement.tagName || ''), typing = /INPUT|TEXTAREA|SELECT/.test(tag), editing = S.view === 'edit-post' || S.view === 'edit-page';
  if (S.modal) {
    if (ev.key === 'Escape') { S.modal = null; render(); }
    else if (S.modal === 'pal') {
      const n = ACTIONS.filter((a) => a[0].toLowerCase().includes(palFilter.toLowerCase())).length;
      if (ev.key === 'ArrowDown') { ev.preventDefault(); palIdx = (palIdx + 1) % Math.max(1, n); render(); } else if (ev.key === 'ArrowUp') { ev.preventDefault(); palIdx = (palIdx - 1 + n) % Math.max(1, n); render(); }
      else if (ev.key === 'Enter') { ev.preventDefault(); const a = ACTIONS.filter((x) => x[0].toLowerCase().includes(palFilter.toLowerCase()))[palIdx]; S.modal = null; render(); if (a) a[2](); }
    }
    return;
  }
  if (!S.token) return;
  if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'k') { ev.preventDefault(); H.palette(); return; }
  if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 's' && editing) { ev.preventDefault(); saveEdit(false); return; }
  if ((ev.ctrlKey || ev.metaKey) && ev.key === 'Enter') { ev.preventDefault(); if (editing) saveEdit(true); else buildSite(); return; }
  if (ev.key === 'Escape' && S.menu) { S.menu = ''; render(); return; }
  if (S.menu && (ev.key === 'ArrowDown' || ev.key === 'ArrowUp')) { ev.preventDefault(); const b = [...document.querySelectorAll('.ddm button')]; const i = b.indexOf(document.activeElement); (b[(i + (ev.key === 'ArrowDown' ? 1 : -1) + b.length) % b.length] || b[0]).focus(); return; }
  if (ev.key === 'Escape') { if (editing) clearTimeout(S.dt); if (editing) go(S.edit.mode === 'page' ? 'pages' : 'posts'); else if (typing) document.activeElement.blur(); return; }
  if (typing || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (S.pendingG) { S.pendingG = false; const m = { e: 'posts', p: 'pages', a: 'look', r: 'perf' }[ev.key]; if (m) { ev.preventDefault(); go(m); } return; }
  if (ev.key === 'g') { S.pendingG = true; setTimeout(() => { S.pendingG = false; }, 1200); return; }
  if (ev.key === '?') { H.help(); return; }
  if (S.view === 'posts') {
    const rows = [...document.querySelectorAll('tr[data-id]')]; const cur = () => rows[S.sel];
    const mark = () => { rows.forEach((r, i) => r.classList.toggle('sel', i === S.sel)); if (cur()) { cur().focus(); } };
    if (ev.key === 'n') { ev.preventDefault(); newPost(); } else if (ev.key === '/') { ev.preventDefault(); const q = $('#q'); if (q) q.focus(); }
    else if (ev.key === 'j') { S.sel = Math.min(rows.length - 1, S.sel + 1); mark(); } else if (ev.key === 'k') { S.sel = Math.max(0, S.sel - 1); mark(); }
    else if ((ev.key === 'Enter' || ev.key === 'e') && cur()) { ev.preventDefault(); editPost(Number(cur().dataset.id)); }
    else if (ev.key === 'd' && cur()) deletePost(Number(cur().dataset.id));
  }
});
boot();
