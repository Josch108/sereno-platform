-- =============================================================================
--  SERENO · Datos semilla mínimos
-- =============================================================================
--  Inserta el catálogo base para que la API arranque con un cuestionario activo.
--  Los datos de respuestas/puntajes de ejemplo se cargan con los scripts de
--  Python (ver scripts/generate_data.py y scripts/load_data.py).
-- =============================================================================

INSERT INTO questionnaires (version, title, is_active) VALUES
    ('v1.0', 'Cuestionario Sereno de hábitos digitales y bienestar', TRUE);

-- Usuario tutor de ejemplo
INSERT INTO users (external_uid, role, age, gender) VALUES
    ('guardian-0001', 'guardian', 41, 'F');

-- Adolescente de ejemplo enlazado al tutor anterior
INSERT INTO users (external_uid, role, age, gender, guardian_id) VALUES
    ('teen-0001', 'adolescent', 15, 'M', 1);

-- Doble consentimiento otorgado
INSERT INTO consents (user_id, consent_type, granted, granted_at) VALUES
    (2, 'self',     TRUE, NOW()),
    (1, 'guardian', TRUE, NOW());
