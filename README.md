# 🌙 Sereno — Plataforma de detección temprana de estrés

> Proyecto #06 · Unidad 2 — Diseño de la plataforma y repositorio

Sereno convierte el comportamiento digital de un adolescente en un **puntaje de
riesgo de estrés (SRS)** que padres y orientadores escolares pueden entender y
sobre el que pueden actuar a tiempo — **sin espiar ni castigar**. A partir de un
cuestionario corto, un modelo asigna un puntaje y muestra un **semáforo de 3
niveles** con guías de conversación.

Este repositorio contiene el **esqueleto desplegable** de la plataforma: esquema
de base de datos, estructura de la API, scripts de generación de datos y
archivos de datos de ejemplo (CSV, JSON, Excel).

---

## 🧱 Estructura del proyecto

```
sereno-platform/
├── api/                      # Capa de servicio (FastAPI)
│   ├── main.py               #   Endpoints: /health, /responses
│   ├── models.py             #   Esquemas de entrada/salida (Pydantic)
│   ├── scoring.py            #   Capa predictiva: puntaje de riesgo (SRS)
│   └── database.py           #   Conexión a base de datos (SQLite local)
├── database/
│   ├── schema.sql            # Esquema completo (PostgreSQL, 6 tablas)
│   └── seed.sql              # Datos catálogo mínimos
├── scripts/
│   ├── generate_data.py      # Genera datos de ejemplo -> CSV / JSON / XLSX
│   └── load_data.py          # Carga los datos a la base local
├── data/                     # Datos de ejemplo generados
│   ├── sample_responses.csv
│   ├── sample_responses.json
│   └── sample_responses.xlsx
├── tests/
│   └── test_api.py           # Pruebas del scoring y de la API
├── docs/
│   └── architecture.md       # Arquitectura de 4 capas
├── .github/workflows/ci.yml  # Integración continua (build + test + health)
└── requirements.txt
```

La arquitectura completa está documentada en
[`docs/architecture.md`](docs/architecture.md).

---

## 🗄️ Infraestructura de datos

El modelo de datos tiene **6 tablas** (ver [`database/schema.sql`](database/schema.sql)):

| Tabla            | Para qué sirve                                            |
|------------------|-----------------------------------------------------------|
| `users`          | Adolescentes y tutores (identificador anónimo).           |
| `consents`       | Doble consentimiento (adolescente + tutor).               |
| `questionnaires` | Cuestionario versionado.                                  |
| `responses`      | Respuestas, alineadas con el dataset SMMH de Kaggle.      |
| `risk_scores`    | Puntaje de riesgo de estrés y versión del modelo.         |
| `alerts`         | Mensajes de retroalimentación por nivel de semáforo.      |

> **Nota técnica:** el esqueleto usa **SQLite** para poder ejecutarse y
> desplegarse sin un servidor de base de datos. El esquema lógico es idéntico al
> de PostgreSQL en `database/schema.sql`.

---

## ▶️ Cómo ejecutarlo en local

Requisitos: **Python 3.12+**.

```bash
# 1. Clonar el repositorio
git clone <URL-del-repo>
cd sereno-platform

# 2. (Opcional) crear un entorno virtual
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Generar los datos de ejemplo (CSV, JSON, Excel)
python scripts/generate_data.py --n 200

# 5. Cargar los datos a la base local
python scripts/load_data.py

# 6. Levantar la API
uvicorn api.main:app --reload
```

Luego abre la documentación interactiva en **http://localhost:8000/docs**.

### Probar la API rápido

```bash
# Salud del servicio
curl http://localhost:8000/health

# Enviar un cuestionario y obtener el puntaje + alerta
curl -X POST http://localhost:8000/responses \
  -H "Content-Type: application/json" \
  -d '{"external_uid":"teen-0001","platforms":"TikTok,Instagram",
       "daily_usage_minutes":300,"nocturnal_usage_min":85,"last_session_hour":1,
       "restlessness":4,"worry":4,"distraction":3,"sleep_problems":5}'
```

### Correr las pruebas

```bash
pytest -q
```

---

## 🚦 Cómo funciona el puntaje

El semáforo se calibra con la literatura sobre uso nocturno de pantallas:

| Nivel       | Uso nocturno | Acción                                   |
|-------------|--------------|------------------------------------------|
| 🟢 Verde    | < 30 min     | Sin alarma. Refuerzo positivo.           |
| 🟡 Amarillo | 30 – 60 min  | Aviso informativo.                       |
| 🔴 Rojo     | > 60 min     | Alerta + guías de conversación familiar. |

El puntaje no es solo un contador de minutos: combina el uso nocturno, la
**dominancia de plataforma** (TikTok pesa más por su algoritmo de recompensa
variable) y señales psicológicas (inquietud, preocupación, distracción, sueño).
La lógica vive aislada en [`api/scoring.py`](api/scoring.py) para poder
reemplazarla por el modelo de ML entrenado sin tocar el resto de la API.

---

## 👥 Equipo y roles

| Integrante | Rol | GitHub |
|------------|-----|--------|
| _[Joel Perez]_ | Datos y modelo (limpieza, análisis, scoring) | _[JOELPEREZ119]_ |
| _[Josue Chan]_ | Backend y API (FastAPI, base de datos) | _[@Josch108]_ |
| _[Joel Perez]_ | Frontend / App y documentación | _[JOELPEREZ119]_ |


### Cómo agregar tu commit

```bash
git clone <URL-del-repo>
cd sereno-platform
# haz un cambio pequeño (p. ej. tu nombre en la tabla de arriba)
git add README.md
git commit -m "docs: agrega a <tu nombre> al equipo"
git push
```

---

## 🔄 Despliegue (GitHub Actions)

El flujo de [`.github/workflows/ci.yml`](.github/workflows/ci.yml) se ejecuta en
cada `push` a `main`: instala dependencias, genera datos, corre las pruebas y
verifica que la API arranque (`/health`). El profesor revisa y despliega desde
ahí.

---

## 🔒 Ética y privacidad

- **Doble consentimiento:** la app no se activa con permiso unilateral.
- **Minimización de datos:** nunca se guarda contenido, solo métricas de uso.
- **No es diagnóstico médico:** es una herramienta de **detección temprana**.
