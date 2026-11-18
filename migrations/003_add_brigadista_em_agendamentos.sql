-- 003: liga cada agendamento ao brigadista que o analisou (relacionamento N:1)
-- Fica nulo enquanto a solicitação está "em_analise".
ALTER TABLE agendamentos
    ADD COLUMN IF NOT EXISTS brigadista_id INTEGER REFERENCES brigadistas (id);

CREATE INDEX IF NOT EXISTS idx_agendamentos_brigadista ON agendamentos (brigadista_id);
