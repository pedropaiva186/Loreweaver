# LoreWeaver - Pipeline de conhecimento para Hollow Knight

## Equipe

| # | Nome completo | Matrícula |
| --- | --- | --- |
| 1 | João Victor Oliveira | (20240008468) |
| 2 | Kevin Gabriel Mangueira | (20240008000) |
| 3 | Luiz Henrique Santos | (20240008261) |
| 4 | Pedro Henrique Paiva | (20240008145) |
| 5 | Victor Gabriel Menezes | (20240008323) |

---

Este projeto reúne um pipeline completo para construir uma base de conhecimento sobre Hollow Knight, extrair triplas semânticas, carregar esses dados em um banco de grafos e disponibilizar uma interface de conversa em uma página HTML.

O fluxo atual é composto pelos scripts 01 a 05:

1. Extração de páginas da wiki para arquivos Markdown.
2. Geração de triplas a partir do corpus.
3. Refinamento e normalização das triplas.
4. Carregamento das triplas no Memgraph.
5. Integração com a interface web.

---

## Pré-requisitos

- Python 3.12
- Docker
- Chave de API do Gemini
- Acesso à internet para consultar a wiki e chamar a API do Gemini

## Configuração do ambiente

### 1. Criar e ativar um ambiente virtual com venv

No Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar as dependências

Na raiz do projeto, execute:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar a chave do Gemini

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:

```env
GEMINI_API_KEY=sua_chave_aqui
```

---

## Fluxo de execução do loreweaver

### 0. Script 01 - Obter a wiki

Esse script acessa a wiki de Hollow Knight e salva os artigos limpos em Markdown.

```bash
python src/01_obter_wiki.py
```

### 1. Script 02 - Extração de triplas

Esse script lê o corpus gerado no passo anterior e usa o Gemini para extrair triplas de conhecimento.

```bash
python src/02_extracao_triplas.py
```

Os resultados são salvos em:

- `data/hollowknight_pipeline/triplas_brutas.json`

### 2. Script 03 - Refinamento das triplas

Esse script normaliza entidades, relações e remove ruídos, produzindo um conjunto mais limpo para o banco de grafos.

```bash
python src/03_refinamento_triplas.py
```

O arquivo gerado é:

- `data/hollowknight_pipeline/triplas_refinadas.json`

### 3. Subir o Memgraph

Antes de rodar o script 04, inicie o container do Memgraph:

```bash
docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph-mage
```


### 4. Script 04 - Memgraph e Cypher

Esse script carrega as triplas refinadas no Memgraph e executa consultas de exemplo em Cypher.

```bash
python src/04_memgraph_cypher.py
```

### 5. Script 05 - Integração com o frontend

Esse script sobe a API Flask que recebe perguntas do usuário, gera uma consulta Cypher e retorna uma resposta com base no grafo.

```bash
python src/05_integracao_front.py
```

A API fica disponível em:

- `http://127.0.0.1:5000/api/chat`

### 6. Abrir a interface HTML

A interface web está em `index.html`.

Para evitar problemas de CORS, é recomendado subir a pasta do projeto com um servidor simples:

```bash
python -m http.server 8000
```

Depois abra no navegador:

- `http://127.0.0.1:8000/`

---

## Arquivos principais

- `src/01_obter_wiki.py` - extração dos artigos da wiki
- `src/02_extracao_triplas.py` - extração de triplas com Gemini
- `src/03_refinamento_triplas.py` - normalização das triplas
- `src/04_memgraph_cypher.py` - carga no Memgraph e consultas Cypher
- `src/05_integracao_front.py` - API backend para o frontend
- `index.html` - interface web do projeto

---

## Observações

- O processo depende de uma chave válida do Gemini configurada no `.env`.
- O Memgraph precisa estar rodando antes do passo 04.
- Se algum passo falhar, a execução pode ser repetida a partir do script seguinte, desde que os arquivos intermediários já tenham sido gerados.
