-- =============================================================================
--  SERENO · Esquema de base de datos (PostgreSQL)
-- =============================================================================
--  Plataforma de detección temprana de riesgo de estrés en adolescentes a
--  partir de su comportamiento en redes sociales.
--
--  Modelo de 4 capas:
--    1. Recolección  -> cuestionarios y respuestas
--    2. Procesamiento-> variables derivadas
--    3. Predicción   -> puntaje de riesgo de estrés (SRS)
--    4. Alertas      -> semáforo verde / amarillo / rojo + retroalimentación
--
--  Principios éticos reflejados en el esquema:
--    - Doble consentimiento (adolescente + tutor)  -> tabla `consents`
--    - Minimización de datos (no se guarda contenido, solo métricas de uso)
--    - Trazabilidad de la versión del modelo que generó cada puntaje
-- =============================================================================

-- Para reejecutar el script desde cero en un entorno de desarrollo:
DROP TABLE IF EXISTS alerts             CASCADE;
DROP TABLE IF EXISTS risk_scores        CASCADE;
DROP TABLE IF EXISTS responses          CASCADE;
DROP TABLE IF EXISTS questionnaires     CASCADE;
DROP TABLE IF EXISTS consents           CASCADE;
DROP TABLE IF EXISTS users              CASCADE;

-- -----------------------------------------------------------------------------
-- 1. USUARIOS
--    Adolescentes y tutores. No se almacenan datos sensibles de contenido.
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    external_uid  VARCHAR(40)  NOT NULL UNIQUE,           -- identificador anónimo
    role          VARCHAR(20)  NOT NULL                   -- 'adolescent' | 'guardian'
                  CHECK (role IN ('adolescent', 'guardian')),
    age           SMALLINT     CHECK (age BETWEEN 10 AND 25),
    gender        VARCHAR(20),
    guardian_id   INTEGER REFERENCES users (id),          -- enlace adolescente -> tutor
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 2. CONSENTIMIENTOS (doble consentimiento)
--    El cuestionario solo se habilita si existen los dos consentimientos.
-- -----------------------------------------------------------------------------
CREATE TABLE consents (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    consent_type   VARCHAR(20) NOT NULL                   -- 'self' | 'guardian'
                   CHECK (consent_type IN ('self', 'guardian')),
    granted        BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at     TIMESTAMP,
    UNIQUE (user_id, consent_type)
);

-- -----------------------------------------------------------------------------
-- 3. CUESTIONARIOS
--    Versionado: cada despliegue del cuestionario tiene su propia versión.
-- -----------------------------------------------------------------------------
CREATE TABLE questionnaires (
    id          SERIAL PRIMARY KEY,
    version     VARCHAR(10) NOT NULL UNIQUE,              -- p. ej. 'v1.0'
    title       VARCHAR(120) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. RESPUESTAS
--    Una fila = un cuestionario contestado. Las columnas se alinean con las
--    variables del dataset público de Kaggle "Social Media and Mental Health"
--    (SMMH) con el que se entrena el modelo.
-- -----------------------------------------------------------------------------
CREATE TABLE responses (
    id                    SERIAL PRIMARY KEY,
    user_id               INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    questionnaire_id      INTEGER NOT NULL REFERENCES questionnaires (id),

    -- Plataformas y uso
    platforms             VARCHAR(200),                   -- 'TikTok,Instagram'
    daily_usage_minutes   SMALLINT  CHECK (daily_usage_minutes >= 0),
    nocturnal_usage_min   SMALLINT  CHECK (nocturnal_usage_min >= 0),
    last_session_hour     SMALLINT  CHECK (last_session_hour BETWEEN 0 AND 23),

    -- Variables psicológicas (escala 1-5, estilo SMMH)
    restlessness          SMALLINT  CHECK (restlessness  BETWEEN 1 AND 5),
    worry                 SMALLINT  CHECK (worry         BETWEEN 1 AND 5),
    distraction           SMALLINT  CHECK (distraction   BETWEEN 1 AND 5),
    sleep_problems        SMALLINT  CHECK (sleep_problems BETWEEN 1 AND 5),

    submitted_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 5. PUNTAJES DE RIESGO (Stress Risk Score)
--    Resultado de la capa predictiva. Se guarda la versión del modelo para
--    poder reproducir y auditar cada puntaje.
-- -----------------------------------------------------------------------------
CREATE TABLE risk_scores (
    id             SERIAL PRIMARY KEY,
    response_id    INTEGER NOT NULL REFERENCES responses (id) ON DELETE CASCADE,
    srs            NUMERIC(5,2) NOT NULL                  -- 0.00 - 100.00
                   CHECK (srs BETWEEN 0 AND 100),
    risk_level     VARCHAR(10) NOT NULL                   -- 'green' | 'yellow' | 'red'
                   CHECK (risk_level IN ('green', 'yellow', 'red')),
    model_version  VARCHAR(20) NOT NULL,                  -- p. ej. 'logreg-1.0'
    computed_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 6. ALERTAS
--    Capa de retroalimentación. Las alertas NO castigan: entregan guías de
--    conversación según el nivel de riesgo.
-- -----------------------------------------------------------------------------
CREATE TABLE alerts (
    id            SERIAL PRIMARY KEY,
    risk_score_id INTEGER NOT NULL REFERENCES risk_scores (id) ON DELETE CASCADE,
    level         VARCHAR(10) NOT NULL
                  CHECK (level IN ('green', 'yellow', 'red')),
    message       TEXT NOT NULL,
    acknowledged  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Índices para las consultas más frecuentes
-- -----------------------------------------------------------------------------
CREATE INDEX idx_responses_user        ON responses (user_id);
CREATE INDEX idx_risk_scores_response  ON risk_scores (response_id);
CREATE INDEX idx_alerts_risk_score     ON alerts (risk_score_id);
CREATE INDEX idx_users_guardian        ON users (guardian_id);
