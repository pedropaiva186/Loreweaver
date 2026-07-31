import json
import os
import networkx as nx
import ollama
import re
from tqdm import tqdm
from json_repair import repair_json

PATH_KNOWLEDGE_GRAPH = 'data/knowledge_graph_hk.json'
PATH_DEDUP_GRAPH = 'data/knowledge_graph_hk_clean.json'
CHECKPOINT_FILE = 'data/dedup_checkpoint.json'
MODEL = "mistral:7b-instruct-v0.3-q4_K_M"

REMOVE_DUPLICATES_PROMPT = '''Given these entity names from a Hollow Knight knowledge graph,
identify which ones refer to the SAME entity (case-insensitive, aliases,
Portuguese/English variations). Return a JSON object mapping each name
to its canonical form.

Names:
{names_list}

Return format:
{{"Knight": "The Knight", "the knight": "The Knight", "Dirtmouth": "Dirtmouth", "dirtmouth": "Dirtmouth"}}'''

def load_graph(path: str) -> nx.DiGraph:
    print(f"Carregando grafo de {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return nx.node_link_graph(data)

def save_graph(graph: nx.DiGraph, path: str):
    print(f"Salvando grafo limpo em {path}...")
    data = nx.node_link_data(graph)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_checkpoint(mapping: dict):
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

def extract_json_from_text(text: str) -> dict:
    match = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    if match:
        text = match.group(0)
    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except Exception as e:
        return {}

def fast_programmatic_dedup(entities: list) -> dict:
    """Pré-filtro rápido para strings idênticas (ignorando case/espaços)."""
    mapping = {}
    canonical_map = {}
    
    for entity in entities:
        normalized = entity.strip().lower()
        if normalized not in canonical_map:
            canonical_map[normalized] = entity # O primeiro que aparecer vira o canônico
        mapping[entity] = canonical_map[normalized]
        
    return mapping

def deduplicate_large_graph(graph: nx.DiGraph) -> nx.DiGraph:
    entities = list(graph.nodes())
    print(f"Total de entidades originais: {len(entities)}")

    # Pré-processamento algorítmico (muito mais rápido que o LLM)
    programmatic_mapping = fast_programmatic_dedup(entities)
    
    # Filtrar apenas as entidades canônicas resultantes para enviar ao LLM
    unique_entities = list(set(programmatic_mapping.values()))
    print(f"Entidades após pré-filtro algorítmico: {len(unique_entities)}")

    # Processamento via LLM com Checkpoint
    name_to_canonical = load_checkpoint()
    
    # Filtrar o que já foi processado no checkpoint
    entities_to_process = [e for e in unique_entities if e not in name_to_canonical]
    
    if entities_to_process:
        print(f"Iniciando deduplicação LLM para {len(entities_to_process)} entidades...")
        batch_size = 30
        
        for i in tqdm(range(0, len(entities_to_process), batch_size), desc="Processando Lotes"):
            batch = entities_to_process[i:i + batch_size]
            names_list = '\n'.join(f'- {name}' for name in batch)
            
            try:
                response = ollama.chat(
                    model=MODEL,
                    format="json",
                    messages=[{'role': 'user', 'content': REMOVE_DUPLICATES_PROMPT.format(names_list=names_list)}],
                    options={'temperature': 0.0, 'num_ctx': 4096}
                )
                raw = response['message']['content'].strip()
                mapping = extract_json_from_text(raw)
                
                # Prevenir que o modelo retorne mapeamentos vazios ou destrua chaves
                for name in batch:
                    name_to_canonical[name] = mapping.get(name, name)
                
                save_checkpoint(name_to_canonical)
                
            except Exception as e:
                print(f"\nErro no lote {i // batch_size + 1}: {e}. Salvando checkpoint atual...")
                save_checkpoint(name_to_canonical)
    else:
        print("Todas as entidades já foram processadas via LLM (Checkpoint carregado).")

    # Construir o novo grafo
    G = nx.DiGraph()
    print("\nReconstruindo arestas e fundindo nós...")
    
    def get_final_canonical(node_name):
        if node_name is None:
            return "Unknown"
            
        prog_can = programmatic_mapping.get(node_name, node_name)
        canonical = name_to_canonical.get(prog_can, prog_can)
        
        # Proteção contra nulos
        if canonical is None:
            return prog_can
            
        # Proteção contra alucinações estruturais da IA (retornar um Dict ou List)
        if isinstance(canonical, (dict, list)):
            return prog_can
            
        # Força a conversão para string final (evita números, booleanos, etc)
        return str(canonical).strip()

    for node, data in graph.nodes(data=True):
        canonical = get_final_canonical(node)
        if canonical not in G:
            G.add_node(canonical, **data)
        else:
            G.nodes[canonical].update(data)

    for a, b, data in tqdm(graph.edges(data=True), desc="Mapeando Relações"):
        can_a = get_final_canonical(a)
        can_b = get_final_canonical(b)
        
        # Proteção 3: Só cria a aresta se as entidades existirem e não apontarem para si mesmas
        if can_a is not None and can_b is not None and can_a != can_b:
            G.add_edge(can_a, can_b, **data)

    print(f"\nGrafo finalizado! Total de entidades únicas: {G.number_of_nodes()}")
    return G

if __name__ == '__main__':
    # Cria o diretório caso não exista
    os.makedirs('data', exist_ok=True)
    
    if os.path.exists(PATH_KNOWLEDGE_GRAPH):
        grafo_original = load_graph(PATH_KNOWLEDGE_GRAPH)
        grafo_limpo = deduplicate_large_graph(grafo_original)
        save_graph(grafo_limpo, PATH_DEDUP_GRAPH)
        
        # Opcional: Remover checkpoint após sucesso
        # if os.path.exists(CHECKPOINT_FILE):
        #    os.remove(CHECKPOINT_FILE)
    else:
        print(f"Erro: Arquivo {PATH_KNOWLEDGE_GRAPH} não encontrado.")