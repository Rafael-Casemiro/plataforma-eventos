# Sprint 3 — Reservas e Concorrência

## Contexto

Sprint 3 do plano de 7 sprints do projeto. Reservas são por quantidade ("pista"), não por assento — decisão já travada no Sprint 1. O mecanismo anti-double-sell é a decisão técnica mais importante do projeto: garantir que a soma das reservas ativas de um evento nunca ultrapasse `Event.capacity`, mesmo sob requisições concorrentes.

Os models `Reservation`, `Ticket` e `Payment` já existem desde o Sprint 1 (`backend/reservations/models.py`), mas `reservations/views.py` está vazio e não há `serializers.py`, `urls.py`, nem registro em `core/urls.py` — este sprint parte do zero na camada de API.

`Ticket` e `Payment` estão fora de escopo deste sprint: a geração de ingresso (`Ticket`) só acontece quando um pagamento é confirmado, e pagamento é Sprint 4.

## Mudanças no model `Reservation`

Dois campos novos:

- `expires_at` — `DateTimeField(null=True, blank=True)`. Setado apenas na criação de uma reserva `pendente`, como `agora + 15 minutos`. Não é limpo quando o status muda; simplesmente deixa de ser relevante.
- `created_at` — `DateTimeField(auto_now_add=True)`. Necessário para ordenar "minhas reservas" por mais recente (o model hoje não tem timestamps, diferente de `Event`/`User`).

Nenhuma mudança em `Event`, `Ticket` ou `Payment`.

## Mecanismo anti-double-sell

Dentro de uma transação atômica (`transaction.atomic()`), a criação de reserva segue:

1. `Event.objects.select_for_update().get(pk=event_id, is_published=True)` — trava a linha do evento. Qualquer outra transação tentando reservar o *mesmo* evento bloqueia aqui até esta transação terminar (commit ou rollback).
2. Com a linha travada, soma `quantity` de todas as reservas **ativas** desse evento: `status=paga` OU (`status=pendente` E `expires_at > agora`). Reservas pendentes vencidas não contam para a soma, independente do que o campo `status` ainda diga no banco.
3. Se `soma_ativa + quantity > event.capacity` → falha com 409 (ver seção de erros).
4. Senão, cria a `Reservation` com `status=pendente` e `expires_at=agora + 15min`.

A checagem de capacidade sempre recalcula por agregação no momento — nunca confia em um contador armazenado. É o lock na linha do `Event` que garante que não existe uma janela onde duas transações concorrentes leiam a mesma capacidade disponível e ambas consigam reservar além dela.

**Abordagem descartada:** um campo `capacity_available` denormalizado no `Event`, atualizado via `UPDATE ... WHERE capacity_available >= quantity`. Teria melhor throughput sob alta concorrência, mas exige manter esse contador sincronizado manualmente em toda transição de status (cancelamento, expiração, pagamento) — mais um lugar para divergir da realidade. Descartado por complexidade desnecessária para o escopo do projeto.

## Expiração preguiçosa (lazy expiration)

Não há job, cron ou worker em background. `expires_at` é a fonte da verdade sobre se uma reserva pendente ainda vale — a checagem de capacidade (seção anterior) já ignora reservas pendentes vencidas automaticamente via o filtro `expires_at > agora`, então a capacidade nunca fica presa por uma reserva morta.

O campo `status` no banco só é fisicamente atualizado de `pendente` para `cancelada` quando a reserva é lida individualmente (listagem "minhas reservas" ou tentativa de cancelamento) — reaproveitando o status `cancelada` já existente, sem introduzir um status `expirada` separado. A consistência dos dados converge conforme o sistema é usado, sem infraestrutura nova.

## Quem pode reservar

Qualquer usuário autenticado, independente do `role` (`IsAuthenticated` padrão já configurado globalmente) — não há motivo de negócio para impedir um organizador ou portaria de comprar um ingresso.

## Limite de quantidade

Sem limite fixo por reserva — só limita pela capacidade disponível do evento no momento. `quantity` deve ser inteiro ≥ 1.

## Endpoints

Todos sob `api/v1/reservations/` (novo `include()` em `core/urls.py`).

### `POST /api/v1/reservations/`
Cria uma reserva.

- Auth: `IsAuthenticated`.
- Body: `{"event": <id>, "quantity": <int>}`.
- Sucesso: `201` com a reserva criada (`id`, `event`, `quantity`, `status`, `expires_at`, `created_at`).
- Erros:
  - `400` — `quantity` ausente ou < 1, ou a `date` do evento já passou (evento existe e está publicado, mas a sessão já aconteceu).
  - `404` — evento não existe ou não está `is_published=True`. Rascunhos de outros organizadores respondem 404, não 403, para não vazar a existência do evento.
  - `409` — capacidade insuficiente. Mensagem: `"Restam apenas N vaga(s) para este evento."`.

### `GET /api/v1/reservations/mine/`
Lista todas as reservas do usuário autenticado, todos os status, mais recentes primeiro. Aplica a expiração preguiçosa (grava `cancelada` nas que venceram) antes de serializar.

- Auth: `IsAuthenticated`.
- Sucesso: `200` com `{"reservas": [...]}`.

### `POST /api/v1/reservations/<id>/cancel/`
Cancela uma reserva própria.

- Auth: `IsAuthenticated`, dono da reserva.
- Aplica a expiração preguiçosa primeiro. Se o status (já atualizado) for `pendente`, cancela agora. Se já for `cancelada` — seja por cancelamento anterior ou por ter acabado de expirar nesta mesma chamada — trata como sucesso idempotente, sem erro.
- Sucesso: `200` com a reserva atualizada (`status=cancelada`).
- Erros:
  - `404` — reserva não existe ou não pertence ao usuário (não `403`, para não confirmar a terceiros que aquele ID existe).
  - `400` — reserva está `paga` ou `recusada` (estado que não pode ser cancelado por essa via), com mensagem explicando.

## Testes

Casos padrão via `APIClient` (mesmo padrão de `users`/`events`): criação com sucesso, `quantity` inválida, evento não publicado, evento no passado, capacidade insuficiente, listagem própria, cancelamento com sucesso, cancelamento de reserva alheia, cancelamento de reserva já resolvida.

**Teste de concorrência real** — o mais importante do sprint, prova que o `select_for_update()` realmente impede overselling em vez de apenas parecer correto na leitura do código:

- Evento com `capacity=1`.
- Duas threads disparam `POST /reservations/` simultaneamente, cada uma com `quantity=1` e sua própria conexão de banco.
- Resultado esperado: exatamente uma retorna `201`, a outra `409` — nunca as duas `201`.
- Requer `@pytest.mark.django_db(transaction=True)`, já que o modo padrão do pytest-django embrulha cada teste numa transação que nunca comita, o que mascararia o comportamento real do lock sob concorrência.

## Fora de escopo deste sprint

- Geração de `Ticket` (Sprint 4, ligado à confirmação de pagamento).
- `Payment` (Sprint 4).
- Endpoint do organizador para ver quem reservou em um evento seu (cogitado, mas mais natural no Sprint 5, junto da validação de portaria).
- Expiração via job/worker em background (lazy expiration cobre o caso de uso sem essa infraestrutura).
- Limite máximo de quantidade por reserva.
