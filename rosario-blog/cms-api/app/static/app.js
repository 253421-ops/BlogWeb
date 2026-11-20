/* Interfaz del CMS «Sigo intentándolo». JavaScript sin dependencias; habla con la API en /api (mismo origen). */
'use strict';
const API = '/api';
const LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M21 3a13 13 0 1 0 8 22A11 11 0 0 1 21 3z" fill="#f5c451"/></svg>';
const THEME_SLUG = 'tema-visual';
const DEFAULT_THEME = { mode: 'dark', scene: 'noche', accent: null, fontHead: 'script-accent', fontBody: 'clean-sans', fontMono: 'jetbrains', fontScale: 'editorial', blog: 'tarjetas' };
const SCENES = {
  noche: { mode: 'dark', name: 'Noche estrellada', note: 'Cielo azul con luna, montañas, un pueblo y un campo de flores.', c: ['#050a24', '#10265e', '#4d86a8', '#1d3b22', '#f8e7a0', '#f5c451'] },
  atardecer: { mode: 'dark', name: 'Atardecer', note: 'El mismo paisaje con cielo morado y naranja.', c: ['#1b1140', '#7a3a86', '#ff9a5c', '#34402a', '#fff0c4', '#ffb36b'] },
  amanecer: { mode: 'dark', name: 'Amanecer', note: 'Cielo rosado y verdes suaves.', c: ['#1a2a5a', '#c46a9a', '#ffc9a3', '#3f6b4a', '#fff7e0', '#ff8fa3'] },
  papel: { mode: 'light', name: 'Papel editorial', note: 'Crema cálido, como una revista impresa.', c: ['#e9e2d0', '#f3d9b8', '#fbe9d2', '#a9c18f', '#fff6dc', '#8f5a00'] },
  pastel: { mode: 'light', name: 'Lienzo pastel', note: 'Rosas y lilas suaves sobre fondo claro.', c: ['#f3dcec', '#e3d4f7', '#fde1d3', '#b9d8b0', '#fff7e8', '#a3246a'] },
  menta: { mode: 'light', name: 'Menta botánico', note: 'Verdes frescos, como un herbario.', c: ['#d4ecdf', '#cfe8f0', '#f1f8e6', '#a8d4a0', '#fffbe6', '#1c6b4a'] },
};
const DEFAULT_SCENE = { dark: 'noche', light: 'papel' };
const FONT_HEAD = { 'editorial-serif': ['Editorial serif', 'Playfair Display / Newsreader — elegante, literaria', "'Playfair Display',Georgia,serif"], 'modern-sans': ['Moderna sans', 'Plus Jakarta Sans / Inter — limpia, tecnológica', "'Plus Jakarta Sans',system-ui,sans-serif"],
  'humanist-serif': ['Humanista serif', 'Lora / Fraunces — cálida, narrativa', "'Lora',Georgia,serif"], 'script-accent': ['Manuscrita de acento', 'Caveat / Dancing Script — personal, artística (sólo títulos principales)', "'Dancing Script',cursive"] };
const FONT_BODY = { 'reading-serif': ['Serif de lectura', 'Source Serif 4 / Georgia — lectura larga sin fatiga ocular', "'Source Serif 4',Georgia,serif"], 'clean-sans': ['Sans limpia', 'Inter / System UI — claridad técnica inmediata', "'Inter',system-ui,sans-serif"],
  'humanist-sans': ['Sans humanista', 'DM Sans / Atkinson Hyperlegible — máxima accesibilidad', "'Atkinson Hyperlegible',system-ui,sans-serif"] };
const FONT_MONO = { jetbrains: ['JetBrains Mono', 'Código y etiquetas', "'JetBrains Mono',monospace"], fira: ['Fira Code', 'Código y etiquetas', "'Fira Code',monospace"] };
const SCALES = { compact: ['Compacta', '16 px · razón 1.20', 'Ideal para documentación técnica densa.', 16, 1.2], editorial: ['Editorial estándar', '18 px · razón 1.25', 'Recomendada: balance estilo Stripe Increment.', 18, 1.25], spacious: ['Lectura amplia', '20 px · razón 1.333', 'Máxima comodidad visual, estilo Stripe Press.', 20, 1.333] };
const LEGACY_FONT = { manuscrita: 'script-accent', clasica: 'editorial-serif', moderna: 'modern-sans' };
const LANGS = ['Python', 'JavaScript', 'SQL', 'Bash', 'JSON', 'HTML', 'CSS', 'Texto'];

const S = {
  token: localStorage.getItem('tk') || '', user: null, blogs: [], blog: null, menu: '', dirty: localStorage.getItem('dirty') === '1', view: 'login', posts: [], pages: [], cats: [], builds: [],
  edit: null, siteUrl: '', flash: '', sel: 0, building: false, theme: { ...DEFAULT_THEME }, themePage: null, metrics: null, q: '', pendingG: false, modal: null, pv: 'split', themeLoaded: false, step: '', insFilter: '', insIdx: 0, pending: null,
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
  const v0 = localStorage.getItem('view'); await go(['posts', 'pages', 'perf'].includes(v0) ? v0 : 'posts');
}

/* ---------- navegación ---------- */
const MENU = [
  ['docs', 'Documentos', [['posts', 'Entradas', 'g d'], ['pages', 'Páginas', 'g p']]],
  ['tpl', 'Plantillas', [['@design', 'Diseño del sitio', 'g a']]],
  ['met', 'Métricas', [['perf', 'Métricas y rendimiento', 'g m']]],
];
const groupOf = (v) => ({ posts: 'docs', 'edit-post': 'docs', pages: 'docs', 'edit-page': 'docs', perf: 'met' }[v]);
async function go(view, extra) {
  S.view = view; S.flash = (extra && extra.flash) || ''; S.sel = 0;
  if (['posts', 'pages', 'perf'].includes(view)) localStorage.setItem('view', view);
  render(true);
  try {
    if (view === 'posts') { await loadPosts(); await loadBuilds(); }
    if (view === 'pages') await loadPages();
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
  if (!S.themeDirty) S.theme = readTheme(S.themePage && S.themePage.content);
  S.themeLoaded = true;
}
function readTheme(content) {                                       // el tema guardado puede ser de la versión antigua (font: manuscrita…)
  let t = {}; try { t = JSON.parse(content || '{}'); } catch (e) { /* tema dañado → por defecto */ }
  const th = { ...DEFAULT_THEME, ...t };
  if (t.font && !t.fontHead) th.fontHead = LEGACY_FONT[t.font] || th.fontHead;
  delete th.font;
  if (!SCENES[th.scene] || SCENES[th.scene].mode !== th.mode) th.scene = DEFAULT_SCENE[th.mode] || 'noche';
  return th;
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

/* ---------- markdown para la vista previa (misma sintaxis que el generador) ---------- */
const safeSrc = (u) => /^(https?:\/\/|\/)[^\s"'<>]*$/.test(u) ? u : '';
function md(src) {
  let n = 0;
  const basic = (t) => esc(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (m, alt, u) => { const q = safeSrc(u.replace(/&amp;/g, '&').replace('#wide', '')); return q ? `<img src="${esc(q)}" alt="${alt}">` : m; })
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  const inline = (t) => basic(t.replace(/\[\^nota:\s*((?:[^\[\]]|\[[^\]]*\]\([^)]*\))+)\]/g, (m, note) => `\u0001${++n}\u0002${note.trim()}\u0003`))
    .replace(/\u0001(\d+)\u0002([\s\S]*?)\u0003/g, (m, k, note) => `<sup class="pv-n">${k}</sup><span class="pv-sn"><b>${k}</b> ${note}</span>`);
  const lines = String(src || '').replace(/\r/g, '').split('\n'), out = []; let list = false, i = 0;
  const endList = () => { if (list) { out.push('</ul>'); list = false; } };
  while (i < lines.length) {
    const l = lines[i].trimEnd(); let m;
    if ((m = /^\s{0,3}```\s*([\w+#.-]*)/.exec(l))) {                // bloque de código
      endList(); const code = []; i++; while (i < lines.length && !/^\s{0,3}```/.test(lines[i])) code.push(lines[i++]); i++;
      out.push(`<div class="codeblock"><span class="lang">${esc((m[1] || 'texto').toUpperCase())}</span><pre>${esc(code.join('\n'))}</pre></div>`); continue;
    }
    if ((m = /^:::(info|tip|warning|wide)(?:\s+(.*))?$/.exec(l.trim()))) {   // cajas y contenedor ancho
      endList(); const inner = []; i++; while (i < lines.length && lines[i].trim() !== ':::') inner.push(lines[i++]); i++;
      if (m[1] === 'wide') out.push(`<figure class="wide">${md(inner.join('\n')).replace(/<\/?p>/g, '')}</figure>`);
      else out.push(`<div class="callout ${m[1]}"><b>${esc(m[2] || { info: 'Idea clave', tip: 'Consejo', warning: 'Ojo' }[m[1]])}</b>${md(inner.join('\n'))}</div>`);
      continue;
    }
    i++;
    if ((m = /^>>\s+(.+)$/.exec(l))) { endList(); out.push(`<aside class="pullquote">${inline(m[1])}</aside>`); continue; }
    const li = /^\s*[-*]\s+(.*)/.exec(l);
    if (li) { if (!list) { out.push('<ul>'); list = true; } out.push('<li>' + inline(li[1]) + '</li>'); continue; }
    endList();
    if ((m = /^!\[([^\]]*)\]\(([^)\s]+)#wide\)\s*$/.exec(l))) { const q = safeSrc(m[2]); if (q) { out.push(`<figure class="wide"><img src="${esc(q)}" alt="${esc(m[1])}"><figcaption>${esc(m[1])}</figcaption></figure>`); continue; } }
    if (/^###\s/.test(l)) out.push('<h3>' + inline(l.slice(4)) + '</h3>');
    else if (/^##\s/.test(l)) out.push('<h2>' + inline(l.slice(3)) + '</h2>');
    else if (/^#\s/.test(l)) out.push('<h1>' + inline(l.slice(2)) + '</h1>');
    else if (/^>\s?/.test(l)) out.push('<blockquote>' + inline(l.replace(/^>\s?/, '')) + '</blockquote>');
    else if (l.trim()) out.push('<p>' + inline(l) + '</p>');
  }
  endList();
  return out.join('') || '<p style="color:var(--mute)">La vista previa aparece aquí mientras escribes…</p>';
}

/* ---------- vistas ---------- */
function shell(inner) {
  const menu = MENU.map(([k, name, items]) => `<div class="dd"><button class="ddb" data-act="menu" data-k="${k}" aria-haspopup="true" aria-expanded="${S.menu === k}" ${groupOf(S.view) === k ? 'aria-current="page"' : ''}>${name} <span aria-hidden="true">▾</span></button>
    ${S.menu === k ? `<div class="ddm" role="menu">${items.map(([v, n, h]) => v[0] === '@' ? `<button role="menuitem" data-act="opendesign">${n}<kbd>${h}</kbd></button>` : `<button role="menuitem" data-act="go" data-v="${v}">${n}<kbd>${h}</kbd></button>`).join('')}</div>` : ''}</div>`).join('');
  return `<div class="bar"><span>Sesión: ${esc(S.user && S.user.email)}</span><span><a href="/docs" target="_blank" rel="noopener">API</a>${S.siteUrl ? `<a href="${esc(S.siteUrl)}" target="_blank" rel="noopener">Ver sitio</a>` : ''}<button data-act="panelmode" aria-label="Cambiar entre modo claro y oscuro del panel" title="Modo claro / oscuro (t)">${document.documentElement.dataset.panel === 'light' ? '☾ Oscuro' : '☀ Claro'} <kbd>t</kbd></button><button data-act="help" title="Guía rápida y atajos">Guía y atajos ?</button><button data-act="logout">Cerrar sesión</button></span></div>
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
  const tb = (act, label, title, extra = '') => `<button type="button" class="tb ${extra}" data-act="${act}" title="${title}" aria-label="${title}">${label}</button>`;
  return `<p style="margin:22px 0 0"><button class="btn ghost sm" data-act="cancel">← Volver <kbd>Esc</kbd></button></p>
  <div class="page-h"><h1>${e.id ? 'Editar' : 'Nueva'} ${isPost ? 'entrada' : 'página'}</h1><span class="state">${e.status === 'published' ? '<b>Publicada</b>' : 'Borrador'} · <button class="btn ghost sm" type="button" data-act="postopts">⚙ Más opciones</button></span></div>
  <div id="recover"></div>
  <div class="split ${S.pv === 'full' ? 'pv-full' : ''}" id="split"><form data-form="edit"><div class="editor-col"><label for="f-title">Título</label><input id="f-title" type="text" data-f="title" value="${esc(e.title)}" required maxlength="200" autofocus>
    <label for="f-content" style="margin-bottom:0">Escribe aquí <small>pulsa <kbd>/</kbd> al inicio de una línea para insertar bloques</small></label>
    <div class="toolbar" role="toolbar" aria-label="Herramientas de escritura">${tb('fmt-bold', '<b>B</b>', 'Negritas (Ctrl B)')}${tb('fmt-italic', '<i>I</i>', 'Cursivas (Ctrl I)')}${tb('fmt-link', '🔗', 'Enlace (Ctrl K)')}${tb('pickimg', '🖼 <span class="hide-s">Imagen</span>', 'Insertar imagen')}
      <span class="sep"></span>${tb('insertmenu', '＋ Bloque editorial <kbd>/</kbd>', 'Insertar bloque editorial', 'main')}${tb('ins-sidenote', '✎<span class="hide-s"> Nota</span>', 'Nota al margen (Ctrl Shift M)')}${tb('ins-pullquote', '❝<span class="hide-s"> Cita</span>', 'Cita destacada (Ctrl Shift Q)')}${tb('ins-codelang', '&lt;/&gt;<span class="hide-s"> Código</span>', 'Bloque de código (Ctrl Shift C)')}
      <span class="grow"></span><small id="imgmsg"></small>${tb('togglepv', '👁 <span class="hide-s">Vista previa</span>', 'Alternar vista previa dividida o completa (Ctrl P)')}</div>
    <input type="file" id="imgfile" accept="image/*" hidden>
    <textarea id="f-content" data-f="content" aria-label="Contenido">${esc(e.content)}</textarea></div>
    <p class="editor-actions"><button class="btn fill" type="submit">Guardar <kbd>Ctrl S</kbd></button><button class="btn" type="button" data-act="savebuild">Guardar y publicar sitio <kbd>Ctrl ↵</kbd></button></p></form>
  <div class="card preview" aria-live="polite"><div class="crumb">Vista previa</div><h1 id="pv-t">${esc(e.title)}</h1><div id="pv">${md(e.content)}</div></div></div>`;
}

function vPages() {
  const rows = S.pages.map((p) => `<tr tabindex="0"><td><div class="t">${esc(p.title)}</div><div class="s">${p.type === 'landing' ? 'Portada' : 'Página'} · /${esc(p.slug)}</div></td><td><span class="pill ${p.status === 'published' ? 'p' : 'd'}">${p.status === 'published' ? 'Publicada' : 'Borrador'}</span></td><td>${fmtDate(p.updatedAt)}</td>
    <td class="act"><button class="btn ghost sm" data-act="editpage" data-id="${p.id}">Editar</button> <button class="btn ghost sm" data-act="delpage" data-id="${p.id}">Borrar</button></td></tr>`).join('');
  return `<div class="page-h"><div><div class="crumb">CMS</div><h1>Páginas</h1></div><button class="btn rose" data-act="newpage">+ Nueva página</button></div>
  <p class="hint"><span>💡</span><span>La <b>portada</b> es el texto de bienvenida del inicio. Las demás páginas (Sobre mí, Proyectos…) aparecen en el menú inferior del sitio.</span></p>
  <div class="card" style="padding:0">${S.pages.length ? `<table><thead><tr><th>Título</th><th>Estado</th><th>Actualizada</th><th></th></tr></thead><tbody>${rows}</tbody></table>` : '<div class="empty"><h2>Aún no hay páginas</h2><p>Crea una portada para que el inicio tenga tu voz.</p></div>'}</div>`;
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
  const box0 = $('.modal .box'), keepTop = box0 ? box0.scrollTop : 0, ae = document.activeElement;     // al redibujar se conserva el foco y el scroll de la ventana
  const focusKey = ae && ae !== document.body ? (ae.id ? '#' + ae.id : ae.name && ae.value ? `[name="${ae.name}"][value="${ae.value}"]` : ae.dataset && ae.dataset.t ? `[data-t="${ae.dataset.t}"]` : '') : '';
  const inModal = ae && ae.closest && ae.closest('.modal');
  let html;
  if (S.view === 'login') html = vLogin();
  else if (S.view === 'onboarding') html = vOnboarding();
  else if (!S.blog) html = vLogin();
  else html = shell({ posts: vPosts, 'edit-post': vEdit, 'edit-page': vEdit, pages: vPages, perf: vPerf }[S.view]());
  app.innerHTML = html + modalHtml();
  if (S.view === 'edit-post' || S.view === 'edit-page') checkRecover();
  const first = $('[autofocus]'); if (first && !S.modal) first.focus();
  if (S.modal) {
    const nb = $('.modal .box'); if (nb) nb.scrollTop = keepTop;
    const again = focusKey && inModal ? $(focusKey) : null;
    if (again) again.focus(); else { const i = $('#pi') || $('.modal [data-autofocus]') || $('.modal .x'); if (i) i.focus(); }
  }
  if (S.pending && !S.modal) {                                      // después de insertar un bloque: el cursor vuelve a la caja de texto
    const ta = $('#f-content'), p = S.pending; S.pending = null;
    if (ta) { ta.focus(); ta.setSelectionRange(p.a, p.b); ta.scrollTop = p.top || 0; }
  }
}

/* ---------- ventanas (modales) ---------- */
const ACTIONS = [
  ['Nueva entrada', 'n', () => newPost()], ['Ir a Entradas', 'g d', () => go('posts')], ['Ir a Páginas', 'g p', () => go('pages')],
  ['Diseño y apariencia', 'g a', () => openDesign()], ['Ir a Métricas', 'g m', () => go('perf')], ['Publicar sitio', 'Ctrl ↵', () => buildSite()],
  ['Cambiar modo claro / oscuro del panel', 't', () => togglePanel()], ['Guía rápida y atajos', '?', () => openModal('help')], ['Cerrar sesión', '', () => logout()],
];
let palFilter = '', palIdx = 0;
const openModal = (m) => { S.modal = m; S.insFilter = ''; S.insIdx = 0; render(); };
const closeModal = () => { S.modal = null; S.step = ''; render(); };
const close = '<button class="x" data-act="closemodal" aria-label="Cerrar (Esc)">✕</button>';
const dlg = (label, inner, wide) => `<div class="modal" data-act="closemodal"><div class="box${wide ? ' wide' : ''}" role="dialog" aria-modal="true" aria-label="${esc(label)}">${inner}</div></div>`;

/* ejemplos copiables de la guía y de «Insertar» */
const SNIPS = [
  ['Nota al margen', 'Una idea[^nota: Aquí va la nota; en el móvil se despliega.] en medio del texto.'],
  ['Cita destacada', '>> Una frase de impacto que quieras destacar.'],
  ['Caja de concepto', ':::info Idea clave\nExplica el concepto en dos líneas.\n:::'],
  ['Caja de consejo', ':::tip Consejo\nUn truco para recordar.\n:::'],
  ['Caja de advertencia', ':::warning Ojo\nAlgo que conviene vigilar.\n:::'],
  ['Bloque de código', '```python\nprint("Hola, Brisa")\n```'],
  ['Contenedor ancho', ':::wide\n![Descripción de la imagen](https://ejemplo.com/imagen.png)\nPie de foto editorial\n:::'],
  ['Imagen ancha', '![Pie de foto](https://ejemplo.com/imagen.png#wide)'],
];
const KEYS_GLOBAL = [['n', 'Nueva entrada'], ['g d', 'Ir a Documentos / Entradas'], ['g p', 'Ir a Páginas'], ['g a', 'Abrir Diseño y apariencia'], ['g m', 'Ir a Métricas y rendimiento'], ['t', 'Alternar modo claro / oscuro del panel'],
  ['?', 'Abrir esta guía'], ['Ctrl K', 'Buscar cualquier acción (fuera del editor)'], ['j / k', 'Moverte por la lista'], ['Enter o e', 'Editar la entrada marcada'], ['d', 'Borrar (con deshacer)'], ['/', 'Buscar entradas'], ['Esc', 'Cerrar una ventana o volver']];
const KEYS_EDITOR = [['Ctrl S', 'Guardar borrador'], ['Ctrl Enter', 'Guardar y publicar el sitio'], ['Ctrl B', 'Negritas'], ['Ctrl I', 'Cursivas'], ['Ctrl K', 'Insertar enlace'], ['Ctrl Shift C', 'Bloque de código (eliges el lenguaje)'],
  ['Ctrl Shift M', 'Nota al margen'], ['Ctrl Shift Q', 'Cita destacada'], ['Ctrl P', 'Vista previa dividida / completa'], ['/ al inicio de línea', 'Menú rápido de bloques']];
const kbdList = (rows) => `<table class="kt"><tbody>${rows.map(([k, t]) => `<tr><td>${k.split(' ').map((x) => (x === '/' || x.length < 7) ? `<kbd>${esc(x)}</kbd>` : esc(x)).join(' ')}</td><td>${t}</td></tr>`).join('')}</tbody></table>`;
const ico = (p) => `<svg viewBox="0 0 64 64" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;

function helpModal() {
  const editing = S.view === 'edit-post' || S.view === 'edit-page';
  return dlg('Guía rápida y atajos', `<div class="mhead"><div><h2>Guía rápida</h2><p class="sub" style="margin:0">Escribir, personalizar y publicar: 60 segundos.</p></div>${close}</div>
  <div class="steps3"><div class="step3">${ico('<rect x="10" y="8" width="38" height="48" rx="5"/><path d="M18 20h22M18 29h22M18 38h14"/><path d="M44 40l12-12 5 5-12 12-7 2z"/>')}<b>1 · Escribe</b><span>Pulsa <kbd>n</kbd>, pon un título y escribe. Con <kbd>/</kbd> insertas bloques de revista.</span></div>
  <div class="step3">${ico('<circle cx="32" cy="32" r="8"/><path d="M32 6v8M32 50v8M6 32h8M50 32h8M13 13l6 6M45 45l6 6M13 51l6-6M45 19l6-6"/>')}<b>2 · Personaliza</b><span>Pulsa <kbd>g</kbd> <kbd>a</kbd>: modo claro u oscuro, atmósfera, letras y tamaño.</span></div>
  <div class="step3">${ico('<path d="M32 6c10 8 14 18 12 32H20C18 24 22 14 32 6z"/><circle cx="32" cy="26" r="4"/><path d="M20 38l-8 10 10-3M44 38l8 10-10-3M28 46l4 12 4-12"/>')}<b>3 · Publica</b><span>Pulsa <kbd>Ctrl</kbd> <kbd>Enter</kbd> o «Publicar sitio». La primera vez puede tardar ~1 minuto.</span></div></div>
  <div class="blk"><h3>Ejemplos de bloques</h3><p class="help">Copia con un clic${editing ? ' o insértalo donde está el cursor' : ''}.</p><div class="snips">${SNIPS.map((x, i) => `<div class="snip"><b>${x[0]}</b><span><button class="btn ghost sm" data-act="copysnip" data-i="${i}">Copiar</button>${editing ? ` <button class="btn sm" data-act="inssnip" data-i="${i}">Insertar</button>` : ''}</span><pre>${esc(x[1])}</pre></div>`).join('')}</div></div>
  <div class="blk"><h3>Atajos del panel</h3>${kbdList(KEYS_GLOBAL)}</div><div class="blk"><h3>Atajos del editor</h3>${kbdList(KEYS_EDITOR)}</div>
  <div class="mfoot"><button class="btn" data-act="closemodal" data-autofocus>Entendido</button></div>`, true);
}

function palModal() {
  const items = ACTIONS.filter((a) => a[0].toLowerCase().includes(palFilter.toLowerCase()));
  palIdx = Math.min(palIdx, Math.max(0, items.length - 1));
  return dlg('Buscar acción', `<div class="pal"><input id="pi" type="text" placeholder="¿Qué quieres hacer?" value="${esc(palFilter)}" autocomplete="off">${items.map((a, i) => `<button data-act="runpal" data-n="${esc(a[0])}" class="${i === palIdx ? 'on' : ''}"><span>${a[0]}</span><kbd>${a[1] || '—'}</kbd></button>`).join('') || '<p class="sub">Sin resultados</p>'}</div>`);
}

/* ---- insertar bloque editorial ---- */
const INSERTS = [['image', '🖼 Imagen', 'Sube una foto y se pone en el texto'], ['sidenote', '✎ Nota al margen', 'Va en la columna derecha; en el móvil se despliega'], ['pullquote', '❝ Cita destacada', 'Una frase grande que rompe la columna'],
  ['info', 'ⓘ Caja de concepto clave', 'Idea importante con borde azul'], ['tip', '💡 Caja de consejo', 'Un truco, con borde verde'], ['warning', '⚠ Caja de advertencia', 'Algo que vigilar, con borde ámbar'],
  ['code', '</> Bloque de código', 'Con lenguaje y botón «Copiar»'], ['wide', '▭ Contenedor ancho (The Pudding)', 'Imagen o gráfico más ancho que el texto']];
function insertModal() {
  if (S.step === 'lang') return dlg('Elegir lenguaje', `<div class="mhead"><h2>¿En qué lenguaje?</h2>${close}</div><p class="sub">Se pondrá la etiqueta del lenguaje y el botón «Copiar».</p><div class="langs">${LANGS.map((l, i) => `<button data-act="inscode" data-l="${l.toLowerCase() === 'texto' ? '' : l.toLowerCase()}" ${i === 0 ? 'data-autofocus' : ''}>${l}</button>`).join('')}</div>`);
  const items = INSERTS.filter((x) => (x[1] + x[2]).toLowerCase().includes(S.insFilter.toLowerCase()));
  S.insIdx = Math.min(S.insIdx, Math.max(0, items.length - 1));
  return dlg('Insertar bloque editorial', `<div class="mhead"><h2>Insertar bloque</h2>${close}</div><div class="pal"><input id="pi" data-ins="1" type="text" placeholder="Busca: nota, cita, código…" value="${esc(S.insFilter)}" autocomplete="off">
  ${items.map((x, i) => `<button data-act="insblock" data-k="${x[0]}" class="${i === S.insIdx ? 'on' : ''}"><span>${x[1]}<small>${x[2]}</small></span></button>`).join('') || '<p class="sub">Sin resultados</p>'}</div>`);
}

/* ---- opciones de la entrada o página ---- */
function optsModal() {
  const e = S.edit, isPost = e.mode === 'post';
  const catOpts = '<option value="">Sin categoría</option>' + S.cats.map((c) => `<option value="${c.id}" ${e.categoryId === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('');
  const body = isPost ? `<label for="f-slug">Dirección (slug) <small>se genera del título si la dejas vacía</small></label><input id="f-slug" type="text" data-f="slug" value="${esc(e.slug)}" placeholder="mi-entrada">
    <label for="f-excerpt">Resumen editorial <small>aparece en las tarjetas</small></label><input id="f-excerpt" type="text" data-f="excerpt" value="${esc(e.excerpt)}" maxlength="300">
    <label for="f-cat">Categoría <small>elige una sección de la portada (Proyectos, Dibujos, Pensamientos…) o «Entrada» para el blog</small></label>
    <div style="display:flex;gap:8px;flex-wrap:wrap"><select id="f-cat" data-f="categoryId" style="flex:1;min-width:180px">${catOpts}</select>${missingSections().length ? '<button class="btn ghost sm" type="button" data-act="addsections">＋ Crear secciones de la portada</button>' : ''}</div>
    <div style="display:flex;gap:8px;margin-top:8px"><input type="text" id="newcat" placeholder="Otra categoría nueva…" aria-label="Nueva categoría"><button class="btn ghost sm" type="button" data-act="addcat">Crear</button></div>
    <label>Imagen de portada</label><div class="coverrow">${e.coverUrl ? `<img src="${esc(e.coverUrl)}" alt="Portada actual">` : '<span class="help">Sin portada</span>'}<button class="btn ghost sm" type="button" data-act="pickcover">Subir imagen</button>${e.coverUrl ? '<button class="btn ghost sm" type="button" data-act="nocover">Quitar</button>' : ''}<input type="file" id="coverfile" accept="image/*" hidden></div>`
    : `<label for="f-slug">Dirección (slug)</label><input id="f-slug" type="text" data-f="slug" value="${esc(e.slug)}" placeholder="se genera del título">
    <label for="f-type">Tipo</label><select id="f-type" data-f="type"><option value="page" ${e.type === 'page' ? 'selected' : ''}>Página</option><option value="landing" ${e.type === 'landing' ? 'selected' : ''}>Texto de la portada</option></select>
    <p class="help">Para tu foto y texto de «Sobre mí»: dirección <b>sobre-mi</b> y la imagen arriba.</p>`;
  return dlg('Más opciones', `<div class="mhead"><h2>Más opciones</h2>${close}</div><p class="sub">Todo lo que no es escribir vive aquí, para que el editor quede limpio.</p>${body}
    <label for="f-status">Estado</label><select id="f-status" data-f="status"><option value="draft" ${e.status !== 'published' ? 'selected' : ''}>Borrador (no se ve en el sitio)</option><option value="published" ${e.status === 'published' ? 'selected' : ''}>Publicado en el blog</option></select>
    <div class="mfoot"><button class="btn" data-act="closemodal" data-autofocus>Listo</button></div>`);
}

/* ---- diseño y apariencia ---- */
function designModal() {
  const t = S.theme, light = t.mode === 'light';
  const thumb = (c) => `<span class="thumb" style="background:radial-gradient(circle at 78% 24%,${c[4]} 0 7%,transparent 8%),linear-gradient(${c[0]},${c[1]} 55%,${c[2]} 70%,${c[3]} 71%)"></span>`;
  const scenes = Object.entries(SCENES).filter(([, v]) => v.mode === t.mode).map(([k, v]) => `<label><input type="radio" name="scene" value="${k}" data-t="scene" ${t.scene === k ? 'checked' : ''}><span class="opt">${thumb(v.c)}<b>${v.name}</b><small>${v.note}</small></span></label>`).join('');
  const lay = (k, n, svg) => `<label><input type="radio" name="blog" value="${k}" data-t="blog" ${t.blog === k ? 'checked' : ''}><span class="opt">${svg}<b>${n}</b></span></label>`;
  const cards = '<svg viewBox="0 0 120 56"><rect x="4" y="6" width="34" height="44" rx="6" fill="currentColor" opacity=".7"/><rect x="43" y="6" width="34" height="44" rx="6" fill="currentColor" opacity=".5"/><rect x="82" y="6" width="34" height="44" rx="6" fill="currentColor" opacity=".35"/></svg>';
  const list = '<svg viewBox="0 0 120 56"><rect x="4" y="5" width="112" height="13" rx="6" fill="currentColor" opacity=".7"/><rect x="4" y="22" width="112" height="13" rx="6" fill="currentColor" opacity=".5"/><rect x="4" y="39" width="112" height="13" rx="6" fill="currentColor" opacity=".35"/></svg>';
  const sc = SCENES[t.scene], acc = t.accent || sc.c[5];
  const fsel = (id, key, map, label, sampleExtra) => `<div class="fontrow"><label for="${id}">${label}</label><select id="${id}" data-t="${key}">${Object.entries(map).map(([k, v]) => `<option value="${k}" ${t[key] === k ? 'selected' : ''}>${v[0]} — ${v[1]}</option>`).join('')}</select><p class="sample" style="font-family:${map[t[key]][2]}${sampleExtra || ''}">${key === 'fontMono' ? 'const idea = "sigo intentándolo";' : key === 'fontHead' ? 'Sigo intentándolo' : 'Escribir despacio también es avanzar, una línea a la vez.'}</p></div>`;
  const [, , , base, ratio] = SCALES[t.fontScale];
  const scale = Object.entries(SCALES).map(([k, v]) => `<label><input type="radio" name="fontScale" value="${k}" data-t="fontScale" ${t.fontScale === k ? 'checked' : ''}><span class="opt"><b>${v[0]}</b>${k === 'editorial' ? '<span class="rec">Recomendada</span>' : ''}<small>${v[1]}</small><small>${v[2]}</small></span></label>`).join('');
  return dlg('Diseño y apariencia', `<div class="mhead"><div><h2>Diseño del sitio</h2><p class="sub" style="margin:0">Elige y listo: el CMS genera el CSS por ti. Nada de código.</p></div>${close}</div>
  <div class="blk"><h3>1 · Modo de color</h3><p class="help">El que verá primero tu lector (él podrá cambiarlo con el botón del sol/luna).</p>
    <div class="mode-sw"><span class="ic ${light ? '' : 'on'}" aria-hidden="true">🌙</span><span class="switch"><input type="checkbox" role="switch" id="md" data-t="mode" ${light ? 'checked' : ''} aria-label="Modo claro (activado) u oscuro (desactivado)"><i></i></span><span class="ic ${light ? 'on' : ''}" aria-hidden="true">☀</span><span id="mdl">${light ? 'Modo claro' : 'Modo oscuro'}</span></div></div>
  <div class="blk"><h3>2 · Escena y atmósfera</h3><p class="help">${light ? 'Atmósferas para modo claro.' : 'Atmósferas para modo oscuro.'}</p><div class="tpl three">${scenes}</div>
    <label for="ac">Color de acento <small>botones y detalles; el CMS cuida que se lea bien</small></label><div style="display:flex;gap:10px;align-items:center"><input id="ac" type="color" data-t="accent" value="${acc}" style="width:54px;height:40px;padding:0;border:0;background:none"><button class="btn ghost sm" data-act="resetaccent">Usar el de la plantilla</button></div>
    <label style="margin-top:16px">Listado del blog</label><div class="tpl">${lay('tarjetas', 'Tarjetas', cards)}${lay('lista', 'Lista', list)}</div></div>
  <div class="blk"><h3>3 · Tipografía, un rol a la vez</h3><p class="help">Tres selectores separados: no se mezclan.</p>${fsel('fh', 'fontHead', FONT_HEAD, 'Títulos (display / headings)', ';font-size:28px;font-weight:700')}${fsel('fb', 'fontBody', FONT_BODY, 'Lectura (cuerpo / body)')}${fsel('fm', 'fontMono', FONT_MONO, 'Código y etiquetas (monospace)', ';font-size:14px')}</div>
  <div class="blk"><h3>4 · Escala de tamaño</h3><p class="help">Tres perfiles ya calculados para que la jerarquía siempre se vea bien.</p><div class="scalecards">${scale}</div></div>
  <div class="pvbox" style="background:${sc.c[0]};color:${light ? '#1d1b16' : '#eef1ff'};font-family:${FONT_BODY[t.fontBody][2]}"><h4 style="font-family:${FONT_HEAD[t.fontHead][2]};font-size:${Math.round(base * ratio * ratio)}px;line-height:1.1;margin:0 0 6px">Así se verá un título</h4><p style="font-size:${base}px;margin:0 0 8px">Y así el texto de lectura, con <code style="font-family:${FONT_MONO[t.fontMono][2]}">código</code> y una <span style="color:${acc};font-weight:700">palabra de acento</span>.</p></div>
  <details class="blk"><summary>¿Cómo se mete el CSS? (para entenderlo)</summary><ol style="line-height:1.8"><li>Tú eliges modo, escena, letras y tamaño aquí.</li><li>Al publicar, el CMS lo convierte en variables CSS con contraste mínimo WCAG AA (4,5:1) y las manda al generador.</li><li>El generador ya trae el diseño; sólo le pone tus variables.</li></ol><p><button class="btn ghost sm" data-act="showcss">Ver el CSS que genera el CMS</button></p><div id="cssbox"></div></details>
  <div class="mfoot"><button class="btn ghost" data-act="closemodal">Cerrar</button><button class="btn" data-act="savetheme">Guardar tema</button><button class="btn fill" data-act="savethemebuild">Guardar y publicar sitio</button></div>`, true);
}

function modalHtml() {
  if (!S.modal) return '';
  return { help: helpModal, pal: palModal, insert: insertModal, post: optsModal, design: designModal }[S.modal]();
}

/* ---------- edición ---------- */
const draftKey = () => `draft:${S.blog.id}:${S.edit.mode}:${S.edit.id || 'nuevo'}`;
function newPost() { S.edit = { mode: 'post', id: null, title: '', excerpt: '', content: '', categoryId: null, status: 'draft', slug: '', coverUrl: null }; S.view = 'edit-post'; S.flash = ''; render(); }
async function editPost(id) {
  try { const p = await api('GET', `/blogs/${S.blog.id}/posts/${id}`); S.edit = { mode: 'post', id: p.id, title: p.title, excerpt: p.excerpt || '', content: p.content || '', categoryId: p.categoryId, status: p.status, slug: p.slug, coverUrl: p.coverUrl || null }; S.view = 'edit-post'; S.flash = ''; render(); } catch (e) { toast(e.message); }
}
function editPage(p) { S.edit = { mode: 'page', id: p ? p.id : null, title: p ? p.title : '', content: p ? p.content : '', type: p ? p.type : 'page', status: p ? p.status : 'draft', slug: p ? p.slug : '' }; S.view = 'edit-page'; S.flash = ''; render(); }
function checkRecover() {
  let d = null; try { d = JSON.parse(localStorage.getItem(draftKey()) || 'null'); } catch (e) { /* ignorado */ }
  const box = $('#recover'); if (!d || !box || (d.title === S.edit.title && d.content === S.edit.content)) return;
  box.innerHTML = `<div class="flash">Encontré cambios sin guardar de ${esc(new Date(d.at).toLocaleString('es-MX'))}. <button class="btn sm" data-act="recover">Recuperar</button> <button class="btn ghost sm" data-act="dropdraft">Descartar</button></div>`;
}
function draftSoon() {
  clearTimeout(S.dt);
  S.dt = setTimeout(() => { try { localStorage.setItem(draftKey(), JSON.stringify({ at: Date.now(), data: { title: S.edit.title, excerpt: S.edit.excerpt, content: S.edit.content, categoryId: S.edit.categoryId, status: S.edit.status, slug: S.edit.slug, coverUrl: S.edit.coverUrl } })); } catch (e) { /* sin almacenamiento */ } }, 600);
}
async function saveEdit(then) {
  const e = S.edit; if (!e.title.trim()) { toast('Escribe un título primero.'); return; }
  const base = e.mode === 'post' ? `/blogs/${S.blog.id}/posts` : `/blogs/${S.blog.id}/pages`;
  const body = e.mode === 'post' ? { title: e.title, excerpt: e.excerpt || null, content: e.content, categoryId: e.categoryId, status: e.status, coverUrl: e.coverUrl || null } : { title: e.title, content: e.content, type: e.type, status: e.status };
  if (e.slug) body.slug = e.slug;
  try {
    await api(e.id ? 'PUT' : 'POST', e.id ? `${base}/${e.id}` : base, body);
    clearTimeout(S.dt); localStorage.removeItem(draftKey()); markDirty(); S.modal = null;
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
    S.themePage = saved; S.themeDirty = false; markDirty(); toast('Tema guardado.'); if (then) { S.modal = null; render(); buildSite(); }
  } catch (e) { toast('No se pudo guardar el tema: ' + e.message); }
}
async function openDesign() {
  if (!S.blog) return;
  if (!S.themeLoaded) { try { await loadPages(); } catch (e) { toast(e.message); return; } }
  openModal('design');
}

/* ---------- modo claro / oscuro del panel ---------- */
function togglePanel() {
  const m = document.documentElement.dataset.panel === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.panel = m; try { localStorage.setItem('panel-mode', m); } catch (e) { /* sin almacenamiento */ }
  render();
}

/* ---------- insertar bloques y formato en el texto ---------- */
function copyText(txt) {
  if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(txt).then(() => true, () => false);
  const t = document.createElement('textarea'); t.value = txt; t.style.cssText = 'position:fixed;opacity:0'; document.body.append(t); t.select();
  let ok = false; try { ok = document.execCommand('copy'); } catch (e) { /* sin permiso */ } t.remove(); return Promise.resolve(ok);
}
function selection() {                                              // dónde está el cursor: la caja de texto, o lo guardado al abrir una ventana
  const ta = $('#f-content'), e = S.edit;
  if (e && e.sel) return { a: e.sel[0], b: e.sel[1], top: e.sel[2] || 0 };
  return ta ? { a: ta.selectionStart, b: ta.selectionEnd, top: ta.scrollTop } : { a: e.content.length, b: e.content.length, top: 0 };
}
function remember() { const ta = $('#f-content'); if (ta && S.edit) S.edit.sel = [ta.selectionStart, ta.selectionEnd, ta.scrollTop]; }
/* construye el texto de cada bloque; `pick` es lo que se deja seleccionado para escribir encima */
function snippet(kind, sel, opt = {}) {
  const T = (x, d) => (sel && sel.trim() ? sel : d);
  switch (kind) {
    case 'bold': return { t: `**${T(sel, 'texto')}**`, pre: 2, len: T(sel, 'texto').length };
    case 'italic': return { t: `*${T(sel, 'texto')}*`, pre: 1, len: T(sel, 'texto').length };
    case 'link': { const x = T(sel, 'texto'); return { t: `[${x}](https://)`, pre: x.length + 3, len: 8 }; }
    case 'sidenote': { const x = T(sel, 'Texto de la nota'); return { t: `[^nota: ${x}]`, pre: 8, len: x.length }; }
    case 'pullquote': { const x = T(sel, 'Una frase que quieras destacar'); return { t: `>> ${x}`, pre: 3, len: x.length, block: true }; }
    case 'info': case 'tip': case 'warning': { const title = { info: 'Idea clave', tip: 'Consejo', warning: 'Ojo' }[kind], x = T(sel, 'Escribe aquí el texto de la caja.'); return { t: `:::${kind} ${title}\n${x}\n:::`, pre: kind.length + title.length + 5, len: x.length, block: true }; }
    case 'code': { const x = T(sel, '# tu código aquí'), l = opt.lang || ''; return { t: '```' + l + `\n${x}\n` + '```', pre: 4 + l.length, len: x.length, block: true }; }
    case 'wide': { const x = T(sel, '![Descripción de la imagen](https://)\nPie de foto editorial'); return { t: `:::wide\n${x}\n:::`, pre: 8, len: x.length, block: true }; }
    default: return null;
  }
}
function applyInsert(kind, opt) {
  const e = S.edit; if (!e) return; const { a, b, top } = selection(), sel = e.content.slice(a, b), sn = snippet(kind, sel, opt); if (!sn) return;
  let pre = '', post = '', off = 0;
  if (sn.block) {                                                   // los bloques van en su propio párrafo
    const before = e.content.slice(0, a), after = e.content.slice(b);
    pre = !before || before.endsWith('\n\n') ? '' : before.endsWith('\n') ? '\n' : '\n\n'; post = !after || after.startsWith('\n\n') ? '' : after.startsWith('\n') ? '\n' : '\n\n'; off = pre.length;
  }
  e.content = e.content.slice(0, a) + pre + sn.t + post + e.content.slice(b); e.sel = null;
  const from = a + off + sn.pre; S.pending = { a: from, b: from + sn.len, top };
  S.modal = null; S.step = ''; draftSoon(); render();
}
function wrapOnly(kind) { remember(); applyInsert(kind); }
function insertRaw(txt) {                                           // para los ejemplos de la guía
  const e = S.edit; if (!e) return; const { a, b, top } = selection(); const before = e.content.slice(0, a);
  const pre = !before || before.endsWith('\n\n') ? '' : before.endsWith('\n') ? '\n' : '\n\n';
  e.content = before + pre + txt + '\n\n' + e.content.slice(b); e.sel = null; S.pending = { a: before.length + pre.length + txt.length + 2, b: before.length + pre.length + txt.length + 2, top };
  S.modal = null; draftSoon(); render();
}
function openInsert(step) { remember(); S.step = step || ''; openModal('insert'); }
function togglePreview() { S.pv = S.pv === 'full' ? 'split' : 'full'; const sp = $('#split'); if (sp) sp.classList.toggle('pv-full', S.pv === 'full'); }

/* ---------- eventos ---------- */
const H = {
  go: (d) => { S.menu = ''; go(d.v); }, logout: () => logout(), help: () => { remember(); openModal('help'); }, palette: () => { palFilter = ''; palIdx = 0; openModal('pal'); },
  opendesign: () => { S.menu = ''; openDesign(); }, panelmode: () => togglePanel(), postopts: () => { remember(); openModal('post'); },
  closemodal: (d, ev) => { if (ev.target === ev.currentTarget) closeModal(); }, build: () => buildSite(), new: () => newPost(),
  edit: (d) => editPost(Number(d.id)), del: (d) => deletePost(Number(d.id)), cancel: () => { clearTimeout(S.dt); go(S.edit && S.edit.mode === 'page' ? 'pages' : 'posts'); },
  toggle: async (d) => { const p = S.posts.find((x) => x.id === Number(d.id)); const st = p.status === 'published' ? 'draft' : 'published'; try { await api('PATCH', `/blogs/${S.blog.id}/posts/${p.id}/status`, { status: st }); p.status = st; markDirty(); toast(st === 'published' ? 'Marcada como publicada. Pulsa «Publicar sitio» para verla en línea.' : 'Vuelta a borrador.'); await loadBuilds(); render(); } catch (e) { toast(e.message); } },
  savebuild: () => saveEdit(true), newpage: () => editPage(null), editpage: (d) => editPage(S.pages.find((p) => p.id === Number(d.id))),
  delpage: async (d) => { if (!confirm('¿Borrar esta página? Puedes volver a crearla, pero perderás su texto.')) return; try { await api('DELETE', `/blogs/${S.blog.id}/pages/${d.id}`); markDirty(); await go('pages'); toast('Página borrada.'); } catch (e) { toast(e.message); } },
  recover: () => { const d = JSON.parse(localStorage.getItem(draftKey())); Object.assign(S.edit, d.data); render(); toast('Cambios recuperados.'); }, dropdraft: () => { localStorage.removeItem(draftKey()); $('#recover').innerHTML = ''; },
  pickimg: () => { remember(); $('#imgfile').click(); }, pickcover: () => $('#coverfile').click(), nocover: () => { S.edit.coverUrl = null; draftSoon(); render(); },
  addsections: async () => { try { for (const n of missingSections()) S.cats.push(await api('POST', `/blogs/${S.blog.id}/categories`, { name: n })); render(); toast('Listo: ya puedes elegir Dibujos, Proyectos, Pensamientos o Innovación textil.'); } catch (e) { toast(e.message); } },
  addcat: async () => { const n = $('#newcat').value.trim(); if (!n) return; try { const c = await api('POST', `/blogs/${S.blog.id}/categories`, { name: n }); S.cats.push(c); S.edit.categoryId = c.id; render(); toast('Categoría creada.'); } catch (e) { toast(e.message); } },
  runpal: (d) => { const a = ACTIONS.find((x) => x[0] === d.n); S.modal = null; render(); if (a) a[2](); },
  resetaccent: () => { S.theme.accent = null; S.themeDirty = true; render(); },
  menu: (d) => { S.menu = S.menu === d.k ? '' : d.k; render(); setTimeout(() => { const f = $('.ddm button'); if (f) f.focus(); }, 0); },
  savetheme: () => saveTheme(false), savethemebuild: () => saveTheme(true),
  showcss: async () => { try { const r = await api('POST', '/theme/css', S.theme); $('#cssbox').innerHTML = `<div style="margin-top:10px"><p class="sub">Esto se envía al generador. Sólo contiene variables validadas.</p><pre class="css">${esc(r.css.replace(/;/g, ';\n  ').replace(/\{/g, '{\n  '))}</pre></div>`; } catch (e) { toast(e.message); } },
  'fmt-bold': () => wrapOnly('bold'), 'fmt-italic': () => wrapOnly('italic'), 'fmt-link': () => wrapOnly('link'),
  'ins-sidenote': () => wrapOnly('sidenote'), 'ins-pullquote': () => wrapOnly('pullquote'), 'ins-codelang': () => openInsert('lang'), insertmenu: () => openInsert(''), togglepv: () => togglePreview(),
  insblock: (d) => { if (d.k === 'image') { S.modal = null; render(); const f = $('#imgfile'); if (f) f.click(); } else if (d.k === 'code') { S.step = 'lang'; render(); } else applyInsert(d.k); },
  inscode: (d) => applyInsert('code', { lang: d.l }),
  copysnip: async (d, ev) => { const ok = await copyText(SNIPS[Number(d.i)][1]); ev.currentTarget.textContent = ok ? '¡Copiado!' : 'Selecciona y copia'; setTimeout(() => { ev.currentTarget.textContent = 'Copiar'; }, 1500); },
  inssnip: (d) => insertRaw(SNIPS[Number(d.i)][1]),
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
  if (t.id === 'pi') { const pos = t.selectionStart; if (t.dataset.ins) { S.insFilter = t.value; S.insIdx = 0; } else { palFilter = t.value; palIdx = 0; } render(); const i = $('#pi'); i.focus(); i.setSelectionRange(pos, pos); return; }
  if (t.dataset.f && S.edit) {
    const k = t.dataset.f; S.edit[k] = k === 'categoryId' ? (t.value ? Number(t.value) : null) : t.value;
    if (k === 'title') { const h = $('#pv-t'); if (h) h.textContent = t.value; } if (k === 'content') { const p = $('#pv'); if (p) p.innerHTML = md(t.value); }
    if (k === 'status') render();
    draftSoon();
  }
});
document.addEventListener('change', async (ev) => {
  const t = ev.target;
  if ((t.id === 'imgfile' || t.id === 'coverfile') && t.files[0] && S.edit) {
    const cover = t.id === 'coverfile', msg = $('#imgmsg'); if (msg) msg.textContent = ' Subiendo…';
    try {
      const blob = await shrink(t.files[0]), fd = new FormData(); fd.append('file', blob, (t.files[0].name || 'imagen').replace(/\.[^.]+$/, '') + '.jpg');
      const m = await api('POST', `/blogs/${S.blog.id}/media`, undefined, fd);
      if (cover) { S.edit.coverUrl = m.url; draftSoon(); render(); toast('Portada puesta.'); }
      else {
        const name = (t.files[0].name || '').replace(/\.[^.]+$/, ''), { a, top } = selection(), c = S.edit.content, before = c.slice(0, a);
        const ins = `![${name}](${m.url})`, pre = !before || before.endsWith('\n\n') ? '' : before.endsWith('\n') ? '\n' : '\n\n';
        S.edit.content = before + pre + ins + '\n\n' + c.slice(a); S.edit.sel = null; const end = before.length + pre.length + ins.length + 2; S.pending = { a: end, b: end, top }; draftSoon(); render();
        const msg2 = $('#imgmsg'); if (msg2) msg2.textContent = ' ✓ Imagen puesta en el texto';
      }
    } catch (e) { if (msg) msg.textContent = ' ' + e.message; else toast(e.message); }
    t.value = ''; return;
  }
  if (!t.dataset.t) return;
  const k = t.dataset.t;
  if (k === 'mode') { S.theme.mode = t.checked ? 'light' : 'dark'; if (SCENES[S.theme.scene].mode !== S.theme.mode) S.theme.scene = DEFAULT_SCENE[S.theme.mode]; }
  else S.theme[k] = t.type === 'checkbox' ? t.checked : t.value;
  S.themeDirty = true; render();
});

/* ---------- teclado ---------- */
const focusables = (root) => [...root.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]):not([hidden]),select,textarea,[tabindex]:not([tabindex="-1"])')].filter((x) => x.offsetParent !== null);
document.addEventListener('keydown', (ev) => {
  const act = document.activeElement, tag = (act.tagName || ''), typing = /INPUT|TEXTAREA|SELECT/.test(tag), editing = S.view === 'edit-post' || S.view === 'edit-page', inTa = act && act.id === 'f-content';
  const mod = ev.ctrlKey || ev.metaKey, key = (ev.key || '').toLowerCase();
  if (S.modal) {                                                    // ventana abierta: foco atrapado, Esc cierra, flechas y Enter en las listas
    if (ev.key === 'Escape') { ev.preventDefault(); closeModal(); return; }
    if (ev.key === 'Tab') { const box = $('.modal .box'); if (box) { const f = focusables(box); if (f.length) { const i = f.indexOf(act); if (ev.shiftKey && (i <= 0)) { ev.preventDefault(); f[f.length - 1].focus(); } else if (!ev.shiftKey && (i === f.length - 1 || i < 0)) { ev.preventDefault(); f[0].focus(); } } } return; }
    const list = S.modal === 'pal' ? ACTIONS.filter((a) => a[0].toLowerCase().includes(palFilter.toLowerCase())) : S.modal === 'insert' && S.step !== 'lang' ? INSERTS.filter((x) => (x[1] + x[2]).toLowerCase().includes(S.insFilter.toLowerCase())) : null;
    if (list && ['ArrowDown', 'ArrowUp', 'Enter'].includes(ev.key)) {
      ev.preventDefault(); const n = Math.max(1, list.length);
      if (ev.key === 'Enter') { const it = list[S.modal === 'pal' ? palIdx : S.insIdx]; if (!it) return; if (S.modal === 'pal') { S.modal = null; render(); it[2](); } else H.insblock({ k: it[0] }); return; }
      const d = ev.key === 'ArrowDown' ? 1 : -1; if (S.modal === 'pal') palIdx = (palIdx + d + n) % n; else S.insIdx = (S.insIdx + d + n) % n; render();
    }
    return;
  }
  if (!S.token) return;
  if (mod && editing && inTa) {                                     // atajos de escritura (sólo con el cursor en el texto)
    if (!ev.shiftKey && key === 'b') { ev.preventDefault(); wrapOnly('bold'); return; }
    if (!ev.shiftKey && key === 'i') { ev.preventDefault(); wrapOnly('italic'); return; }
    if (!ev.shiftKey && key === 'k') { ev.preventDefault(); wrapOnly('link'); return; }
    if (ev.shiftKey && key === 'c') { ev.preventDefault(); openInsert('lang'); return; }
    if (ev.shiftKey && key === 'm') { ev.preventDefault(); wrapOnly('sidenote'); return; }
    if (ev.shiftKey && key === 'q') { ev.preventDefault(); wrapOnly('pullquote'); return; }
  }
  if (mod && editing && !ev.shiftKey && key === 'p') { ev.preventDefault(); togglePreview(); return; }
  if (mod && key === 'k') { ev.preventDefault(); H.palette(); return; }
  if (mod && key === 's' && editing) { ev.preventDefault(); saveEdit(false); return; }
  if (mod && ev.key === 'Enter') { ev.preventDefault(); if (editing) saveEdit(true); else buildSite(); return; }
  if (editing && inTa && ev.key === '/' && !mod && !ev.altKey) {    // «/» al inicio de una línea → menú de bloques
    const p = act.selectionStart; if (p === act.selectionEnd && (p === 0 || act.value[p - 1] === '\n')) { ev.preventDefault(); openInsert(''); return; }
  }
  if (ev.key === 'Escape' && S.menu) { S.menu = ''; render(); return; }
  if (S.menu && (ev.key === 'ArrowDown' || ev.key === 'ArrowUp')) { ev.preventDefault(); const b = [...document.querySelectorAll('.ddm button')]; const i = b.indexOf(document.activeElement); (b[(i + (ev.key === 'ArrowDown' ? 1 : -1) + b.length) % b.length] || b[0]).focus(); return; }
  if (ev.key === 'Escape') { if (editing) clearTimeout(S.dt); if (editing) go(S.edit.mode === 'page' ? 'pages' : 'posts'); else if (typing) document.activeElement.blur(); return; }
  if (typing || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (S.pendingG) { S.pendingG = false; const m = { d: 'posts', e: 'posts', p: 'pages', m: 'perf', r: 'perf' }[ev.key]; if (m) { ev.preventDefault(); go(m); } else if (ev.key === 'a') { ev.preventDefault(); openDesign(); } return; }
  if (ev.key === 'g') { S.pendingG = true; setTimeout(() => { S.pendingG = false; }, 1200); return; }
  if (ev.key === '?') { H.help(); return; }
  if (ev.key === 't') { togglePanel(); return; }
  if (ev.key === 'n' && S.view !== 'posts') { ev.preventDefault(); newPost(); return; }
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
