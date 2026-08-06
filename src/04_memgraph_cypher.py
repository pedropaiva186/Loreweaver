"""Etapa 7 — O mesmo grafo em um banco de grafos: Memgraph + Cypher.

Carrega as triplas refinadas no Memgraph usando Rótulos e Relações Nativas,
executa consultas Cypher e demonstra text-to-Cypher com schema rigoroso.
"""

import json
import sys
import re
import unicodedata
from importlib import import_module

from neo4j import GraphDatabase

from util_comum import DIR_DADOS, MODEL, chamar_modelo_sem_json

URI = "bolt://localhost:7687"

# Listas de validação/normalização conforme o schema
ENTIDADES_VALIDAS = {
    "item", "localizacao", "npc", "conceito", "inimigo", 
    "habilidade", "chefe", "vendedor", "grupo", "protagonista"
}

# Lista de relações válidas conforme o schema
RELACOES_VALIDAS = {
    "contem", "derrota", "usa", "localizado_em", "afeta", "requer",
    "executa_habilidade", "leva_a", "vende", "dropa", "libera",
    "cria", "eh_inimigo_de", "eh_relatado_por", "eh_membro_de", "protege"
}

# Dicionário com consultas básicas de exemplo para demonstração
CONSULTAS_CYPHER = {
    "Chefes derrotados no jogo": """
        MATCH (p)-[r:DERROTA]->(c:CHEFE)
        RETURN DISTINCT p.nome AS heroi, c.nome AS chefe
        LIMIT 15
    """,
    
    "Itens requeridos ou usados": """
        MATCH (item:ITEM)-[r:REQUER|USA]->(destino)
        RETURN DISTINCT item.nome AS item, type(r) AS relacao, destino.nome AS alvo
        LIMIT 10
    """,
    
    "Conexões de Locais": """
        MATCH (origem:LOCALIZACAO)-[r:LEVA_A|LOCALIZADO_EM]->(destino:LOCALIZACAO)
        RETURN DISTINCT origem.nome AS origem, type(r) AS relacao, destino.nome AS destino
        LIMIT 10
    """,
    
    "Itens vendidos por vendedores": """
        MATCH (v:VENDEDOR)-[r:VENDE]->(item:ITEM)
        RETURN DISTINCT v.nome AS vendedor, item.nome AS item
        LIMIT 10
    """,
}

# Prompt para gerar consultas Cypher a partir de perguntas em linguagem natural
PROMPT_TEXT2CYPHER = """Você é um especialista em Cypher que gera consultas para Memgraph/Neo4j.

SCHEMA DO BANCO:
- ENTIDADES (Labels dos Nós em MAIÚSCULAS):
  :ITEM, :LOCALIZACAO, :NPC, :CONCEITO, :INIMIGO, :HABILIDADE, :CHEFE, :VENDEDOR, :GRUPO, :PROTAGONISTA

- RELAÇÕES (Tipos de Aresta em MAIÚSCULAS):
  -[:CONTEM]-, -[:DERROTA]-, -[:USA]-, -[:LOCALIZADO_EM]-, -[:AFETA]-,
  -[:REQUER]-, -[:EXECUTA_HABILIDADE]-, -[:LEVA_A]-, -[:VENDE]-, -[:DROPA]-,
  -[:LIBERA]-, -[:CRIA]-, -[:EH_INIMIGO_DE]-, -[:EH_RELATADO_POR]-,
  -[:EH_MEMBRO_DE]-, -[:PROTEGE]-

OBJETIVO PRINCIPAL:
Você deve gerar consultas que maximizem o CONTEXTO NARRATIVO. 
Sempre que consultar uma relação [r], você DEVE OBRIGATORIAMENTE retornar r.evidencia AS contexto. É lá que está a lore rica do jogo.

REGRAS CRÍTICAS:
1. Para perguntas do tipo "Quem é X?", "Fale sobre X" ou "História de X" (Ego Graph):
   - Use relacionamentos NÃO-DIRECIONADOS -[r]- para pegar tudo que entra e sai do nó.
   - Ex: MATCH (n)-[r]-(m) WHERE toLower(n.nome) CONTAINS "sly" RETURN n.nome AS entidade1, type(r) AS relacao, m.nome AS entidade2, r.evidencia AS contexto LIMIT 50
2. Filtragem de Nomes (Desambiguação):
   - NUNCA use propriedades dentro do parênteses (ex: (:NPC {{nome: "X"}}) está ERRADO).
   - SEMPRE use WHERE toLower(n.nome) CONTAINS "texto". Isso garante que "sly" encontre tanto "sly" quanto "grande sabio do ferrao sly".
3. Sintaxe de Múltiplas Relações:
   - O correto é -[r:AFETA|DERROTA]- e NUNCA -[r:(AFETA|DERROTA)]-.
4. Retorno Obrigatório:
   - Sempre inclua r.evidencia AS contexto se houver uma variável de relação r na consulta.
   - Obrigatoriamente atribua um alias com 'AS' para CADA campo no RETURN (ex: type(r) AS relacao).
5. Formato da Resposta:
   - Responda APENAS com o código Cypher puro. 
   - NÃO use blocos de código Markdown (remova as crases ``` e a palavra cypher).
6. Proteção contra Fora de Escopo (Out-of-Domain):
    Se o usuário fizer uma pergunta que NÃO tenha relação com o universo do jogo, ou pedir códigos em outras linguagens (como Python, JavaScript, etc.), você NÃO DEVE gerar o que ele pediu e NÃO DEVE responder com texto natural.
    Nesses casos, você deve OBRIGATORIAMENTE retornar apenas a seguinte consulta de segurança em Cypher:
    RETURN "Fora de escopo" AS erro

EXEMPLOS DE CONSULTAS CORRETAS:
- "Quem é Sly?" ou "Fale sobre Sly":
  MATCH (n)-[r]-(m) 
  WHERE toLower(n.nome) CONTAINS "sly" 
  RETURN n.nome AS entidade_foco, type(r) AS relacao, m.nome AS entidade_relacionada, r.evidencia AS contexto LIMIT 50

- "O que o vendedor vende?":
  MATCH (v:VENDEDOR)-[r:VENDE]->(i:ITEM) 
  RETURN v.nome AS vendedor, i.nome AS item, r.evidencia AS contexto LIMIT 15

- "Quais itens são encontrados na Bacia Antiga?":
  MATCH (i:ITEM)-[r:LOCALIZADO_EM]->(l:LOCALIZACAO)
  WHERE toLower(l.nome) CONTAINS "bacia antiga"
  RETURN i.nome AS item, type(r) AS relacao, l.nome AS localizacao, r.evidencia AS contexto LIMIT 20

PERGUNTA: {pergunta}
"""


def remover_acentos(texto: str) -> str:
    """Remove acentos e marcas combinantes de uma string."""
    if texto is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def limpar_texto(texto: str) -> str:
    """Limpa o texto para uso em identificação/checagem de labels e prompts.

    - remove acentos
    - remove espaços extras
    - converte para minúsculas
    """
    if texto is None:
        return ""
    s = str(texto).strip()
    s = remover_acentos(s)
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def gerar_cypher_com_llm(pergunta: str) -> str:
    pergunta_limpa = limpar_texto(pergunta)
    cypher = chamar_modelo_sem_json(
        PROMPT_TEXT2CYPHER.format(pergunta=pergunta_limpa),
        temperature=0.0,
        max_tokens=1024,
    ).strip()
    cypher = re.sub(r"^```(?:cypher)?\n|```$", "", cypher, flags=re.IGNORECASE).strip()
    return cypher


# Normalizando identificadores
def sanitizar_identificador(texto: str, padrao: str = "OUTRO") -> str:
    if not texto:
        return padrao
    # Remove acentos e normaliza espaços antes de sanitizar
    texto_limpo = limpar_texto(texto)
    limpo = re.sub(r'[^a-zA-Z0-9_]', '_', texto_limpo).lower().strip('_')
    return limpo.upper() if limpo else padrao

# Responder a pergunta do usuário usando os resultados do grafo como contexto
def responder_pergunta_com_graphrag(pergunta, resultados_grafo):
    prompt_rag = f"""
    Você é um assistente especialista na lore de Hollow Knight.
    Responda à pergunta do usuário utilizando APENAS os fatos extraídos do banco de dados de grafos abaixo.

    PERGUNTA DO USUÁRIO:
    {pergunta}

    DADOS RECUPERADOS DO GRAFO:
    {json.dumps(resultados_grafo, ensure_ascii=False)}

    RESPOSTA (seja claro, conciso e natural):
    """
    return chamar_modelo_sem_json(prompt_rag, temperature=0.2)

# Função para carregar triplas refinadas no Memgraph usando Rótulos e Relações Nativas
def carregar_no_memgraph(driver, triplas):
    with driver.session() as sessao:
        sessao.run("MATCH (n) DETACH DELETE n")
        for t in triplas:
            # 1. etapa de normalização de tipos de origem, destino e relação
            raw_origem = limpar_texto(t.get("tipo_origem", "conceito"))
            raw_destino = limpar_texto(t.get("tipo_destino", "conceito"))
            raw_rel = limpar_texto(t.get("relacao", "afeta"))

            # Valida com o schema (fallback para CONCEITO / AFETA se inválido)
            label_origem = sanitizar_identificador(raw_origem if raw_origem in ENTIDADES_VALIDAS else "conceito")
            label_destino = sanitizar_identificador(raw_destino if raw_destino in ENTIDADES_VALIDAS else "conceito")
            tipo_relacao = sanitizar_identificador(raw_rel if raw_rel in RELACOES_VALIDAS else "afeta")

            # 2. Insere o nó e aresta no banco de grafos utilizando Rótulos e Relações Nativas
            query = f"""
            MERGE (a:`{label_origem}` {{nome: $origem}})
            MERGE (b:`{label_destino}` {{nome: $destino}})
            MERGE (a)-[r:`{tipo_relacao}`]->(b)
            SET r.fonte = $fonte, r.evidencia = $evidencia
            """

            sessao.run(
                query,
                origem=t["origem"],
                destino=t["destino"],
                fonte=t.get("fonte", "?"),
                evidencia=t.get("evidencia", ""),
            )

        total = sessao.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        rels = sessao.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
    print(f"Memgraph carregado: {total} nós, {rels} relações com Rótulos Nativos!")

# Executar uma consulta Cypher e retornar resultados como uma lista de dicionários
def executar(driver, cypher):
    with driver.session() as sessao:
        return [dict(reg) for reg in sessao.run(cypher)]


# Carregar triplas refinadas do arquivo JSON refinado no script 03_refinamento
def carregar_triplas():
    caminho = DIR_DADOS / "triplas_refinadas.json"
    if not caminho.exists():
        raise SystemExit(f"Arquivo não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding='utf-8'))["triplas"]


def main():
    triplas = carregar_triplas()
    try:
        driver = GraphDatabase.driver(URI, auth=("", ""))
        driver.verify_connectivity()
    except Exception as erro:
        raise SystemExit(
            f"Não foi possível conectar ao Memgraph em {URI} ({erro}).\n"
            "Suba o container: docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph-mage"
        )

    carregar_no_memgraph(driver, triplas)

    print("=" * 80)
    print("EXPLORADOR DA LORE — HOLLOW KNIGHT (CYPHER NATIVO)")
    print("=" * 80)

    for titulo, cypher in CONSULTAS_CYPHER.items():
        print(f"\n{titulo}")
        print("-" * 80)
        try:
            resultados = executar(driver, cypher)
            if resultados:
                for linha in resultados:
                    print(f"  ✓ {linha}")
            else:
                print("  (sem resultados)")
        except Exception as e:
            print(f"Erro na consulta: {e}")

    if "--llm" in sys.argv:
        perguntas = [
            "",
        ]
        
        print("\n" + "=" * 80)
        print("CONSULTAS GERADAS POR IA (text-to-Cypher)")
        print("=" * 80)
        
        for pergunta in perguntas:
            print(f"\nPergunta: {pergunta}")
            try:
                cypher = gerar_cypher_com_llm(pergunta)
                if not cypher:
                    print("  [Erro] Falha ao gerar cypher.")
                    continue
                
                print(f"\n[Cypher Gerado]:\n{cypher}\n")
                
                # Executa no banco de grafos
                resultados_grafo = executar(driver, cypher)
                print(f"[Resultados Brutos]: {resultados_grafo}\n")
                
                # Responde via RAG usando os dados extraídos
                resposta_final = responder_pergunta_com_graphrag(pergunta, resultados_grafo)
                print(f"[Resposta RAG]:\n{resposta_final}")
                
            except Exception as e:
                print(f"  [Erro ao processar LLM/Execução]: {e}")

if __name__ == "__main__":
    main()