# Plataforma de Eventos e Ingressos

Plataforma web para publicação de eventos, reserva/compra de ingressos com controle de vagas sob concorrência, pagamento (Stripe) e check-in na portaria via QR Code.

- **Deploy:** frontend na Vercel, backend + PostgreSQL no Render.
- **Stack:** Django 5 + Django REST Framework (backend), React + TypeScript + Vite (frontend), PostgreSQL, Docker Compose (dev local).

## Sumário

- [Funcionalidades](#funcionalidades)
- [Documentação da API (Swagger)](#documentação-da-api-swagger)
- [Como rodar localmente](#como-rodar-localmente)
- [Credenciais de teste (seed)](#credenciais-de-teste-seed)
- [Testes](#testes)
- [Decisões técnicas](#decisões-técnicas)
- [Deploy](#deploy)
- [Limitações conhecidas](#limitações-conhecidas)
- [Uso de IA neste projeto](#uso-de-ia-neste-projeto)

## Funcionalidades

Três papéis de usuário (`role`), cada um com sua própria visão:

| Papel | O que faz |
|---|---|
| **Cliente** | Navega o catálogo público de eventos (paginado, com busca/filtros), reserva N ingressos por evento, paga (fluxo de pagamento simulado, com integração real de Stripe Checkout implementada no código mas não validada em produção), recebe um QR Code assinado por ingresso, acompanha "Minhas Reservas" com contagem regressiva de expiração, compartilha um ingresso via link público. |
| **Organizador** | Cria e edita seus próprios eventos (título, descrição, data, local, capacidade, preço), usando dados de filmes em cartaz da TMDb como base de conteúdo. |
| **Portaria** | Escaneia (câmera) ou digita um código curto para validar ingressos na entrada do evento, com contador de check-in em tempo real. |

Autenticação via JWT em cookies `httpOnly` (não em `localStorage`, para reduzir superfície de XSS), com CSRF habilitado nas rotas mutáveis.

## Documentação da API (Swagger)

Toda a API é documentada via OpenAPI 3 ([drf-spectacular](https://drf-spectacular.readthedocs.io/)), gerada a partir do código (schema, permissões e serializers reais — não escrita à mão):

- **Swagger UI:** `/api/docs/` — interativo, dá pra chamar os endpoints direto pelo navegador (autenticando via `/api/v1/auth/login/`, que seta o cookie).
- **Redoc:** `/api/redoc/` — leitura mais confortável para navegar a referência completa.
- **Schema bruto:** `/api/schema/` (YAML).

Local: `http://localhost:8000/api/docs/`. Em produção: `<url-do-backend-no-render>/api/docs/`.

## Como rodar localmente

Pré-requisitos: Docker e Docker Compose, Node 20+.

```bash
# 1. Clonar e configurar variáveis de ambiente do backend
git clone git@github.com:Rafael-Casemiro/plataforma-eventos.git
cd plataforma-eventos
cp .env.example .env
# edite .env e informe pelo menos SECRET_KEY e TMDB_API_KEY
# (chave gratuita em https://www.themoviedb.org/settings/api)

# 2. Subir backend + banco (migrations rodam automaticamente ao iniciar)
docker compose up -d --build

# 3. Popular o banco com usuários, eventos e reservas de demonstração
docker compose exec web python manage.py seed

# 4. Configurar e rodar o frontend
cd frontend
cp .env.example .env
npm install
npm run dev
```

- Backend disponível em `http://localhost:8000` (API em `/api/v1/`, admin em `/admin/`).
- Frontend disponível em `http://localhost:5173`.

### Configuração do banco

O PostgreSQL sobe via Docker Compose (serviço `db`), com dados persistidos em volume nomeado (`db_data`). Credenciais e nome do banco vêm de `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` no `.env`; o backend se conecta usando `DATABASE_URL` (formato `postgresql://user:senha@db:5432/nome`). Migrations rodam automaticamente no `CMD` do container `web` a cada start — não é preciso rodar `migrate` manualmente em dev.

### Comando de seed

`python manage.py seed` é idempotente: remove e recria (por e-mail) os usuários de demonstração, busca filmes em cartaz na TMDb para gerar ~6 eventos, e cria reservas cobrindo os principais estados (`pendente`, `paga` — com ingresso assinado gerado de verdade —, `recusada`, `cancelada`). Pode ser rodado quantas vezes forem necessárias sem duplicar dados. Requer `TMDB_API_KEY` válida.

## Credenciais de teste (seed)

Todas as senhas: `senha123`

| Papel | E-mail | Observação |
|---|---|---|
| Organizador | `organizador1.seed@example.com` | Um segundo organizador também é criado (`organizador2.seed@example.com`) |
| Cliente | `cliente1.seed@example.com` | Mais dois clientes também são criados (`cliente2`, `cliente3`) |
| Portaria | `portaria1.seed@example.com` | — |
| Admin (Django admin) | criar com `docker compose exec web python manage.py createsuperuser` | Não faz parte do seed |

## Testes

```bash
docker compose exec web pytest
```

92 testes cobrindo modelos, serializers e API, incluindo um teste de concorrência real (`ThreadPoolExecutor` + `django_db(transaction=True)`) que prova que o lock de capacidade impede overselling sob requisições simultâneas — não apenas que o código "parece" correto. CI (GitHub Actions) roda essa mesma suíte a cada push/PR em `main`.

## Decisões técnicas

Registro do "porquê", não só do "o quê" — inclui o que foi cogitado e descartado. Specs completas de cada sprint (com discussão de trade-offs) estão versionadas em [`docs/superpowers/specs/`](docs/superpowers/specs/).

**Reserva por pista (quantidade), não por assento.** Modelar seleção de assento individual (mapa de lugares) adiciona uma dimensão inteira de complexidade — layout do venue, bloqueio por cadeira, renderização de mapa — sem mudar o problema central que o projeto avalia: concorrência e não-overselling. Pista reduz o escopo ao que importa e garante fechar o fluxo ponta a ponta.

**Anti-venda-dupla resolvido no banco, não na aplicação.** A garantia de que a soma de reservas ativas nunca ultrapassa `Event.capacity` vem de `select_for_update()` (lock pessimista na linha do `Event`) somado a uma agregação recalculada a cada tentativa de reserva — nunca um contador `capacity_available` denormalizado. Um contador seria mais rápido sob alta concorrência, mas exigiria mantê-lo sincronizado manualmente em toda transição de status (cancelamento, expiração, confirmação de pagamento), criando mais um lugar para divergir da realidade. Descartado por complexidade desnecessária para o escopo do projeto. A mesma trava reaparece na confirmação de pagamento assíncrona (webhook Stripe), porque o webhook pode chegar tarde ou ser reentregue — sem o lock e uma checagem explícita de expiração ali, uma confirmação tardia/duplicada furava a garantia estabelecida na criação da reserva.

**Expiração preguiçosa, sem worker/cron.** `expires_at` é a fonte de verdade para os cálculos de capacidade (uma reserva pendente vencida simplesmente para de contar); o campo `status` só é fisicamente virado para `cancelada` quando a reserva é lida/tocada individualmente. Evita introduzir um processo em background (Celery, cron) só para essa finalidade — trade-off aceito: o `status` armazenado pode ficar "desatualizado" até a próxima leitura, mas isso nunca afeta a matemática de disponibilidade.

**QR Code assinado (HMAC-SHA256), não um UUID aleatório.** Cada ingresso guarda `code` (UUID) e `signature = HMAC-SHA256(SECRET_KEY, "code:event_id")`; o QR codifica `code.signature`. Isso impede forjar um ingresso válido só adivinhando/gerando um UUID — sem a `SECRET_KEY` do servidor não dá pra produzir uma assinatura que bata. A validação usa `hmac.compare_digest` (tempo constante) para não vazar informação por timing attack. Também existe um código curto alfanumérico (10 caracteres, alfabeto sem caracteres ambíguos) para entrada manual quando a câmera da portaria falha.

**Um ingresso por unidade de quantidade, não um ingresso por reserva.** Uma reserva de 3 ingressos gera 3 registros de `Ticket` (FK, não `OneToOne`), cada um com seu próprio QR/código curto e validado/consumido independentemente. Alternativa descartada: um único QR por reserva — mais simples, mas não permite que um grupo entre em horários diferentes ou que cada pessoa carregue seu próprio ingresso.

## Deploy

**Backend + banco (Render):** `render.yaml` na raiz do repo já descreve o serviço web (Python nativo, `gunicorn`) e o banco Postgres gerenciado — no dashboard do Render, use "New > Blueprint" apontando para este repositório e ele lê o `render.yaml` automaticamente. Depois de criado, defina manualmente as env vars marcadas `sync: false`: `ALLOWED_HOSTS` (domínio `.onrender.com` gerado), `CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS`/`FRONTEND_URL` (domínio da Vercel), `TMDB_API_KEY`, e opcionalmente `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`. Rodar o seed em produção: aba **Shell** do serviço no Render, `python manage.py seed`.

**Frontend (Vercel):** importe o repositório na Vercel com **Root Directory = `frontend`** (framework Vite é detectado automaticamente). Defina a env var `VITE_API_URL` apontando para a URL pública do backend no Render (`https://<seu-servico>.onrender.com/api/v1`). O `vercel.json` já inclui o rewrite necessário para as rotas do React Router funcionarem em acesso direto/refresh.

**Por que domínios diferentes exigem atenção extra:** a autenticação usa cookies `httpOnly`, e como frontend e backend ficam em domínios diferentes em produção, os cookies precisam de `SameSite=None; Secure` para serem enviados em requisições cross-site (em dev, mesmo host, `SameSite=Lax` já basta) — essa troca é automática via `settings.COOKIE_SAMESITE`, condicionada a `DEBUG=False`.

## Limitações conhecidas

- **Cold start no Render (plano free):** o serviço web hiberna após um período sem tráfego; a primeira requisição depois disso pode levar 30–60s para responder. Requisições seguintes voltam ao normal.
- **Pagamento é simulado.** O fluxo de pagamento usado (inclusive no ambiente publicado) é via parâmetro `simulate=success|fail|stripe`, sem depender de credenciais externas. O código tem uma integração real com `stripe.checkout.Session` e verificação de assinatura de webhook, mas ela não foi validada rodando em produção (exigiria `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` reais e o webhook registrado manualmente no dashboard da Stripe).
- **Sem verificação de e-mail no cadastro** — o projeto já tem login funcional via usuários de seed, e configurar um provedor de e-mail transacional (ex.: Brevo, já que o Render bloqueia SMTP na porta 587 nos planos gratuitos) não agregava ao que está sendo avaliado aqui. Cadastro cria a conta e autentica na hora.
- **Sem seleção de assento** — decisão deliberada, ver seção de decisões acima.

## Uso de IA neste projeto

Ferramenta: **Claude Code** (Anthropic), usada de forma deliberadamente desigual entre backend e frontend:

- **Backend:** escrito por mim. IA usada como par de design (discussão de abordagens antes de implementar) e revisão de código — encontrar e confirmar bugs reais, sempre validados empiricamente (`docker compose exec`, `pytest`, `curl`) antes de aceitar qualquer diagnóstico. Assim foram encontrados e corrigidos, por exemplo: falta de checagem de expiração na confirmação de pagamento (webhook tardio/duplicado furando a garantia de não-overselling), permissão errada no endpoint de validação de ingresso, e um vazamento de informação sobre eventos não publicados.
- **Frontend:** misto. Eu implementei partes da interface diretamente (por exemplo a tela de login e o sistema visual — paleta de cores, tipografia); a IA implementou a maior parte das páginas, componentes, integrações com a API e correções de UX sobre essa base, sempre com decisões validadas comigo antes de codar.
- **Processo:** cada funcionalidade não trivial passou por um ciclo spec → aprovação → implementação. As specs de cada sprint estão versionadas em [`docs/superpowers/specs/`](docs/superpowers/specs/) e documentam alternativas consideradas e descartadas, não só a decisão final.






