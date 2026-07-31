# Trabalho III - Grafo de Conhecimento com Inteligência Artificial

Este projeto implementa a geração, estruturação e otimização de um Grafo de Conhecimento (utilizando `networkx`) em conjunto com um modelo de Inteligência Artificial rodando localmente. O pipeline é dividido em duas etapas principais: a extração de entidades brutas a partir de textos e a deduplicação inteligente utilizando processamento algorítmico e IA.

## 🛠️ Pré-requisitos

Para rodar este projeto, você precisará de um ambiente Linux (ou WSL no Windows) com **Python 3.12** instalado.

Todo o gerenciamento de dependências é feito através do **Poetry**, garantindo um ambiente determinístico e isolado. O processamento da IA é feito de forma local e offline utilizando o motor **Ollama**.

## 🚀 Guia de Instalação Passo a Passo

### 1. Instalando o Gerenciador de Pacotes Python (pipx)

O `pipx` é utilizado para instalar o Poetry de forma global e segura, sem quebrar os pacotes do sistema operacional. No terminal, execute:

```bash
sudo apt update
sudo apt install pipx
```

### 2. Instalando o Poetry
Com o `pipx` pronto, instale o gerenciador de dependências Poetry:

```bash
pipx install poetry
pipx ensurepath
```

**Atenção:** Após rodar este comando, pode ser necessário reiniciar o terminal ou rodar `source ~/.bashrc` para que o comando `poetry` seja reconhecido.

### 3. Instalando as Dependências do Projeto

Na raiz do projeto (onde está o arquivo `pyproject.toml`), crie o ambiente virtual e instale as bibliotecas (`networkx`, `pydantic`, `ollama`, `json-repair`, etc.) rodando:

```bash
poetry install
```

### 4. Configurando a Inteligência Artificial Local (Ollama)

O projeto utiliza a LLM Mistral. O modelo escolhido possui quantização de 4 bits (`mistral:7b-instruct-v0.3-q4_K_M`). Essa otimização permite que ele rode de forma extremamente rápida, exigindo a partir de 6GB de VRAM, mas escalando perfeitamente para utilizar o poder de fogo e a memória de placas de vídeo dedicadas mais potentes.

Primeiro, instale o motor do Ollama e suas dependências:

```bash
sudo apt-get install zstd
curl -fsSL https://ollama.com/install.sh | sh
```
Depois, baixe os pesos do modelo específico utilizado no código:

```bash
ollama pull mistral:7b-instruct-v0.3-q4_K_M
```

---

## 💻 Como Executar o Pipeline

O processo de construção do Grafo de Conhecimento é dividido em duas etapas sequenciais.

Antes de iniciar, ative o ambiente virtual para ter o Python e o pacote de dependências disponíveis nativamente na sua sessão atual do terminal:

```bash
source $(poetry env info --path)/bin/activate
```

*(Para sair do ambiente virtual após o uso, basta digitar `deactivate`).*

### Etapa 1: Extração Bruta e Construção do Grafo

A primeira etapa realiza a leitura dos arquivos de texto e aciona a LLM para extrair as ontologias (entidades e relações), construindo o grafo inicial.

```bash
python src/create_graph_knowledge.py

```

Isso irá gerar o arquivo base de dados em `data/knowledge_graph_hk.json`.

### Etapa 2: Limpeza e Deduplicação em Massa

Grafos gerados por IA costumam conter entidades duplicadas (ex: variações de letras maiúsculas/minúsculas, aliases). Para resolver isso sem sobrecarregar o hardware, a segunda etapa aplica um pré-filtro algorítmico rápido seguido de uma análise refinada por IA em lotes.

```bash
python src/remove_knowledge_graph_duplicates.py
```

**Recurso de Checkpoint:**
A análise em lote pela IA é intensiva. O script de deduplicação possui um sistema de salvamento automático (`data/dedup_checkpoint.json`). Caso você precise interromper o processo (pressionando `Ctrl+C`) ou ocorra alguma queda de energia, basta executar o script novamente. Ele pulará os lotes já processados e continuará exatamente de onde parou.

Ao final desta etapa, o grafo consolidado e limpo será salvo como `data/knowledge_graph_hk_clean.json`.