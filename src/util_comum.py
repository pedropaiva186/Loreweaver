import collections
import itertools
import json
import os
import pathlib
import re
import sys
import time

import tiktoken
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Verificação de segurança para garantir que a chave foi carregada
CHAVE_API = os.environ.get("GEMINI_API_KEY")
if not CHAVE_API:
    raise ValueError(
        "Chave da API não encontrada! Certifique-se de que o arquivo .env existe "
        "na raiz do projeto e contém a variável GEMINI_API_KEY."
    )

# Inicializa o cliente da nova biblioteca
client = genai.Client(api_key=CHAVE_API)

DIR_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "data" / "hollow_knight_wiki_knowledge_pt"
DIR_DADOS = pathlib.Path(__file__).resolve().parent.parent / "data" / "hollowknight_pipeline"

CHUNK_SIZE = 3000
CHUNK_OVERLAP = 400
MODEL = "gemini-3.5-flash-lite"

# --- Controle de taxa (Janela e Retry) -------------------------------------

# Free tier do Gemini: 15 requisições por minuto por modelo. Deixamos uma
# folga (14) porque a janela do servidor não é exatamente a nossa.
LIMITE_RPM = int(os.environ.get("GEMINI_RPM", "14"))
JANELA_SEGUNDOS = 60
MAX_TENTATIVAS = 5

_QUADROS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Instantes (time.monotonic) das requisições feitas na janela corrente.
_historico = collections.deque()


def _tty():
    return sys.stderr.isatty()


def aguardar_com_animacao(segundos, motivo):
    """Espera `segundos` mostrando um spinner com contagem regressiva."""
    if segundos <= 0:
        return
    if not _tty():
        print(f"[rate limit] {motivo}: aguardando {segundos:.1f}s", file=sys.stderr)
        time.sleep(segundos)
        return

    fim = time.monotonic() + segundos
    for quadro in itertools.cycle(_QUADROS):
        restante = fim - time.monotonic()
        if restante <= 0:
            break
        sys.stderr.write(f"\r\033[K{quadro} {motivo} — retomando em {restante:4.1f}s")
        sys.stderr.flush()
        time.sleep(min(0.1, restante))
    sys.stderr.write("\r\033[K")
    sys.stderr.flush()


def extrair_atraso(erro):
    """Descobre quantos segundos esperar a partir do erro 429 da API."""
    texto = str(erro)
    achado = re.search(r"retry in ([\d.]+)s", texto)
    if not achado:
        achado = re.search(r"'retryDelay': '(\d+(?:\.\d+)?)s'", texto)
    if not achado:
        return None
    # Margem de segurança: o relógio do servidor não é o nosso.
    return float(achado.group(1)) + 0.5


def _respeitar_limite():
    """Espera, se preciso, para não estourar LIMITE_RPM requisições/minuto."""
    agora = time.monotonic()
    while _historico and agora - _historico[0] >= JANELA_SEGUNDOS:
        _historico.popleft()

    if len(_historico) >= LIMITE_RPM:
        espera = JANELA_SEGUNDOS - (agora - _historico[0]) + 0.2
        aguardar_com_animacao(
            espera, f"cota de {LIMITE_RPM} req/min atingida"
        )
        agora = time.monotonic()
        while _historico and agora - _historico[0] >= JANELA_SEGUNDOS:
            _historico.popleft()

    _historico.append(time.monotonic())


def chamar_api(funcao, *args, **kwargs):
    """Executa uma chamada à API Gemini com controle de taxa e retry no 429."""
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        _respeitar_limite()
        try:
            return funcao(*args, **kwargs)
        except APIError as erro:
            codigo_erro = getattr(erro, "code", getattr(erro, "status_code", None))
            
            # Verifica se é rate limit (429)
            if codigo_erro != 429 and "429" not in str(erro):
                if tentativa == MAX_TENTATIVAS:
                    raise
            elif tentativa == MAX_TENTATIVAS:
                raise
                
            # Extrai o atraso exato ou usa backoff exponencial como plano B
            espera = extrair_atraso(erro) or min(2**tentativa, JANELA_SEGUNDOS)
            aguardar_com_animacao(
                espera, f"cota excedida (429), tentativa {tentativa}/{MAX_TENTATIVAS}"
            )
            # A cota estourou de fato: limpamos a janela local pois ela dessincronizou.
            _historico.clear()


# --- Funções do Modelo e Utilidades do Pipeline ----------------------------

def chamar_modelo(prompt, temperature=0.1, max_tokens=2048):
    """Gera conteúdo (forçando JSON) utilizando o controle de taxa global."""
    resposta = chamar_api(
        client.models.generate_content,
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )
    )
    return resposta.text.strip()


def chamar_modelo_sem_json(prompt, temperature=0.1, max_tokens=2048):
    """Gera conteúdo (texto livre) utilizando o controle de taxa global."""
    resposta = chamar_api(
        client.models.generate_content,
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    )
    return resposta.text.strip()


def carregar_corpus():
    docs = []
    if not DIR_CORPUS.exists():
        raise SystemExit(f"Corpus não encontrado em {DIR_CORPUS}")
    for caminho in sorted(DIR_CORPUS.glob("*.md")):
        docs.append((caminho.name, caminho.read_text(encoding="utf-8")))
    if not docs:
        raise SystemExit(f"Nenhum documento encontrado em {DIR_CORPUS}")
    return docs


def dividir_em_chunks(texto):
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(texto)
    total_tokens = len(tokens)

    if total_tokens <= (CHUNK_SIZE * 1.2):
        return [texto]
    
    chunks = []
    inicio = 0

    while inicio < len(tokens):
        chunk_tokens = tokens[inicio : inicio + CHUNK_SIZE]
        chunk_texto = encoder.decode(chunk_tokens)
        chunks.append(chunk_texto)
        inicio += CHUNK_SIZE - CHUNK_OVERLAP
        
    return chunks


def extrair_json_do_texto(texto):
    texto = texto.strip()
    if texto.startswith('```'):
        texto = re.sub(r"^```[a-zA-Z0-9]*\n|```$", "", texto, flags=re.MULTILINE)
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        texto = match.group(0)
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        raise ValueError(f"Não foi possível parsear JSON da resposta: {texto[:200]}...")


def escrever_json(path, conteudo):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)


def extrair_json_seguro(resposta, max_tentativas=3):
    resposta = resposta.replace("```json", "").replace("```", "")
    
    import re
    json_matches = re.findall(r'\{.*\}', resposta, re.DOTALL)
    
    for tentativa, match in enumerate(json_matches):
        try:
            return json.loads(match)
        except json.JSONDecodeError as e:
            if tentativa == len(json_matches) - 1:
                raise e
            continue