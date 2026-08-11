# Sprint 2 — Autenticação e Eventos: Design

Data: 2026-08-11
Status: aguardando revisão

## Objetivo

Os três papéis (organizador, cliente, portaria) autenticados via JWT, com
permissões reais no DRF, e o organizador conseguindo publicar um evento a
partir do catálogo da TMDb — visível na listagem pública. Primeiras telas do
frontend (login, painel do organizador, listagem pública), já com a
identidade visual definitiva do projeto.

## Escopo e decisões

| Decisão | Escolha | Por quê |
|---|---|---|
| Registro público | Só cria `role=cliente`; campo `role` no payload é ignorado | Organizador/portaria continuam sendo criados só pelo Admin (decisão do Sprint 1) — autocadastro público desses papéis não faz sentido de negócio. |
| Armazenamento do token | Cookie `httpOnly` (não `localStorage`) | Mais seguro contra XSS. Custo aceito conscientemente: view de login customizada, CSRF nas rotas de escrita, CORS com credentials. |
| Refresh token | Sem rotação/blacklist — access curto (15min) + refresh mais longo (7 dias) | Escopo do desafio não justifica a infra extra (app `token_blacklist` + migration) que a rotação exigiria. |
| Publicar/despublicar evento | `PATCH` no evento (`is_published`) | Reaproveita o endpoint de edição padrão do `ModelViewSet`, sem rota extra só pra alternar um bool. |
| Filtros da listagem pública | Busca textual (`search`) + data exata + faixa de preço | Cobre o que o plano pede sem inventar filtros que ninguém pediu. |
| Bibliotecas do frontend | `react-router-dom` + `axios` | Axios facilita mandar `withCredentials` e interceptar 401 pra refresh automático — relevante justamente por causa do cookie httpOnly. |
| Estado de autenticação | Context API do React | Nativo, sem dependência extra; suficiente pra 3 telas com um estado de auth simples. |
| Identidade visual | "Ticket Moderno" — fundo claro, vermelho vibrante (`#d8432e`) como cor única de destaque, títulos em Space Grotesk, motivo de canhoto de ingresso nos cards | Escolhida via comparação visual (3 direções) durante o brainstorming; foge do "AI slop" que o desafio penaliza. |
| Testes de frontend | Fora de escopo neste sprint | Não está pedido no plano; verificação manual no navegador é suficiente por ora. |

## Backend — Autenticação (JWT via cookie httpOnly)

Base: `djangorestframework-simplejwt`, mas com fluxo customizado — o
`TokenObtainPairView` padrão devolve os tokens no corpo da resposta; aqui
eles vão para cookies `httpOnly`.

**Endpoints** (views dentro do app `users` — login/registro/refresh/logout
são todos sobre o `User`; não justifica um app novo só pra isso):

- `POST /api/v1/auth/login/` — valida email/senha, seta cookies `access` e
  `refresh` (`httpOnly`, `secure` em produção, `samesite=Lax`), devolve
  `{"user": {"email", "first_name", "last_name", "role"}}` no corpo (sem o
  token).
- `POST /api/v1/auth/refresh/` — lê o cookie `refresh`, gera novo `access`,
  reseta o cookie. Chamado pelo interceptor do axios ao receber 401.
- `POST /api/v1/auth/logout/` — limpa os cookies `access` e `refresh`.
- `POST /api/v1/auth/registro/` — cria `User` com `role` forçado para
  `CLIENTE`, independente do que vier no payload.
- `GET /api/v1/auth/csrf/` — seta o cookie `csrftoken`; o frontend chama
  isso antes de qualquer POST/PUT/PATCH/DELETE autenticado.

**Autenticação customizada:** subclasse de `JWTAuthentication` que lê o
token do cookie `access` em vez do header `Authorization`.

**CSRF:** rotas de escrita continuam protegidas pelo middleware padrão do
Django (`CsrfViewMiddleware`); o frontend manda o valor do cookie
`csrftoken` no header `X-CSRFToken` (comportamento padrão do Django, sem
lib extra). `CORS_ALLOW_CREDENTIALS = True` e `CORS_ALLOWED_ORIGINS`
explícito (não `*`) em `settings.py`.

## Backend — Permissões por papel

`users/permissions.py`, três classes simples:

```python
class IsOrganizador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ORGANIZADOR

# IsCliente e IsPortaria seguem o mesmo padrão
```

Aplicadas por view (`permission_classes = [IsOrganizador]` no CRUD de
eventos).

## Backend — CRUD de eventos e listagem pública

**`EventViewSet`** (`ModelViewSet`), permissão `IsOrganizador` em tudo
exceto a listagem/detalhe pública:

- `POST /api/v1/events/` — cria a partir de um item do catálogo TMDb
  (`external_ref`, `external_title`, `poster_path` vindos do
  `GET /api/v1/events/catalog/`, já existente desde o Sprint 1); organizador
  define `title`, `description`, `date`, `location`, `capacity`, `price`.
  `organizer` é setado automaticamente para o usuário autenticado — não
  aceito no payload.
- `GET /api/v1/events/meus/` — lista só os eventos do organizador logado.
- `PATCH /api/v1/events/{id}/` — edita campos, incluindo `is_published`.
- `DELETE /api/v1/events/{id}/` — vem de graça do `ModelViewSet`; sem
  requisito específico de negócio neste sprint.

**`GET /api/v1/events/`** (pública, sem autenticação) — só eventos com
`is_published=True`:
- `?search=duna` — busca em `title` (`icontains`, via `SearchFilter` do
  DRF).
- `?date=2026-08-20` — filtro exato de data.
- `?price_min=` / `?price_max=` — faixa de preço (via `django-filter`).

**Serializers separados:**
- `EventCreateSerializer` — campos editáveis pelo organizador.
- `EventPublicSerializer` — somente leitura; expõe só o nome do organizador
  (não email/dados sensíveis).

## Frontend (Vite + React)

**Estrutura:**
```
frontend/
├── src/
│   ├── api/          # cliente axios (baseURL, withCredentials: true,
│   │                  # interceptor de refresh em 401)
│   ├── context/       # AuthContext (usuário, papel, login/logout)
│   ├── pages/          # Login, PainelOrganizador, ListagemPublica
│   ├── components/     # EventoCard, Header, FormularioEvento
│   └── App.jsx         # rotas (react-router-dom), rota protegida por papel
```

**Telas:**
- **Login** (`/entrar`) — formulário email/senha → `POST /auth/login/` →
  guarda usuário no `AuthContext` → redireciona conforme o papel.
- **Painel do organizador** (`/painel`, protegida — só `role=organizador`)
  — lista os próprios eventos (`GET /events/meus/`) + formulário de criação
  (escolhe filme do catálogo, preenche data/local/capacidade/preço).
- **Listagem pública** (`/`) — grid de cards de evento
  (`GET /events/`), com busca e filtros de data/preço.

**Identidade visual — "Ticket Moderno":**
- Fundo claro (`#fdfaf5`), texto escuro (`#1a1a1a`), vermelho vibrante
  (`#d8432e`) como cor única de destaque (botões, links, badges).
- Títulos em **Space Grotesk** (Google Fonts); texto de apoio em sans-serif
  neutra (Inter).
- Cards de evento com motivo de canhoto de ingresso: borda tracejada, badge
  "Ingresso" em uppercase, botão pill vermelho.
- Aplicada de forma consistente nas 3 telas — sem framework de UI genérico
  por cima (Bootstrap/Material).

## Tratamento de erros

Formato padrão de erro do DRF (400 com detalhes de validação, 401/403 de
auth, 404, 502 já tratado pro catálogo TMDb desde o Sprint 1). Sem handler
de exceção customizado neste sprint — polish de mensagens de erro é
explicitamente escopo do Sprint 6 no plano original.

## Testes automatizados (pytest)

- Login: cookies setados corretamente; credenciais erradas → 401.
- Registro: sempre cria `role=cliente`, mesmo enviando outro valor no
  payload.
- Permissões: `IsOrganizador` bloqueia cliente autenticado com 403.
- CRUD de evento: criação a partir de dado do catálogo, edição,
  publicar/despublicar via PATCH.
- Listagem pública: só eventos publicados aparecem; busca e filtros de
  data/preço funcionam.

## Definition of Done

- [ ] Login seta cookies httpOnly e devolve o papel do usuário no corpo da
      resposta.
- [ ] Registro público sempre cria `role=cliente`, mesmo se outro valor for
      enviado.
- [ ] Refresh funciona automaticamente quando o access token expira
      (interceptor do axios).
- [ ] Organizador cria evento a partir de um filme da TMDb e ele aparece na
      listagem pública.
- [ ] Cliente autenticado NÃO consegue acessar rotas de organizador (403).
- [ ] Rotas de escrita protegidas por CSRF.
- [ ] As 3 telas do frontend funcionando com a identidade visual "Ticket
      Moderno".
- [ ] Suíte pytest cobrindo auth, permissões e CRUD de eventos passando.

## Fora de escopo (adiado)

- Rotação/blacklist de refresh token.
- Testes automatizados de frontend.
- Polish de mensagens de erro e estados de loading refinados (Sprint 6).
- Cancelamento de evento, exclusão em cascata de reservas associadas
  (Sprint 3+, quando `Reservation` entra em jogo de verdade).
