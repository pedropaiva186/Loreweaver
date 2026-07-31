# Trabalho III - Grafo de Conhecimento com Inteligência Artificial

Este projeto implementa a geração e manipulação de um Grafo de Conhecimento (utilizando `networkx`) em conjunto com um modelo de Inteligência Artificial rodando localmente.

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

```Bash
pipx install poetry
pipx ensurepath
```

Atenção: Após rodar este comando, pode ser necessário reiniciar o terminal ou rodar `source ~/.bashrc` para que o comando poetry seja reconhecido.

### 3. Instalando as Dependências do Projeto
Na raiz do projeto (onde está o arquivo `pyproject.toml`), crie o ambiente virtual e instale as bibliotecas (como `networkx`, `pydantic` e o cliente `ollama`) rodando:

```Bash
poetry install
```

### 4. Configurando a Inteligência Artificial Local (Ollama)
O projeto utiliza a LLM Mistral. O modelo escolhido possui quantização de 4 bits (`mistral:7b-instruct-v0.3-q4_K_M`), o que significa que ele foi otimizado para rodar de forma extremamente rápida, cabendo perfeitamente na memória dedicada de placas de vídeo com 6GB de VRAM, sem sobrecarregar a memória RAM principal do computador.

Primeiro, instale o motor do Ollama no seu sistema (se ainda não tiver):

```Bash
sudo apt-get install zstdsudo apt-get install zstd
curl -fsSL https://ollama.com/install.sh | sh
```
Depois, baixe os pesos do modelo específico utilizado no código:

```Bash
ollama pull mistral:7b-instruct-v0.3-q4_K_M
```

# 💻 Como Executar
Com todo o ambiente preparado, você tem duas opções para rodar o script principal que gera o grafo de conhecimento:

**Opção A (Execução direta):**
Executar o arquivo Python passando o comando através do Poetry:

```Bash
poetry run python create_graph_knowledge.py
```

**Opção B (Entrando no ambiente isolado):**
Caso queira ativar o ambiente virtual para ter o Python e o pip do projeto disponíveis nativamente na sua sessão atual do terminal, rode:

```Bash
source $(poetry env info --path)/bin/activate
```
Após ativado (o nome do projeto aparecerá no início da linha do terminal), você pode rodar normalmente:

```Bash
python src/create_graph_knowledge.py
```
(Para sair do ambiente virtual depois, basta digitar deactivate).
