-- 002: cria a tabela de brigadistas, responsáveis por analisar as solicitações de queima
CREATE TABLE IF NOT EXISTS brigadistas (
    id         SERIAL PRIMARY KEY,
    nome       VARCHAR(150) NOT NULL,
    brigada    VARCHAR(150) NOT NULL,
    regiao     VARCHAR(150) NOT NULL,
    criado_em  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
