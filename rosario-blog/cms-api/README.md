# CMS API

CMS (API) para administrar un blog: usuarios, blogs, páginas, publicaciones, categorías, imágenes y builds.
Python + FastAPI + SQLAlchemy. Arquitectura en 4 capas: controllers → services → repository → models.

## Arrancar
```bash
python -m venv .venv && .venv/Scripts/activate     # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Abre http://localhost:8000/docs → `POST /api/auth/login` (admin@example.com / admin123) → botón **Authorize** con el token.
Base de datos: SQLite por defecto (archivo `cms.db`). PostgreSQL: `docker compose up -d` y `DATABASE_URL` en `.env`.

## Qué hay dentro
| Carpeta / archivo | Para qué sirve |
|---|---|
| `app/controllers/` | Reciben la petición HTTP y llaman al servicio. |
| `app/services/` | Reglas de negocio (el blog es de su dueña, slug único, fecha de publicación…). |
| `app/repository/` | Lee y escribe en la base de datos. |
| `app/models/` | `entities.py` = tablas; `schemas.py` = JSON de entrada/salida. |
| `app/main.py` | Arranca la API, crea tablas y el administrador. |
| `app/dependencies.py` | Arma repositorios y servicios y los entrega a los controllers. |
| `tests/` | Pruebas del flujo completo y de que las capas se respeten (`pytest`). |

## ¿Por qué se "conecta" con otras APIs?
El CMS **sólo administra contenido**: no genera el sitio ni cuenta visitas. Eso lo hacen otros servicios, y el CMS les habla por HTTP:
- **Generador (Builder):** `POST /api/build` → el CMS lee de la BD lo publicado y se lo envía (`BUILDER_URL`). El generador crea las páginas que ve el visitante.
- **Métricas:** `GET /api/blogs/{id}/metrics` → el CMS le pregunta las visitas a la API de métricas (`METRICS_URL`).

Así cada servicio hace una sola cosa y se puede cambiar sin tocar los demás (la idea de "servicios vecinos" del profe).
Si `BUILDER_URL` / `METRICS_URL` están vacías, el CMS **simula** esas respuestas, por eso funciona solo.
Para que se entiendan, todas las APIs deben usar la misma `SECRET_KEY` (el token que firma una lo acepta la otra).
