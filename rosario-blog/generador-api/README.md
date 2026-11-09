# Generador API

Convierte el contenido que le manda el CMS en el **sitio estático** del blog (HTML + `api/posts.json`) y lo sirve en `/site/`. Puerto 8013.
Capas: `generador/controllers` → `services` → `repository` → `models`.

## Arrancar
```bash
python -m venv .venv && .venv\Scripts\activate      # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn generador.main:create_app --factory --port 8013
```
Documentación: http://localhost:8013/docs · Sitio generado: http://localhost:8013/site/

## Cómo trabaja
1. El CMS llama `POST /api/v1/builds` con `{reason, bundle}` (token de servicio con permiso `builds:write`) → responde **202**.
2. El generador compila en segundo plano, **una a la vez** (si ya hay una en espera, no crea otra: coalescencia).
3. Pasos: extraer el contenido publicado → renderizar todas las páginas en memoria → escribir los archivos. Si algo falla antes de escribir, el sitio anterior queda intacto.
4. Cada página lleva el script de visitas, que envía los eventos a la API de métricas (`METRICS_URL`).

## Rutas (`/api/v1/builds`)
`POST` pedir compilación (`builds:write`) · `GET` listar · `GET /latest` · `GET /{id}` (`builds:read`).
Pruebas: `pytest`.
