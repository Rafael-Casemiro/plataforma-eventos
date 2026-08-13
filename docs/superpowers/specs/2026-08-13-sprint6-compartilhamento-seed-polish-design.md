# Sprint 6 — Compartilhamento, Seed e Polish

## Contexto

Sprint 6 do plano de 7 sprints do projeto. Três frentes independentes: uma página pública de ingresso compartilhável (usando o campo `share_token` do `Ticket`, existente desde o Sprint 1 mas nunca usado), um script de seed para popular o banco com dados de demonstração, e três itens de polimento identificados a partir de exemplos de referência de outros projetos do mesmo desafio.

## Compartilhamento

### Endpoint

`GET /api/v1/reservations/share/<share_token>/` — público (`AllowAny`). Busca o `Ticket` pelo `share_token`.

- `200` com dados do evento: `title`, `date`, `location`, `poster_path`, e `quantity` da reserva associada.
- `404` se o `share_token` não existir.
- **Nunca** inclui `code`, `signature` (o token que valida a entrada) nem qualquer dado do cliente (nome, email) — o link pode ser compartilhado com qualquer pessoa sem risco de vazar o ingresso de verdade ou identificar quem vai ao evento.

### Frontend

Rota pública `/ingresso/<share_token>` (fora do `ProtectedRoute`, sem exigir login) — card simples mostrando os dados acima, sem nenhuma ação disponível (não é possível reservar, editar ou repetir a compra a partir dessa página, é só uma vitrine).

Em `MinhasReservas.tsx`, ao lado do QR code de um ingresso pago, um botão "Copiar link para compartilhar" que monta a URL `/ingresso/<share_token>` e copia pra área de transferência.

## Script de Seed

Management command `python manage.py seed`, em `backend/core/management/commands/seed.py`.

**Idempotente**: no início, apaga qualquer usuário com os emails fixos de seed (e, em cascata, seus eventos e reservas) antes de recriar — pode ser rodado quantas vezes for preciso sem acumular lixo.

**Conteúdo:**
- 2 organizadores, 3 clientes, 1 portaria, todos com senha `senha123` (mesma senha usada nos testes automatizados) e emails previsíveis (ex: `organizador1.seed@example.com`).
- ~6 eventos, buscados ao vivo via `events.tmdb_client.buscar_filmes_em_cartaz()`, divididos entre os 2 organizadores. A maioria `is_published=True`; um ou dois como rascunho, para demonstrar a diferença entre a listagem pública e "meus eventos".
- Reservas cobrindo os 4 estados possíveis:
  - `pendente` — criada normalmente, ainda dentro dos 15 minutos.
  - `paga` — criada e depois confirmada chamando `reservations.views.confirm_payment_and_generate_ticket()` diretamente, para que o `Ticket` gerado tenha uma assinatura HMAC genuinamente válida (permite testar a validação de portaria de verdade com esse ingresso, em vez de um ticket fabricado à mão que falharia a validação).
  - `recusada` — reserva + `Payment` com `status=recusado`.
  - `cancelada`.
- Ao final, o comando imprime no terminal os emails e senha dos usuários criados (não há README ainda documentando isso).

## Polish

### 1. Restringir `/portaria` no frontend

`App.tsx` hoje libera a rota `/portaria` para `allowedRoles={['organizador', 'cliente']}`. Deveria ser só `allowedRoles={['portaria']}` — mesma correção já aplicada no backend (`IsPortaria` em vez de `IsAuthenticated` no endpoint `validate-ticket/`), agora espelhada no guard de rota do frontend.

### 2. Badge de esgotado + card de evento mais rico

Isso tem uma parte de backend, não é só CSS: `GET /api/v1/events/` (listagem pública) hoje não expõe quantas vagas restam por evento. A view precisa anotar cada evento com a soma de reservas ativas (mesmo critério já usado na criação de reserva — `status=paga` OU `status=pendente` com `expires_at` no futuro) e calcular `vagas_disponiveis = capacity - reservado`.

No frontend, o card de evento passa a mostrar um selo "Esgotado" sobreposto quando `vagas_disponiveis <= 0`, ou "Restam N" caso contrário.

Fora de escopo: o conceito de "sessões disponíveis" (múltiplos horários por filme) das referências não se aplica ao modelo atual — cada `Event` tem uma única `date`, não uma lista de sessões. Não será replicado.

### 3. Contador regressivo de expiração

Em `MinhasReservas.tsx`, o texto estático "Expira em: HH:MM:SS" (horário fixo formatado) vira uma contagem regressiva viva (mm:ss restantes), atualizando a cada segundo via `setInterval`. Ao chegar em zero, mostra "Expirado" e refaz a busca de `/reservations/mine/` para refletir o estado real (a reserva só é oficialmente cancelada no backend quando algo a lê — ver [[2026-08-13-sprint3-reservas-concorrencia-design]] sobre expiração preguiçosa).

## Fora de escopo deste sprint

- README (Sprint 7).
- Deploy (Sprint 7).
- Múltiplas sessões/horários por evento (mudança de modelo, não é polish).
- Notificação/lembrete de expiração (ex: alerta sonoro, push) — só o contador visual.
