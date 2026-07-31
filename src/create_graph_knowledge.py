import os
import math
import ollama
import json
import time
import networkx as nx
import re
from json_repair import repair_json

# important parameters to do chunking in big files (all values are counting the characters)
CHUNK_THRESHOLD = 4000
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 250

MODEL = "mistral:7b-instruct-v0.3-q4_K_M"
PATH_KNOWLEDGE_GRAPH = 'data/knowledge_graph_hk.json'

EXPLANATION_PROMPT = '''
You are an expert at extracting structured knowledge from texts about Hollow Knight.
Given a text, extract all entities and their relationships.
Respond ONLY with valid JSON. No markdown, no code fences.
Start your response with '{' and end with '}'. Return a JSON object.'''

EXTRACTION_ONTOLOGIES_PROMPT = '''
Extract all entities and relations from the text about Hollow Knight.

Return ONLY a valid, single JSON object. Do not output any thinking process, text, or explanations outside the JSON.

Expected JSON Structure:
{{
  "entities": [
    {{"id": "Entity Name", "type": "character|location|item|concept|event|organization", "section": "{section_name}"}}
  ],
  "relations": [
    {{"source": "Entity Name", "target": "Entity Name", "type": "relation_description"}}
  ]
}}

Guidelines:
1. Entity IDs must use canonical, standard names (e.g., "The Knight", "Hornet", "Hallownest").
2. Relation types must be short, lowercase, and descriptive with underscores (e.g., "is_located_in", "is_child_of", "defeats").
3. Replace special/accented characters with standard ASCII equivalents (e.g., convert "ç" to "c", "á" to "a").
4. If no entities or relations are found, return empty lists: {{"entities": [], "relations": []}}.

Text to process:
{chunk}'''

REMOVE_DUPLICATES_PROMPT = '''Given these entity names from a Hollow Knight knowledge graph,
identify which ones refer to the SAME entity (case-insensitive, aliases,
Portuguese/English variations). Return a JSON object mapping each name
to its canonical form.

Names:
{names_list}

Return format:
{{"Knight": "The Knight", "the knight": "The Knight", ...}}'''

'''
#
# Functions Section
#
'''

def create_knowledge_graph(folder_path : str):
    final_graph = nx.DiGraph()
    for root, _, files in os.walk(folder_path):
        for i, file in enumerate(files):
            if i % 8 == 0:
                time.sleep(5)
            print(f'Arquivo: {i+1} | {len(files)}')
            file_name = os.path.join(root, file)
            g = process_file(file_name)
            if g:
                final_graph = nx.compose(final_graph, g)
                save_graph(final_graph, PATH_KNOWLEDGE_GRAPH)
    final_graph = deduplicate_entities(final_graph)
    save_graph(final_graph, PATH_KNOWLEDGE_GRAPH)

def chunk_content(content : str) -> list[str]:
    content_chunked = list()

    for i in range(math.ceil(len(content) / CHUNK_SIZE)):
        content_chunked.append(content[max((i * CHUNK_SIZE) - CHUNK_OVERLAP, 0): min(((i + 1) * CHUNK_SIZE) + CHUNK_OVERLAP, len(content))])

    return content_chunked

def extract_ontologies(chunks : list) -> nx.DiGraph:
    ontologies = list()

    for i, chunk in enumerate(chunks):
        print(f'Processando chunk: {i+1}/{len(chunks)}')
        result = extract_with_gleanings(chunk, n=2)
        ontologies.append(result)
        time.sleep(1)

    return build_graph_from_extractions(ontologies)

def build_graph_from_extractions(extractions: list[dict]) -> nx.DiGraph:
    g = nx.DiGraph()

    for extraction in extractions:
        for entity in extraction.get('entities', []):
            g.add_node(entity.get('id'), type=entity.get('type'))

        for rel in extraction.get('relations', []):
            g.add_edge(rel.get('source'), rel.get('target'), type=rel.get('type'))

    return g

def save_graph(graph: nx.DiGraph, path: str):
    data = nx.node_link_data(graph)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_graph(path: str) -> nx.DiGraph:
    with open(path) as f:
        data = json.load(f)
    return nx.node_link_graph(data)

def process_file(file_path : str) -> nx.DiGraph:
    content = ''
    content_chunked = list()

    with open(file_path, 'r') as f:
        content = f.read()

    if len(content) > CHUNK_THRESHOLD: # process big files with chunking
        result = chunk_content(content)
        content_chunked = [(chunk + f'; font: {file_path}') for chunk in result]
    else:
        content_chunked.append(content + f'; font: {file_path}')

    return extract_ontologies(content_chunked)

def extract_json_from_text(text: str) -> dict:
    text = text.strip()
    if text.startswith('"entities"') or text.startswith('"relations"'):
        text = "{" + text + "}"

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except Exception as e:
        raise ValueError(
            f"Could not extract valid JSON from response: {text[:100]}... Error: {e}"
        )

def extract_entities_relationships(chunk : str) -> dict:
    response = ollama.chat(
        model=MODEL,
        format="json",
        messages=[
            {'role': 'system', 'content': EXPLANATION_PROMPT},
            {'role': 'user', 'content': EXTRACTION_ONTOLOGIES_PROMPT.replace('{chunk}', chunk)}
        ],
        keep_alive= -1, # keep the model in memory ever
        options={
            'num_ctx': 8192,
            'num_predict': 2048,
            'temperature': 0.1, # low temperature to greater robustness
            'stop': ["```\n\n", "}\n\n"]
        }
    )

    raw = response['message']['content'].strip()

    return extract_json_from_text(raw)


def extract_with_gleanings(chunk: str, n: int = 3) -> dict:
    all_entities = {}
    all_relations = set()

    for i in range(n):
        try:
            result = extract_entities_relationships(chunk)
            for e in result.get('entities', []):
                eid = e.get('id')
                if eid and eid not in all_entities:
                    all_entities[eid] = e
            for r in result.get('relations', []):
                key = (r.get('source'), r.get('target'), r.get('type'))
                all_relations.add(key)
        except Exception as e:
            print(f'Gleaning pass {i+1} failed: {e}')
        time.sleep(0.5)

    return {
        'entities': list(all_entities.values()),
        'relations': [
            {'source': s, 'target': t, 'type': r}
            for s, t, r in all_relations
        ]
    }


def deduplicate_entities(graph: nx.DiGraph) -> nx.DiGraph:
    entities = list(graph.nodes(data=True))
    name_to_canonical = {}

    for i in range(0, len(entities), 30):
        batch = [name for name, _ in entities[i:i + 30]]
        names_list = '\n'.join(f'- {name}' for name in batch)
        
        response = ollama.chat(
            model=MODEL,
            format="json",
            messages=[{'role': 'user', 'content': REMOVE_DUPLICATES_PROMPT.format(names_list=names_list)}],
            options={'temperature': 0.0}
        )
        raw = response['message']['content'].strip()

        try:
            mapping = extract_json_from_text(raw)
            name_to_canonical.update(mapping)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Dedup batch {i // 30 + 1} failed: {e}")

    G = nx.DiGraph()
    for node, data in graph.nodes(data=True):
        canonical = name_to_canonical.get(node, node)
        if canonical not in G:
            G.add_node(canonical, **data)

    for a, b, data in graph.edges(data=True):
        can_a = name_to_canonical.get(a, a)
        can_b = name_to_canonical.get(b, b)
        if can_a != can_b:
            G.add_edge(can_a, can_b, **data)

    return G


'''
#
# Code Section
#
'''

if __name__ == '__main__':
    wiki_path = 'data/hollow_knight_wiki_knowledge_pt'
    create_knowledge_graph(wiki_path)