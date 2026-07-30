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