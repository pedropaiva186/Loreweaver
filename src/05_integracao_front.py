import importlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase

# Dynamically import the memgraph module because the filename starts with a number
m_cypher = importlib.import_module("04_memgraph_cypher")

app = Flask(__name__)
# Enable CORS so the frontend can communicate with the backend
CORS(app) 

# Initialize the Memgraph connection globally
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

    # Verify if Memgraph is active before trying to query
    if not driver:
        return jsonify({"response": "Erro: Não foi possível conectar ao banco de dados Memgraph. Verifique se o container docker está rodando."})

    try:
        print(f"\n--- Nova pergunta: {user_message} ---")
        
        # 1. Generate Cypher query via LLM
        cypher_query = m_cypher.gerar_cypher_com_llm(user_message)
        print(f"Cypher Query Gerada:\n{cypher_query}")
        
        # 2. Execute query in Memgraph
        resultados_grafo = m_cypher.executar(driver, cypher_query)
        print(f"Resultados do Grafo:\n{resultados_grafo}")
        
        # 3. Generate final response via RAG
        resposta_final = m_cypher.responder_pergunta_com_graphrag(user_message, resultados_grafo)
        
        # 4. Return the actual AI response to the frontend
        return jsonify({"response": resposta_final})

    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        return jsonify({"response": f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"})

if __name__ == '__main__':
    print("Starting LoreWeaver API Server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)