# Métricas API

API que **recibe y cuenta las visitas** del blog. Es un servicio aparte del CMS (puerto 8012).
Capas: `metricas/controllers` → `services` → `repository` → `models`.

## Arrancar
```bash
python -m venv .venv && .venv\Scripts\activate      # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn metricas.main:create_app --factory --port 8012
```
Documentación: http://localhost:8012/docs

## Rutas (`/api/v1`)
| Ruta | Quién la usa | Token |
|---|---|---|
| `POST /events` | el script del sitio publicado (cada visita manda un evento) | no |
| `GET /metrics/overview` | el CMS y la consola: vistas, visitantes únicos, rebote… | sí, permiso `metrics:read` |
| `GET /metrics/pages` | páginas más vistas | sí |
| `GET /metrics/timeseries` | vistas por día | sí |

Pruebas: `pytest`.
