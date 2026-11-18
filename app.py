from datetime import date

from flask import Flask, jsonify, request

import database as db

app = Flask(__name__)
app.json.sort_keys = False

CAMPOS_OBRIGATORIOS = ("solicitante", "endereco", "area_hectares", "data_prevista")


def validar_agendamento(dados):
    """Retorna uma mensagem de erro, ou None se os dados forem válidos."""
    if not isinstance(dados, dict):
        return "Corpo da requisição deve ser um JSON."
    faltando = [c for c in CAMPOS_OBRIGATORIOS if dados.get(c) in (None, "")]
    if faltando:
        return f"Campos obrigatórios ausentes: {', '.join(faltando)}"
    area = dados["area_hectares"]
    if isinstance(area, bool) or not isinstance(area, (int, float)) or area <= 0:
        return "area_hectares deve ser um número maior que zero."
    try:
        date.fromisoformat(dados["data_prevista"])
    except (TypeError, ValueError):
        return "data_prevista deve estar no formato AAAA-MM-DD."
    return None


@app.get("/agendamentos")
def listar():
    return jsonify(db.listar())


@app.get("/agendamentos/<int:id_>")
def buscar(id_):
    ag = db.buscar(id_)
    if not ag:
        return jsonify({"erro": "Agendamento não encontrado."}), 404
    return jsonify(ag)


@app.post("/agendamentos")
def criar():
    dados = request.get_json(silent=True)
    erro = validar_agendamento(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    return jsonify(db.inserir(dados)), 201


@app.put("/agendamentos/<int:id_>")
def atualizar(id_):
    if not db.buscar(id_):
        return jsonify({"erro": "Agendamento não encontrado."}), 404
    dados = request.get_json(silent=True)
    erro = validar_agendamento(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    return jsonify(db.atualizar(id_, dados))


@app.patch("/agendamentos/<int:id_>")
def alterar_status(id_):
    if not db.buscar(id_):
        return jsonify({"erro": "Agendamento não encontrado."}), 404
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        dados = {}
    status = dados.get("analise_brigadista")
    if status not in db.STATUS_VALIDOS:
        return jsonify({"erro": f"analise_brigadista deve ser um de: {', '.join(db.STATUS_VALIDOS)}"}), 400

    # regra de negócio: aceitar ou recusar exige saber qual brigadista fez a análise
    brigadista_id = None
    if status != "em_analise":
        brigadista_id = dados.get("brigadista_id")
        if isinstance(brigadista_id, bool) or not isinstance(brigadista_id, int):
            return jsonify({"erro": "brigadista_id é obrigatório para aceitar ou recusar uma solicitação."}), 400
        if not db.buscar_brigadista(brigadista_id):
            return jsonify({"erro": f"Brigadista {brigadista_id} não encontrado."}), 400
    return jsonify(db.alterar_status(id_, status, brigadista_id))


@app.delete("/agendamentos/<int:id_>")
def excluir(id_):
    # exclusão lógica: o registro fica no banco, mas como "recusada" não aparece mais no GET
    if not db.buscar(id_):
        return jsonify({"erro": "Agendamento não encontrado."}), 404
    db.excluir(id_)
    return "", 204


# ---------- brigadistas ----------

CAMPOS_BRIGADISTA = ("nome", "brigada", "regiao")


def validar_brigadista(dados):
    """Retorna uma mensagem de erro, ou None se os dados forem válidos."""
    if not isinstance(dados, dict):
        return "Corpo da requisição deve ser um JSON."
    faltando = [c for c in CAMPOS_BRIGADISTA
                if not isinstance(dados.get(c), str) or not dados[c].strip()]
    if faltando:
        return f"Campos obrigatórios ausentes: {', '.join(faltando)}"
    return None


@app.get("/brigadistas")
def listar_brigadistas():
    return jsonify(db.listar_brigadistas())


@app.get("/brigadistas/<int:id_>")
def buscar_brigadista(id_):
    brigadista = db.buscar_brigadista(id_)
    if not brigadista:
        return jsonify({"erro": "Brigadista não encontrado."}), 404
    return jsonify(brigadista)


@app.post("/brigadistas")
def criar_brigadista():
    dados = request.get_json(silent=True)
    erro = validar_brigadista(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    return jsonify(db.inserir_brigadista(dados)), 201


@app.get("/brigadistas/<int:id_>/agendamentos")
def agendamentos_do_brigadista(id_):
    if not db.buscar_brigadista(id_):
        return jsonify({"erro": "Brigadista não encontrado."}), 404
    return jsonify(db.listar_agendamentos_do_brigadista(id_))


if __name__ == "__main__":
    db.criar_tabela()
    app.run(debug=True)
