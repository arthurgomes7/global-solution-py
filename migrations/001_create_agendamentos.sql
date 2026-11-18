-- 001: cria a tabela de agendamentos de queima prescrita
CREATE TABLE IF NOT EXISTS agendamentos (
    id                 SERIAL PRIMARY KEY,
    solicitante        VARCHAR(150)     NOT NULL,
    endereco           VARCHAR(255)     NOT NULL,
    area_hectares      DOUBLE PRECISION NOT NULL CHECK (area_hectares > 0),
    data_prevista      DATE             NOT NULL,
    descricao          TEXT,
    analise_brigadista VARCHAR(20)      NOT NULL DEFAULT 'em_analise'
        CHECK (analise_brigadista IN ('em_analise', 'aceita', 'recusada')),
    criado_em          TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP
);
