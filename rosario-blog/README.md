# Rosario Blog — CMS + Generador + Métricas

Tu blog tiene **tres servicios** que se hablan entre sí, y una **Landing** aparte en Vercel.

| Pieza | Qué hace | Dónde vive |
|---|---|---|
| **Landing** (repo aparte) | Tu portada personal. «Mi Blog» lleva al blog. | Vercel |
| `cms-api/` | **Panel** donde escribes, personalizas y publicas. | Render · `/app/` |
| `generador-api/` | Convierte lo publicado en el sitio del blog y lo sirve. | Render · `/site/blog/` |
| `metricas-api/` | Cuenta visitas sin cookies. | Render |

---

## ⚡ Guía de uso en 60 segundos

### 1 · Escribir
1. Entra al panel y pulsa **`n`** (o «+ Nueva entrada»).
2. Pon un **título** y escribe en la caja grande. A la derecha ves la **vista previa** en vivo.
3. ¿Quieres algo de revista (nota al margen, cita, caja, código)? Pulsa **`/`** al inicio de una línea o el botón **＋ Bloque editorial**. Eliges de una lista; no hay que memorizar nada.
4. Todo lo demás (dirección, resumen, categoría, portada, borrador/publicado) está en **⚙ Más opciones**. El editor se queda limpio.

### 2 · Personalizar
Pulsa **`g`** y luego **`a`** (o menú *Plantillas → Diseño del sitio*). Se abre una ventana con cuatro bloques:

| Bloque | Qué eliges |
|---|---|
| **Modo de color** | Interruptor sol / luna: cómo verá el sitio tu lector al llegar (él puede cambiarlo con el botón ☀/☾). |
| **Escena y atmósfera** | Oscuro: *Noche estrellada*, *Atardecer*, *Amanecer*. Claro: *Papel editorial*, *Lienzo pastel*, *Menta botánico*. Más un color de acento. |
| **Tipografía** (tres selectores separados) | **Títulos**, **Lectura** y **Código y etiquetas**. No se mezclan. |
| **Escala de tamaño** | *Compacta* (16 px · 1.20) · *Editorial estándar* (18 px · 1.25, recomendada) · *Lectura amplia* (20 px · 1.333). |

El CMS cuida que el texto siempre se lea bien: contraste mínimo **WCAG AA (4,5:1)** entre fondo y texto, aunque elijas un acento difícil.

### 3 · Publicar
Pulsa **`Ctrl + Enter`** o el botón **✦ Publicar sitio**. *Guardar* no publica: el sitio cambia sólo cuando publicas.
La primera vez del día puede tardar hasta **1 minuto** (el plan gratuito de Render duerme el servicio). El panel ya lo despierta solo.

> ❓ En cualquier momento pulsa **`?`**: guía de 3 pasos con ejemplos de bloques que se **copian con un clic** (o se insertan donde está el cursor).

---

## 🧱 Bloques editoriales (cómo se escriben)

| Bloque | Lo que escribes |
|---|---|
| Nota al margen | `Una idea[^nota: texto de la nota] en medio.` |
| Cita destacada | `>> Una frase de impacto.` |
| Caja de concepto | `:::info Título`⏎texto⏎`:::` (también `:::tip` y `:::warning`) |
| Código | ```` ```python ```` ⏎ código ⏎ ```` ``` ```` (etiqueta del lenguaje + botón **Copiar**) |
| Contenedor ancho | `:::wide`⏎`![descripción](url)`⏎pie de foto⏎`:::` — o una imagen sola: `![pie de foto](url#wide)`. En `:::wide` también vale una línea `iframe: https://…` para una visualización interactiva. |

Los títulos `##` y `###` arman el **índice flotante** («☰ Índice») y hay una **barra de progreso** de lectura. En pantallas grandes las notas viven en la columna derecha; en el móvil se despliegan dentro del texto.

---

## ⌨️ Atajos de teclado

Los atajos de una sola tecla se apagan solos cuando escribes en un campo (salvo los de `Ctrl/Cmd` y `Esc`).

**Navegación**

| Atajo | Acción |
|---|---|
| `n` | Nueva entrada |
| `g` `d` (o `g` `e`) | Documentos / Entradas |
| `g` `p` | Páginas |
| `g` `a` | Diseño y apariencia (ventana) |
| `g` `m` (o `g` `r`) | Métricas y rendimiento |
| `t` | Alternar modo claro / oscuro **del panel** |
| `?` | Guía rápida y atajos |
| `Ctrl/Cmd` `K` | Buscar cualquier acción (fuera del editor) |
| `j` / `k`, `Enter` o `e`, `d`, `/` | Mover por la lista, editar, borrar con deshacer, buscar |
| `Esc` | Cierra la ventana abierta o vuelve atrás |

**Editor**

| Atajo | Acción |
|---|---|
| `Ctrl/Cmd` `S` | Guardar borrador |
| `Ctrl/Cmd` `Enter` | Guardar y publicar el sitio |
| `Ctrl/Cmd` `B` · `I` · `K` | Negritas · cursivas · enlace |
| `Ctrl` `Shift` `C` | Bloque de código (eliges el lenguaje) |
| `Ctrl` `Shift` `M` | Nota al margen |
| `Ctrl` `Shift` `Q` | Cita destacada |
| `Ctrl/Cmd` `P` | Vista previa dividida / completa |
| `/` al inicio de línea | Menú rápido de bloques |

> Algunos navegadores reservan `Ctrl+Shift+C` y `Ctrl+Shift+M` para sus herramientas de desarrollo. Si no responden, usa los botones de la barra del editor o `/`.

---

## 🏗️ Arquitectura

Cada API tiene 4 capas (controllers → services → repository → models) y su base SQL.

```
Landing (Vercel) ──«Mi Blog»──▶ Blog generado (/site/blog/) ◀──«Inicio» / logotipo (LANDING_URL)
       │ GET /api/blogs/{id}/posts · /pages                         ▲
       ▼                                                            │
Tú ──(Bearer JWT)──▶ CMS ──GET /health (warm-up) + POST /api/v1/builds {bundle}──▶ Generador ──▶ sitio estático
                      │                                                                │
                      └──GET /api/v1/metrics/overview──▶ Métricas ◀──POST /api/v1/events── el sitio (script de visitas)
```

- `POST /api/build` en el CMS manda lo publicado al generador (`BUILDER_URL`). **Antes** hace un *warm-up*: `GET /health` hasta 3 veces, con 10 s entre intentos, y el envío espera hasta 120 s. Así no hay `502 Bad Gateway` cuando Render despierta el servicio.
- El **tema** (`mode`, `scene`, `accent`, `fontHead`, `fontBody`, `fontMono`, `fontScale`, `blog`) se guarda como una página en borrador (`tema-visual`); el CMS lo convierte en variables CSS (`--bg`, `--surface`, `--text`, `--text-muted`, `--accent`, `--border`, `--font-head`, `--font-body`, `--font-mono`, `--text-base`, `--scale-ratio`, …) con **dos paletas** (la del modo elegido y la contraria) para que el lector pueda alternar sin pedir nada al servidor. El tema de la versión anterior (`font: manuscrita|clasica|moderna`) se sigue entendiendo.
- El generador sólo acepta de ese CSS variables validadas; nunca copia CSS libre.
- Las tres APIs usan la **misma clave secreta** (`SECRET_KEY` en el CMS, `JWT_SECRET` en las otras).

### Variables de entorno

| Servicio | Variable | Para qué |
|---|---|---|
| todas | `JWT_SECRET` (CMS: `SECRET_KEY`) | La **misma**, 32+ caracteres |
| cms | `ADMIN_PASSWORD`, `BUILDER_URL`, `METRICS_URL`, `DATABASE_URL` | Contraseña, dirección del generador y de métricas, PostgreSQL |
| generador | `METRICS_URL` | Adónde mandan visitas las páginas |
| generador | **`LANDING_URL`** | Dirección de tu Landing en Vercel. El botón **Inicio** y el logotipo del blog van allí (misma pestaña, con transición suave). Si no existe, apuntan a la portada del propio blog. |
| metricas | `CORS_ORIGINS` | Dirección pública del generador |

---

## 🧪 Probar en tu computadora (VS Code)

Tres terminales (el «+» abre otra). En cada una: entra a la carpeta, crea el entorno e instala.

```
cd metricas-api      (terminal 1)           cd generador-api     (terminal 2)           cd cms-api     (terminal 3)
python -m venv .venv                         python -m venv .venv                       python -m venv .venv
.venv\Scripts\activate                       .venv\Scripts\activate                     .venv\Scripts\activate
pip install -r requirements.txt              pip install -r requirements.txt            pip install -r requirements.txt
uvicorn metricas.main:create_app --factory --port 8012
                                             uvicorn generador.main:create_app --factory --port 8013
                                                                                        uvicorn app.main:app --reload
```

Abre **http://localhost:8000/app/** (`admin@example.com` / `admin123` en desarrollo), crea tu blog, escribe y pulsa **Publicar sitio**. Tu blog sale en http://localhost:8013/site/blog/.
La documentación de la API está en http://localhost:8000/docs.

### Pruebas

Se corren **dentro de cada carpeta** (cada API tiene su propio paquete):

```
cd cms-api && pytest            # 10 pruebas
cd generador-api && pytest      # 5 pruebas
cd metricas-api && pytest       # 1 prueba
```

> No sirve `pytest cms-api/tests generador-api/tests` desde la raíz: las dos APIs tienen módulos con el mismo nombre (`app`, `common`) y Python los confunde.

---

## 🚀 Desplegar: VS Code → GitHub → Render

GitHub **guarda** el código; Render lo **ejecuta**. Con el *Auto-Deploy* activado, cada `git push` a `main` despliega los tres servicios.

```
cd rosario-blog
git status
git add .
git commit -m "feat: rediseño editorial, modales del CMS, modo claro/oscuro, atajos y fix 502"
git branch -M main
git push -u origin main
```

Luego, en Render:
1. Un servicio web por carpeta (`cms-api`, `generador-api`, `metricas-api`): *Root Directory* = la carpeta, *Build* `pip install -r requirements.txt`, *Start* el comando de la tabla de arriba con `--host 0.0.0.0 --port $PORT`.
2. En **generador → Environment** agrega `LANDING_URL` = la dirección de tu Landing en Vercel.
3. Usa PostgreSQL (la base gratuita de Render) en `DATABASE_URL`: el disco de estos servicios se borra al reiniciar. El generador vuelve a armar el sitio solo al arrancar, con el último contenido guardado.
4. HTTPS lo pone la plataforma. Vercel sirve páginas estáticas, pero no estas APIs.

### Si algo no responde (Render duerme los servicios gratuitos)

Abre estas tres direcciones y espera hasta ~50 s la primera vez:

| Servicio | Dirección de comprobación |
|---|---|
| cms | `https://cms-fmzc.onrender.com/api/health` |
| generador | `https://generador-3jpz.onrender.com/health` |
| metricas | `https://metricas-doxd.onrender.com/health` |

Cuando las tres digan `ok`, vuelve al panel y publica. Más detalle en el PDF `Guia_Uso_Ecosistema_Brisa.pdf`.
