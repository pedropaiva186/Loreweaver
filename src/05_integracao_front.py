import importlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase

# Importa o módulo 04_memgraph_cypher.py
m_cypher = importlib.import_module("04_memgraph_cypher")

app = Flask(__name__)
# Ativa o CORS para permitir a comunicação do front com o back
CORS(app) 

# Inicializa a conexão com a database de maneira global
try:
    driver = GraphDatabase.driver(m_cypher.URI, auth=("", ""))
    driver.verify_connectivity()
    print("Conexão com o Memgraph estabelecida.")
except Exception as e:
    print(f" Falha ao conectar com o memgraph: {e}")
    driver = None

@app.route('/', methods=['GET'])
def home():
    return "A API do loreweaver está rodando! O frontend deve se conectar a /api/chat."

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Nenhuma mensagem fornecida"}), 400

    user_message = data['message']

    # Verifica se o memgraph está realmente executando
    if not driver:
        return jsonify({"response": "Erro: Não foi possível conectar ao banco de dados Memgraph. Verifique se o container docker está rodando."})

    try:
        print(f"\n--- Nova pergunta: {user_message} ---")
        
        # 1. Geração da query cypher pela llm
        cypher_query = m_cypher.gerar_cypher_com_llm(user_message)
        print(f"Cypher Query Gerada:\n{cypher_query}")
        
        # 2. Execução da query
        resultados_grafo = m_cypher.executar(driver, cypher_query)
        print(f"Resultados do Grafo:\n{resultados_grafo}")
        
        # 3. Geração da respota pela llm
        resposta_final = m_cypher.responder_pergunta_com_graphrag(user_message, resultados_grafo)
        
        # 4. Retorna a resposta final para o front
        return jsonify({"response": resposta_final})

    except Exception as e:
        # Printa o erro nos logs
        print(f"Erro interno no backend (Memgraph/LLM): {e}")
        
        # Retorna uma mensagem amigável para o usuário final
        mensagem_amigavel = (
            "Eu não posso responder essa pergunta. Você pode perguntar outras coisas, como: "
            "*\"Onde encontrar a chave para abrir a cidade das lágrimas?\"*"
        )
        
        return jsonify({"response": mensagem_amigavel})

if __name__ == '__main__':
    print("Starting LoreWeaver API Server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)