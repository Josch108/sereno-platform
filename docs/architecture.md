# Arquitectura de Sereno

Sereno convierte el comportamiento digital de un adolescente en un **puntaje de
riesgo de estrés (SRS)** que padres y orientadores escolares pueden entender y
sobre el que pueden actuar a tiempo — sin espiar ni castigar.

## Las 4 capas

```
┌──────────────────────────────────────────────────────────────────┐
│  1. RECOLECCIÓN        Cuestionario corto (plataformas, uso,       │
│                        inquietud, preocupación, sueño)             │
│                        → tablas: users, consents, responses        │
├──────────────────────────────────────────────────────────────────┤
│  2. PROCESAMIENTO      Limpieza y construcción de variables        │
│                        derivadas (api/scoring.py + scripts/)       │
├──────────────────────────────────────────────────────────────────┤
│  3. PREDICCIÓN         Modelo → puntaje de riesgo de estrés (SRS)  │
│                        Esqueleto: heurística transparente.         │
│                        Producción: regresión logística / RF        │
│                        entrenada con el dataset SMMH (Kaggle).     │
│                        → tabla: risk_scores                         │
├──────────────────────────────────────────────────────────────────┤
│  4. ALERTAS            Semáforo de 3 niveles + guías de            │
│                        conversación SIN culpa                      │
│                        → tabla: alerts                              │
└──────────────────────────────────────────────────────────────────┘
```

## Semáforo de riesgo (según uso nocturno)

| Nivel       | Uso nocturno     | Acción                                   |
|-------------|------------------|------------------------------------------|
| 🟢 Verde    | < 30 min         | Sin alarma. Refuerzo positivo.           |
| 🟡 Amarillo | 30 – 60 min      | Aviso informativo, sin alarma.           |
| 🔴 Rojo     | > 60 min         | Alerta + guías de conversación familiar. |

## Modelo de datos

Seis tablas (ver [`database/schema.sql`](../database/schema.sql)):

- **users** — adolescentes y tutores, con identificador anónimo.
- **consents** — doble consentimiento (adolescente + tutor).
- **questionnaires** — cuestionario versionado.
- **responses** — respuestas, alineadas con las variables del dataset SMMH.
- **risk_scores** — puntaje SRS y versión del modelo que lo generó.
- **alerts** — mensajes de retroalimentación por nivel de semáforo.

## Decisiones de diseño

- **SQLite en el esqueleto, PostgreSQL en producción.** El esqueleto corre y se
  despliega sin un servidor de base de datos; el esquema lógico es idéntico.
- **Capa de scoring aislada** (`api/scoring.py`). El día que el modelo de ML esté
  entrenado solo se reemplaza esa función, sin tocar la API.
- **Ética por diseño:** doble consentimiento, minimización de datos (nunca se
  guarda contenido, solo métricas de uso) y trazabilidad de la versión del
  modelo en cada puntaje.
