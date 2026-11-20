"""CSS y JavaScript del sitio generado. Todos los colores salen de variables (--bg, --text, --accent…) que genera el CMS
con contraste WCAG AA, por eso el mismo CSS sirve para modo claro y oscuro."""

CSS = """*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;min-height:100vh;color:var(--text);font:16px/1.65 var(--font-body);background:var(--bg);padding-bottom:84px;transition:opacity .18s}
body.leaving{opacity:0}
h1,h2,h3{font-family:var(--font-head);font-weight:700;line-height:1.1;margin:0}a{color:var(--accent-text)}
.skip{position:absolute;left:-999px;top:8px;background:var(--accent);color:var(--on-accent);padding:8px 14px;border-radius:10px;z-index:99}.skip:focus{left:12px}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:8px}
.tw{animation:tw 4.5s ease-in-out infinite alternate}@keyframes tw{from{opacity:.25}to{opacity:1}}
@media (prefers-reduced-motion:reduce){.tw{animation:none}html{scroll-behavior:auto}*{transition:none!important}}
.wrap{max-width:1140px;margin:0 auto;padding:0 22px}
.scene{position:relative;overflow:hidden;min-height:clamp(560px,86vh,820px);display:flex;flex-direction:column;background:var(--sky1)}
.scene.compact{min-height:300px}.scene.compact .hero-in{padding-top:12px}
.scenesvg{position:absolute;inset:0;width:100%;height:100%}.scene::after{content:"";position:absolute;inset:auto 0 0 0;height:90px;background:linear-gradient(transparent,var(--bg));pointer-events:none}
.top{position:relative;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 0}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--hero);font:700 28px var(--font-head);text-shadow:0 2px 14px var(--hero-shadow)}.brand svg{width:28px;height:28px}
.kicker{font:600 11px var(--font-mono);letter-spacing:.16em;text-transform:uppercase;color:var(--accent-text)}.top .kicker{text-shadow:0 1px 8px var(--hero-shadow)}
.top-r{display:flex;align-items:center;gap:14px}
.modebtn{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;border:1.5px solid var(--accent);background:var(--surface);color:var(--accent-text);cursor:pointer;backdrop-filter:blur(6px)}
.modebtn svg{width:20px;height:20px}.modebtn .moon{display:none}:root[data-mode=dark] .modebtn .sun{display:none}:root[data-mode=dark] .modebtn .moon{display:block}
.hero-in{position:relative;z-index:2;flex:1;display:flex;align-items:center;padding-bottom:70px}.hero-in .box{max-width:720px}
.hero-in h1{font-size:clamp(52px,9vw,108px);color:var(--hero);text-shadow:0 4px 30px var(--hero-shadow);margin:6px 0 12px}.compact .hero-in h1{font-size:clamp(34px,6vw,var(--step-5))}
.hero-in .intro{color:var(--hero);font-size:18px;max-width:52ch;text-shadow:0 2px 14px var(--hero-shadow)}.hero-in .intro p{margin:0 0 10px}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 22px;border-radius:999px;border:1.5px solid var(--accent);color:var(--accent-text);background:var(--surface);text-decoration:none;font-weight:600;font-size:14px;transition:transform .15s;backdrop-filter:blur(4px)}
.btn:hover{transform:translateY(-2px)}.btn.fill{background:var(--accent);color:var(--on-accent)}
.sec{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:36px 0 16px}.sec h2{font-size:clamp(34px,5vw,48px)}.sec a{font-weight:600;font-size:14px}
.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.cat{padding:20px 22px;border-radius:20px;border:1px solid var(--border);background:var(--surface);text-decoration:none;color:inherit}.cat:hover{border-color:var(--accent)}
.cat h3{font-size:clamp(1.4rem,2vw,2rem);overflow-wrap:break-word;hyphens:auto}.cat span{color:var(--text-muted);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}.grid.list{grid-template-columns:1fr}
.card{display:flex;flex-direction:column;gap:8px;min-width:0;padding:20px 22px;border-radius:20px;border:1px solid var(--border);background:var(--surface);text-decoration:none;color:inherit;transition:transform .18s,border-color .18s,box-shadow .18s}
.card:hover,.card:focus-visible{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 14px 34px rgba(0,0,0,.25)}
.card.big{grid-column:span 2}.card.big h3{font-size:46px}
.grid.list .card{flex-direction:row;align-items:center;flex-wrap:wrap;gap:14px}.grid.list .card h3{flex:1 1 240px}.grid.list .card p{flex:2 1 260px}
.card h3{font-size:32px;overflow-wrap:break-word}.card p{margin:0;color:var(--text-muted);font-size:15px}
.chip{align-self:flex-start;font:600 11px var(--font-mono);letter-spacing:.1em;text-transform:uppercase;padding:3px 10px;border-radius:999px;background:var(--border);color:var(--accent-text);border:0}
.meta{font:12px var(--font-mono);color:var(--text-muted);margin-top:auto}.more{color:var(--accent-text);font-weight:600;font-size:14px}
.note{margin:40px 0 10px;background:var(--paper);color:#2a2540;border-radius:22px;padding:24px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.note h2{font-size:36px;color:#241f3d}.note p{margin:4px 0 0;max-width:56ch;font-size:15px}.note .n{font:700 56px var(--font-head);color:#8f5a00;line-height:1;text-align:center}
.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 16px}.tools input{flex:1 1 220px;max-width:340px;padding:10px 16px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--text);font:inherit}
.chip.f{cursor:pointer;padding:7px 14px;font-size:12px}.chip.f[aria-pressed=true]{background:var(--accent);color:var(--on-accent)}
.panel{padding:18px 20px;border-radius:18px;border:1px solid var(--border);background:var(--surface)}
.panel h3{font-size:28px;margin-bottom:6px}.panel a{display:block;padding:7px 0;color:var(--text);text-decoration:none;border-bottom:1px dashed var(--border);font-size:15px}.panel a:last-child{border:0}.panel a:hover{color:var(--accent-text)}
#prog{position:fixed;z-index:9;top:0;left:0;height:3px;width:0;background:var(--accent)}
.dock{position:fixed;z-index:5;left:50%;bottom:14px;transform:translateX(-50%);display:flex;gap:6px;padding:8px;border-radius:22px;background:var(--dock);border:1px solid var(--border);backdrop-filter:blur(10px);max-width:calc(100vw - 20px);overflow-x:auto}
.dock a{display:flex;align-items:center;gap:7px;padding:10px 16px;border-radius:15px;color:var(--text);text-decoration:none;font-size:13px;font-weight:600;white-space:nowrap}
.dock a:hover{background:var(--surface)}.dock a[aria-current=page]{background:var(--accent);color:var(--on-accent)}
.foot{text-align:center;color:var(--text-muted);font-size:12px;padding:26px 0 10px}
@media (max-width:820px){.card.big{grid-column:auto}.top .kicker{display:none}.scene{min-height:560px}.scene.compact{min-height:260px}}

/* ---------- artículo editorial: 3 carriles (lectura · marginalia · ancho completo) ---------- */
.editorial-post{--main:min(65ch,680px);--gap:32px;--margin:240px;font-size:var(--text-base);line-height:1.75;padding:26px 0 20px;
 display:grid;grid-template-columns:[full-start] minmax(0,1fr) [main-start] minmax(0,var(--main)) [main-end] var(--gap) [margin-start] var(--margin) [margin-end] minmax(0,1fr) [full-end];counter-reset:sn}
.editorial-post>*,.editorial-post .prose>*{grid-column:main-start/main-end;min-width:0}
.editorial-post .prose{display:contents}
.editorial-post .back{margin-bottom:18px;display:inline-block}
.editorial-post .prose>p,.editorial-post .prose>ul,.editorial-post .prose>ol{margin:0 0 1.15em}
.editorial-post .prose>p:first-of-type::first-letter{float:left;font:700 3.6em/.82 var(--font-head);padding:.08em .1em 0 0;color:var(--accent-text)}
.editorial-post .prose h1{font-size:var(--step-4);margin:1.4em 0 .4em}
.editorial-post .prose h2{font-size:var(--step-3);margin:1.5em 0 .35em;scroll-margin-top:16px}
.editorial-post .prose h3{font-size:var(--step-2);margin:1.3em 0 .3em;scroll-margin-top:16px}
.editorial-post .prose a{text-underline-offset:3px}
.editorial-post .prose img{max-width:100%;border-radius:14px}
.editorial-post .prose blockquote{margin:1.4em 0;padding:2px 0 2px 1.2em;border-left:3px solid var(--accent);color:var(--text-muted);font-family:var(--font-head);font-size:var(--step-1)}
.editorial-post .prose code{font:.88em var(--font-mono);background:var(--border);padding:.12em .4em;border-radius:6px}
.editorial-post .prose pre code{background:none;padding:0}
.editorial-post .tags{margin:1.4em 0 0}
@media (max-width:1079px){.editorial-post{grid-template-columns:[full-start] 0 [main-start] minmax(0,1fr) [main-end] 0 [margin-start] 0 [margin-end] 0 [full-end]}}
/* notas al margen */
.sn-num{counter-increment:snc}.sn-num::after{content:counter(snc);font:700 .7em var(--font-mono);vertical-align:super;color:var(--accent-text);cursor:pointer;padding:0 .15em}
.sidenote::before{content:counter(snc) " ";font:700 .85em var(--font-mono);color:var(--accent-text)}
.editorial-post{counter-reset:snc}
.margin-toggle{display:none}
.sidenote{display:none;font-size:.82rem;line-height:1.5;color:var(--text-muted);margin:.6em 0;padding:.6em .8em;border-left:3px solid var(--accent);background:var(--surface);border-radius:0 10px 10px 0}
.margin-toggle:checked+.sidenote{display:block}
@media (min-width:1080px){.sidenote,.margin-toggle:checked+.sidenote{display:block;float:right;clear:right;width:var(--margin);margin:.2em calc(-1 * (var(--margin) + var(--gap))) 0 0;padding:0 0 0 .8em;background:none;border-radius:0}
 .sn-num{pointer-events:none}}
/* cita destacada */
.pullquote{margin:1.8em 0;padding:.2em 0 .2em 1.1em;border-left:4px solid var(--accent);font:600 var(--step-2)/1.25 var(--font-head);color:var(--text)}
.pullquote p{margin:0}
@media (min-width:1080px){.editorial-post .pullquote{grid-column:main-start/margin-end;padding-left:1.4em;font-size:var(--step-3);margin:1.5em 0}}
/* cajas de concepto */
.callout{margin:1.5em 0;padding:14px 18px;border-left:3px solid var(--c,var(--accent));background:var(--surface);border-radius:0 14px 14px 0;--c:var(--accent)}
.callout.info{--c:#3b82c4}.callout.tip{--c:#2e9a68}.callout.warning{--c:#d68a00}
.callout-t{display:flex;align-items:center;gap:9px;font:700 .8em var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--text)}.callout-t svg{width:20px;height:20px;flex:none;color:var(--c)}
.callout-b{margin-top:.4em;font-size:.95em}.callout-b>p{margin:.4em 0}.callout-b>:last-child{margin-bottom:0}
/* código */
.codeblock{margin:1.5em 0;border:1px solid var(--border);border-radius:14px;overflow:hidden;background:var(--code-bg);font-size:.86rem;line-height:1.6}
.codebar{display:flex;align-items:center;justify-content:space-between;padding:6px 10px 6px 14px;border-bottom:1px solid var(--border);background:var(--surface)}
.codebar .lang{font:700 .72rem var(--font-mono);letter-spacing:.12em;color:var(--accent-text)}
.copy{font:600 .72rem var(--font-mono);color:var(--text);background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer}.copy:hover{border-color:var(--accent)}.copy.ok{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}
.codeblock pre{margin:0;padding:14px;overflow:auto;font-family:var(--font-mono)}.codeblock code{font-family:var(--font-mono)}
.tk-c{color:var(--tk-c)}.tk-s{color:var(--tk-s)}.tk-k{color:var(--tk-k)}.tk-n{color:var(--tk-n)}.tk-f{color:var(--tk-f)}
:root[data-mode=dark]{--tk-c:#8a96bd;--tk-s:#8fd6a4;--tk-k:#ff9e8a;--tk-n:#f5c451;--tk-f:#8ec5ff}
:root[data-mode=light]{--tk-c:#5f6b7a;--tk-s:#1b6e3f;--tk-k:#b3261e;--tk-n:#8a5a00;--tk-f:#0b5cad}
/* ancho completo (estilo The Pudding) */
.editorial-post .wide{grid-column:full-start/full-end;width:100%;max-width:1100px;justify-self:center;margin:2em 0}
.wide img,.wide iframe{display:block;width:100%;border:0;border-radius:16px}.wide iframe{height:min(70vh,560px);background:var(--surface)}
.wide figcaption{margin-top:.7em;font:.8rem/1.5 var(--font-mono);color:var(--text-muted);text-align:center}.wide figcaption p{margin:0}
/* índice flotante */
.toc-fab{position:fixed;z-index:6;right:14px;bottom:84px}
.toc-fab>button{font:600 13px var(--font-body);color:var(--on-accent);background:var(--accent);border:0;border-radius:999px;padding:10px 16px;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.3)}
.toc-fab nav{position:absolute;right:0;bottom:calc(100% + 10px);width:min(320px,calc(100vw - 28px));max-height:60vh;overflow:auto;padding:14px 16px;border-radius:16px;background:var(--dock);border:1px solid var(--border);backdrop-filter:blur(10px);box-shadow:0 18px 40px rgba(0,0,0,.3)}
.toc-fab nav[hidden]{display:none}.toc-fab b{display:block;font:700 11px var(--font-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted);margin-bottom:6px}
.toc-fab a{display:block;padding:6px 0;color:var(--text);text-decoration:none;font-size:14px;border-bottom:1px dashed var(--border)}.toc-fab a.l3{padding-left:14px;font-size:13px;color:var(--text-muted)}.toc-fab a.on{color:var(--accent-text);font-weight:700}.toc-fab a:last-child{border:0}
.editorial-post .more-reading{grid-column:main-start/main-end;margin-top:2.4em}.more-reading h2{font-size:var(--step-2);margin-bottom:.6em}
@media (min-width:1080px){.editorial-post .more-reading{grid-column:main-start/margin-end}}
@media (max-width:640px){.editorial-post{font-size:min(var(--text-base),18px)}.toc-fab{bottom:78px}}"""

SITE_JS = """(function(){var D=document,R=D.documentElement;
var bar=D.getElementById('prog');if(bar){addEventListener('scroll',function(){var d=R,m=d.scrollHeight-innerHeight;bar.style.width=(m>0?scrollY/m*100:0)+'%'},{passive:true})}
/* modo claro / oscuro del lector */
[].forEach.call(D.querySelectorAll('[data-mode-toggle]'),function(b){b.addEventListener('click',function(){var m=R.dataset.mode==='dark'?'light':'dark';R.dataset.mode=m;try{localStorage.setItem('brisa-mode',m)}catch(e){}
b.setAttribute('aria-label',m==='dark'?'Cambiar a modo claro':'Cambiar a modo oscuro')})});
var mb=D.querySelector('[data-mode-toggle]');if(mb)mb.setAttribute('aria-label',R.dataset.mode==='dark'?'Cambiar a modo claro':'Cambiar a modo oscuro');
/* «Inicio» hacia la Landing: se desvanece y cambia de página en la misma pestaña */
D.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-landing]');if(!a||e.ctrlKey||e.metaKey||e.shiftKey||e.button)return;e.preventDefault();D.body.classList.add('leaving');setTimeout(function(){location.href=a.href},180)});
addEventListener('pageshow',function(){D.body.classList.remove('leaving')});
/* buscador y filtros del listado */
var q=D.getElementById('buscar'),chips=[].slice.call(D.querySelectorAll('.chip.f')),cards=[].slice.call(D.querySelectorAll('[data-cat]')),cat='';
function apply(){var t=q?q.value.toLowerCase():'';cards.forEach(function(c){var ok=(!cat||c.dataset.cat===cat)&&(!t||c.dataset.t.indexOf(t)>-1);c.style.display=ok?'':'none'})}
chips.forEach(function(b){b.addEventListener('click',function(){cat=b.dataset.c;chips.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});apply()})});if(q)q.addEventListener('input',apply);
D.addEventListener('keydown',function(e){var tg=D.activeElement.tagName;if(/INPUT|TEXTAREA/.test(tg)||e.ctrlKey||e.metaKey||e.altKey)return;
var c=cards.filter(function(x){return x.style.display!=='none'}),i=c.indexOf(D.activeElement);
if(e.key==='j'){e.preventDefault();(c[i+1]||c[0])&&(c[i+1]||c[0]).focus()}else if(e.key==='k'){e.preventDefault();(c[i-1]||c[c.length-1])&&(c[i-1]||c[c.length-1]).focus()}
else if(e.key==='/'&&q){e.preventDefault();q.focus()}else if(e.key==='h'){location.href=D.querySelector('.brand').href}else if(e.key==='t'&&mb){mb.click()}});
/* botón «Copiar» y resaltado ligero de código (sin librerías) */
var KW={python:'def class return if elif else for while in not and or import from as with try except finally raise lambda yield pass break continue None True False is async await',
javascript:'function const let var return if else for while of in new class extends import from export default async await try catch finally throw switch case break continue null true false this typeof',
sql:'select from where insert into values update set delete create table join left right inner on group by order limit having and or not null as distinct primary key foreign references',
bash:'if then else fi for do done while case esac function echo cd git pip npm sudo export',json:'true false null',html:'html head body div span a p ul li script style'};
KW.js=KW.javascript;KW.py=KW.python;KW.ts=KW.javascript;KW.typescript=KW.javascript;KW.sh=KW.bash;KW.shell=KW.bash;
function esc(s){return s.replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]})}
function hl(code,lang){var kw=(KW[lang]||'').split(' ').filter(Boolean),set={};kw.forEach(function(k){set[k]=1});
var re=/(#[^\\n]*|\\/\\/[^\\n]*|--[^\\n]*|\\/\\*[\\s\\S]*?\\*\\/)|("(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*'|`(?:\\\\.|[^`\\\\])*`)|(\\b\\d+(?:\\.\\d+)?\\b)|([A-Za-z_][A-Za-z_0-9]*)(\\s*\\()?|([\\s\\S])/g,out='',m;
var lineC=(lang==='python'||lang==='py'||lang==='bash'||lang==='sh'||lang==='shell');
while((m=re.exec(code))){if(m[1]){if(m[1][0]==='#'&&!lineC||(m[1].slice(0,2)==='--'&&lang!=='sql')){out+=esc(m[1])}else out+='<span class="tk-c">'+esc(m[1])+'</span>'}
else if(m[2])out+='<span class="tk-s">'+esc(m[2])+'</span>';else if(m[3])out+='<span class="tk-n">'+m[3]+'</span>';
else if(m[4]){var low=lang==='sql'?m[4].toLowerCase():m[4];out+=set[low]?'<span class="tk-k">'+esc(m[4])+'</span>':m[5]?'<span class="tk-f">'+esc(m[4])+'</span>'+esc(m[5]):esc(m[4])}else out+=esc(m[6])}return out}
[].forEach.call(D.querySelectorAll('.codeblock code'),function(c){var l=((c.className.match(/language-(\\S+)/)||[])[1]||'');if(l&&l!=='text')c.innerHTML=hl(c.textContent,l)});
D.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-copy]');if(!b)return;var pre=b.closest('.codeblock').querySelector('code'),txt=pre.textContent;
function ok(){b.textContent='¡Copiado!';b.classList.add('ok');setTimeout(function(){b.textContent='Copiar';b.classList.remove('ok')},1600)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(ok,function(){fb()})}else fb();
function fb(){var t=D.createElement('textarea');t.value=txt;t.style.position='fixed';t.style.opacity='0';D.body.appendChild(t);t.select();try{D.execCommand('copy');ok()}catch(x){}t.remove()}});
/* índice flotante: abre/cierra y marca la sección que lees */
var fab=D.querySelector('.toc-fab');if(fab){var btn=fab.querySelector('button'),nav=fab.querySelector('nav');
function tog(open){nav.hidden=!open;btn.setAttribute('aria-expanded',open?'true':'false')}
btn.addEventListener('click',function(){tog(nav.hidden)});nav.addEventListener('click',function(e){if(e.target.closest('a'))tog(false)});
D.addEventListener('keydown',function(e){if(e.key==='Escape'&&!nav.hidden){tog(false);btn.focus()}});
var links=[].slice.call(nav.querySelectorAll('a')),heads=links.map(function(a){return D.getElementById(a.getAttribute('href').slice(1))});
addEventListener('scroll',function(){var cur=0;heads.forEach(function(h,i){if(h&&h.getBoundingClientRect().top<innerHeight*.35)cur=i});links.forEach(function(a,i){a.classList.toggle('on',i===cur)})},{passive:true})}
})();"""
