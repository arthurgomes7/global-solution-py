import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()  # lê o arquivo .env da pasta do projeto, se existir

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "queimas"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

STATUS_VALIDOS = ("em_analise", "aceita", "recusada")

# datas convertidas para texto para o JSON sair no formato AAAA-MM-DD
COLUNAS = """id, solicitante, endereco, area_hectares,
             data_prevista::text AS data_prevista, descricao, analise_brigadista,
             brigadista_id, to_char(criado_em, 'YYYY-MM-DD HH24:MI:SS') AS criado_em"""

COLUNAS_BRIGADISTA = """id, nome, brigada, regiao,
             to_char(criado_em, 'YYYY-MM-DD HH24:MI:SS') AS criado_em"""


MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def conectar():
    return psycopg.connect(**DB_CONFIG, row_factory=dict_row, connect_timeout=5)


def criar_tabela():
    """Aplica os scripts de migrations/ em ordem (todos idempotentes, ver MIGRATION.md)."""
    with conectar() as conn:
        for script in sorted(MIGRATIONS_DIR.glob("*.sql")):
            conn.execute(script.read_text(encoding="utf-8"))


def listar():
    with conectar() as conn:
        return conn.execute(
            f"SELECT {COLUNAS} FROM agendamentos WHERE analise_brigadista <> 'recusada' ORDER BY id"
        ).fetchall()


def buscar(id_):
    with conectar() as conn:
        return conn.execute(
            f"SELECT {COLUNAS} FROM agendamentos WHERE id = %s AND analise_brigadista <> 'recusada'",
            (id_,),
        ).fetchone()


def inserir(d):
    with conectar() as conn:
        return conn.execute(
            f"""INSERT INTO agendamentos (solicitante, endereco, area_hectares, data_prevista, descricao)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {COLUNAS}""",
            (d["solicitante"], d["endereco"], d["area_hectares"], d["data_prevista"], d.get("descricao")),
        ).fetchone()


def atualizar(id_, d):
    with conectar() as conn:
        return conn.execute(
            f"""UPDATE agendamentos
                SET solicitante = %s, endereco = %s, area_hectares = %s, data_prevista = %s, descricao = %s
                WHERE id = %s
                RETURNING {COLUNAS}""",
            (d["solicitante"], d["endereco"], d["area_hectares"], d["data_prevista"], d.get("descricao"), id_),
        ).fetchone()


def alterar_status(id_, status, brigadista_id):
    """Registra a análise: o status e o brigadista responsável (None quando volta a em_analise)."""
    with conectar() as conn:
        return conn.execute(
            f"""UPDATE agendamentos SET analise_brigadista = %s, brigadista_id = %s
                WHERE id = %s RETURNING {COLUNAS}""",
            (status, brigadista_id, id_),
        ).fetchone()


def excluir(id_):
    """Exclusão lógica: marca como recusada e mantém o brigadista que já estava vinculado."""
    with conectar() as conn:
        conn.execute("UPDATE agendamentos SET analise_brigadista = 'recusada' WHERE id = %s", (id_,))


# ---------- brigadistas ----------

def listar_brigadistas():
    with conectar() as conn:
        return conn.execute(f"SELECT {COLUNAS_BRIGADISTA} FROM brigadistas ORDER BY id").fetchall()


def buscar_brigadista(id_):
    with conectar() as conn:
        return conn.execute(
            f"SELECT {COLUNAS_BRIGADISTA} FROM brigadistas WHERE id = %s", (id_,)
        ).fetchone()


def inserir_brigadista(d):
    with conectar() as conn:
        return conn.execute(
            f"""INSERT INTO brigadistas (nome, brigada, regiao)
                VALUES (%s, %s, %s)
                RETURNING {COLUNAS_BRIGADISTA}""",
            (d["nome"], d["brigada"], d["regiao"]),
        ).fetchone()


def listar_agendamentos_do_brigadista(brigadista_id):
    """Histórico de análises do brigadista, incluindo as solicitações recusadas."""
    with conectar() as conn:
        return conn.execute(
            f"SELECT {COLUNAS} FROM agendamentos WHERE brigadista_id = %s ORDER BY id",
            (brigadista_id,),
        ).fetchall()
