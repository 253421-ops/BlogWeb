# Rosario Blog — CMS + Métricas + Generador

Tres APIs separadas que se conectan entre sí, cada una con sus 4 capas (controllers → services → repository → models) y su base SQL:

| Carpeta | Qué hace | Puerto | Arranque |
|---|---|---|---|
| `cms-api/` | **CMS**: blogs, posts, páginas, categorías, imágenes, builds. Es la guía de tu amigo, hecha tuya. | 8000 | `uvicorn app.main:app --reload` |
| `metricas-api/` | **Métricas**: recibe y cuenta las visitas. | 8012 | `uvicorn metricas.main:create_app --factory --port 8012` |
| `generador-api/` | **Generador**: convierte lo publicado en el sitio del blog y lo sirve. | 8013 | `uvicorn generador.main:create_app --factory --port 8013` |

## Cómo se conectan
```
Tú ──(Bearer JWT)──▶ CMS ──POST /api/v1/builds {bundle}──▶ Generador ──▶ sitio en :8013/site/
                      │                                          
                      └──GET /api/v1/metrics/overview──▶ Métricas ◀──POST /api/v1/events── el sitio (script de visitas)
```
- `POST /api/build` en el CMS → el CMS manda lo publicado al generador (`BUILDER_URL`).
- `GET /api/blogs/{id}/metrics` en el CMS → el CMS pregunta las visitas a métricas (`METRICS_URL`).
- Cada página generada manda sus visitas a métricas (`METRICS_URL` del generador).
- Las tres usan la **misma clave secreta** (`SECRET_KEY` en el CMS, `JWT_SECRET` en las otras; en desarrollo ya coinciden).

## Pasos (TRES terminales en VS Code; el "+" abre otra)
En cada una: entra a la carpeta, crea el entorno e instala.
```
cd metricas-api      (terminal 1)           cd generador-api     (terminal 2)           cd cms-api     (terminal 3)
python -m venv .venv                         python -m venv .venv                       python -m venv .venv
.venv\Scripts\activate                       .venv\Scripts\activate                     .venv\Scripts\activate
pip install -r requirements.txt              pip install -r requirements.txt            pip install -r requirements.txt
uvicorn metricas.main:create_app --factory --port 8012
                                             uvicorn generador.main:create_app --factory --port 8013
                                                                                        uvicorn app.main:app --reload
```
**Prueba completa** en http://localhost:8000/docs: `POST /api/auth/login` (`admin@example.com` / `admin123`) → **Authorize** →
`POST /api/blogs` → `POST /api/blogs/1/posts` con `"status": "published"` → `POST /api/build` con `{"blogId": 1}` →
abre http://localhost:8013/site/ (tu blog generado) → entra a un post → `GET /api/blogs/1/metrics` muestra la visita.

## Desplegar
GitHub **guarda** el código; no lo ejecuta. Para publicarlo se usa un host:
1. Sube todo a GitHub (`git add .`, `git commit`, `git push`).
2. En **Render** (o Railway) crea **un servicio web por carpeta** (`cms-api`, `metricas-api`, `generador-api`): *Root Directory* = la carpeta, *Build* `pip install -r requirements.txt`, *Start* el comando de la tabla con `--host 0.0.0.0 --port $PORT`.
3. Variables de entorno en cada servicio: `JWT_SECRET` (CMS: `SECRET_KEY`) **igual en los tres**, 32+ caracteres; en el CMS `ADMIN_PASSWORD`, `BUILDER_URL`, `METRICS_URL` y `DATABASE_URL`; en el generador `METRICS_URL`; en métricas `CORS_ORIGINS` con la dirección pública del generador.
4. Usa PostgreSQL (la base gratuita de Render) en `DATABASE_URL`: el disco de estos servicios se borra al reiniciar, y SQLite se perdería. El sitio generado también vive en disco: tras un reinicio se vuelve a generar con `POST /api/build`.
5. HTTPS lo pone la plataforma automáticamente.
Vercel sirve bien páginas estáticas, pero no estas APIs.

## Pruebas
`pytest` dentro de cada carpeta (cms-api: 6 · metricas-api: 1 · generador-api: 1).
