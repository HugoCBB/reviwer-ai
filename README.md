# Reviewer AI

Bot de revisão automática de Pull Requests usando múltiplos agentes de IA. Quando um PR é aberto ou atualizado, o bot busca o diff, roda agentes especializados em paralelo e posta um review detalhado no GitHub.

## Arquitetura

```
GitHub Webhook → FastAPI → Celery Task → LangGraph
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                   ▼                   ▼
                     Security Agent      Quality Agent       Tests Agent
                          │                   │                   │
                          └───────────────────┼───────────────────┘
                                              ▼
                                        Docs Agent
                                              │
                                              ▼
                                      Aggregator Agent
                                              │
                                              ▼
                                    GitHub PR Review
```

### Agentes

| Agente | Responsabilidade |
|---|---|
| **Security** | Vulnerabilidades OWASP, injeções, segredos expostos |
| **Quality** | Complexidade, duplicação, naming, SOLID |
| **Tests** | Cobertura de testes, casos de borda não testados |
| **Docs** | Docstrings, type hints, comentários |
| **Aggregator** | Consolida todos os findings em um review final |

## Stack

- **FastAPI** — recebe webhooks do GitHub
- **Celery + Redis** — fila de tarefas assíncronas
- **LangGraph** — orquestração dos agentes
- **LLM** — DeepSeek, Gemini ou Ollama (configurável)
- **ngrok** — túnel para expor a API localmente

## Configuração

### 1. Clone e configure o `.env`

```bash
cp .env.example .env
```

Preencha o `.env`:

```env
# GitHub
GITHUB_TOKEN=ghp_...          # Personal Access Token com scope "repo"
GITHUB_SECRET=seu-secret      # String aleatória usada no webhook

# LLM — escolha um provider
LLM_PROVIDER=deepseek         # deepseek | gemini | ollama

# DeepSeek (recomendado — sem limite diário)
DEEPSEEK_API_KEY=sk-...

# Gemini (alternativa)
GOOGLE_API_KEY=AIza...

# Ollama (local, sem custo)
# OLLAMA_MODEL=llama3.1

# ngrok
NGROK_AUTHTOKEN=...
```

### 2. Suba os containers

```bash
docker compose up --build
```

Na primeira execução com Ollama, aguarde o download do modelo (~4.7 GB).

### 3. Pegue a URL do ngrok

Acesse `http://localhost:4040` e copie a URL gerada (ex: `https://abc123.ngrok-free.app`).

### 4. Configure o webhook no GitHub

No seu repositório: **Settings → Webhooks → Add webhook**

| Campo | Valor |
|---|---|
| Payload URL | `https://abc123.ngrok-free.app/webhook/github` |
| Content type | `application/json` |
| Secret | valor do `GITHUB_SECRET` no `.env` |
| Events | Pull requests |

### 5. Abra um PR e veja o bot revisar

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/webhook/github` | Recebe eventos do GitHub |
| `GET` | `/health` | Health check |

## Monitoramento

```bash
# Logs da API
docker compose logs api -f

# Logs do worker (tasks Celery)
docker compose logs worker -f

# Flower — dashboard do Celery
http://localhost:5555

# ngrok — dashboard de requests
http://localhost:4040
```

## Providers LLM

| Provider | `LLM_PROVIDER` | Variável necessária | Limite free |
|---|---|---|---|
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | Sem limite diário |
| Gemini | `gemini` | `GOOGLE_API_KEY` | 1500 req/dia (2.0-flash) |
| Ollama | `ollama` | — | Sem limite (local) |

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `GITHUB_TOKEN` | — | PAT com scope `repo` |
| `GITHUB_SECRET` | — | Secret do webhook |
| `LLM_PROVIDER` | `ollama` | Provider de LLM |
| `DEEPSEEK_API_KEY` | — | Chave da API DeepSeek |
| `GOOGLE_API_KEY` | — | Chave da API Google |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Modelo DeepSeek |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Modelo Gemini |
| `OLLAMA_MODEL` | `llama3.1` | Modelo Ollama |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL do Ollama |
| `REDIS_URL` | `redis://redis:6379/0` | URL do Redis |
| `NGROK_AUTHTOKEN` | — | Token do ngrok |
