# Sprint 1 — Fundação: Design

Data: 2026-08-09
Status: aguardando revisão

## Objetivo

Ter o esqueleto do projeto rodando em Docker, o banco modelado (os 5 models do
domínio) e uma chamada real à API da TMDb funcionando no backend. Sem UI —
este sprint é só o alicerce (Django + DRF + PostgreSQL).

## Escopo e decisões

Decisões tomadas nesta sessão de brainstorming, com a razão de cada uma:

| Decisão | Escolha | Por quê |
|---|---|---|
| Modo de reserva | Pista (quantidade), não mapa de assentos | Plano recomenda explicitamente pista primeiro; assentos é opcional só se sobrar tempo. Reduz risco de não fechar o fluxo ponta a ponta até o Dia 5. |
| API externa | TMDb (filmes) | Mais simples de integrar que Ticketmaster, conforme o próprio plano. |
| Papéis de usuário | Campo `role` (choices) no Custom User Model | 3 papéis fixos e mutuamente exclusivos por usuário — não precisa da flexibilidade de Groups. |
| Frontend build | Vite + React | Setup rápido, sem overhead de SSR que não será usado (SPA autenticada). Entra no Sprint 2, não neste sprint. |
| Deps Python | pip + requirements.txt | Zero fricção dentro do container Docker; padrão simples, sem necessidade da camada extra de um gerenciador como Poetry para este escopo. |
| Apps Django | `users`, `events`, `reservations` (3 apps separados) | Cada um com responsabilidade de domínio clara. |
| Timing dos models | Os 5 models (User, Event, Reservation, Ticket, Payment) criados já no Dia 1 | O próprio plano descreve a modelagem completa como tarefa do Dia 1 ("o coração do projeto"); evita migrations fragmentadas nos dias seguintes. |
| Docker Compose (Dia 1) | Só `web` + `db`; `front` entra no Dia 2 | Este sprint é "nada de UI ainda" — um serviço `front` vazio hoje não agrega nada. |
| Nome do projeto Django | `core` | Já scaffolded via `django-admin startproject core` antes desta sessão (commit `a7941b7`); mantido em vez do `config` inicialmente sugerido. |
| `Seat`/setor | Fora do escopo | YAGNI — só entra se o modo assentos virar opcional mais adiante (Dia 3/6). |

## Estrutura de diretórios

```
plataforma-eventos/
├── backend/
│   ├── core/              # projeto Django (settings, urls, wsgi/asgi) — já existe
│   ├── manage.py          # já existe
│   ├── users/              # app: Custom User Model
│   ├── events/             # app: Event, client TMDb
│   ├── reservations/       # app: Reservation, Ticket, Payment
│   └── requirements.txt
├── frontend/                # scaffold vazio neste sprint (populado no Sprint 2)
├── docker-compose.yml       # web + db
├── .env.example
├── .gitignore                # já existe (commit a7941b7)
└── README.md                 # inicial, com enunciado resumido
```

## Modelagem de dados

**`users.User`** (extends `AbstractUser`)
- `role`: `CharField` com `choices` — `organizador` / `cliente` / `portaria`

**`events.Event`**
- `title`, `description`, `date`, `location`, `capacity`, `price`
- `organizer`: FK → `User` (esperado `role=organizador`, validado na camada de permissão no Sprint 2)
- `external_ref`: id do filme na TMDb
- `external_title`, `poster_path`: cache dos dados da TMDb (evita depender da API em toda listagem)
- `is_published`: bool, default `False`
- Sem campo de "tipo pista/assentos" — modo pista é o único suportado por ora (ver tabela de decisões)

**`reservations.Reservation`**
- `customer`: FK → `User`
- `event`: FK → `Event`
- `quantity`: inteiro positivo
- `status`: choices — `pendente` / `paga` / `recusada` / `cancelada`

**`reservations.Ticket`**
- `reservation`: FK one-to-one → `Reservation`
- `code`: token opaco (UUID)
- `signature`: assinatura HMAC (lógica real implementada no Sprint 4; campo existe desde já)
- `used_at`: `DateTimeField(null=True)`
- `share_token`: usado no Sprint 6 para compartilhamento público

**`reservations.Payment`**
- `reservation`: FK → `Reservation`
- `status`: choices — pendente/confirmado/recusado
- `amount`: decimal

Todos os models registrados no Django Admin com `list_display` básico para
inspeção manual.

## Docker Compose

- **`web`**: build de `backend/Dockerfile` (Python 3.11-slim), monta o código
  como volume, roda `manage.py runserver 0.0.0.0:8000` via entrypoint,
  healthcheck HTTP em `/admin/`.
- **`db`**: `postgres:15`, volume nomeado para persistência de dados,
  healthcheck `pg_isready`.
- `web` depende de `db` com `condition: service_healthy`.
- Variáveis sensíveis (`SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
  `DB_HOST`, `DB_PORT`, `TMDB_API_KEY`) lidas de `.env`; `.env.example`
  versionado como referência, `.env` já coberto pelo `.gitignore`.
- `settings.py` passa a ler `DATABASES` do Postgres via variáveis de ambiente
  (troca do SQLite padrão do scaffold atual) e adiciona `rest_framework` a
  `INSTALLED_APPS`.

## Dependências (`requirements.txt`)

- `Django`, `djangorestframework` — framework e API
- `psycopg2-binary` — driver PostgreSQL
- `requests` — chamadas HTTP à TMDb
- `python-dotenv` — carregar `.env` em desenvolvimento
- `django-cors-headers` — necessário a partir do Sprint 2 quando o frontend
  (porta separada) passa a consumir a API; incluído já aqui para não
  fragmentar o requirements.txt entre sprints
- `pytest`, `pytest-django` — suíte de testes
- `responses` — mock de chamadas HTTP nos testes do client TMDb

## Integração TMDb

- Client simples em `events/tmdb_client.py`, usando `requests`, autenticado
  com `TMDB_API_KEY` do `.env`.
- Endpoint interno `GET /api/events/catalog/` — autenticado (organizador,
  ainda sem enforcement de papel neste sprint — isso é Sprint 2), chama o
  endpoint `discover/movie` (ou `movie/now_playing`) da TMDb e devolve
  título, poster, id externo, sinopse.
- Este é o catálogo que o organizador usa no Sprint 2 para criar um `Event`.
- Sem cache/persistência intermediária neste sprint — só confirma que a
  chamada funciona e retorna dados reais.

## Definition of Done

- [ ] `docker compose up` sobe `web` + `db` sem erro, healthchecks verdes.
- [ ] `python manage.py migrate` aplicado; os 5 models visíveis no Django Admin.
- [ ] Chamada real à TMDb (via endpoint ou shell) retornando filmes reais.
- [ ] Suíte `pytest` cobrindo os 5 models e o `tmdb_client` passando localmente.
- [ ] Workflow de CI (`backend-ci.yml`) passando no GitHub Actions.
- [ ] README inicial: enunciado resumido, estrutura do repo, como subir o
      ambiente.
- [ ] Commit: `feat: modelagem inicial, docker e integração TMDb`.

## Fora de escopo (adiado)

- UI/frontend funcional (Sprint 2 em diante).
- Enforcement de permissões por papel (Sprint 2).
- Lógica de HMAC/QR real no `Ticket` (Sprint 4).
- Lógica de anti-venda-dupla (Sprint 3).
- Modo de reserva por assentos (`Seat`) — só se sobrar tempo, opcional.

## Testes unitários

Mesmo sem lógica de negócio complexa neste sprint, a fundação já entra com
suíte de testes para não acumular dívida até o Sprint 3 (onde os testes de
concorrência dependem dessa base já existir):

- `users/tests.py`: criação de `User` com cada `role`; valor de `role`
  inválido é rejeitado.
- `events/tests.py`: criação de `Event` com campos obrigatórios; teste do
  `tmdb_client` com a chamada HTTP mockada (`unittest.mock` ou
  `responses`), verificando parsing da resposta sem depender da API real.
- `reservations/tests.py`: criação de `Reservation`, `Ticket`, `Payment` e
  suas relações (FKs, one-to-one do `Ticket`).

Framework: `pytest` + `pytest-django` (mais conciso que `TestCase` puro do
Django e já pensando no Sprint 3, onde testes de transação/concorrência se
beneficiam de fixtures do pytest).

## CI/CD

GitHub Actions, workflow `.github/workflows/backend-ci.yml`, disparado em
push e pull request para `main`:

1. Sobe um serviço `postgres:15` (service container do próprio Actions).
2. Instala dependências (`pip install -r backend/requirements.txt`).
3. Roda `python manage.py migrate --check` (garante que não há migration
   pendente não gerada).
4. Roda a suíte `pytest`.

Falha em qualquer etapa quebra o check do PR/push. Ampliar o workflow (lint,
build do frontend, etc.) fica para os sprints em que esses componentes
existirem.
