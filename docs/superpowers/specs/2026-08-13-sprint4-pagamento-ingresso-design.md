# Sprint 4 — Pagamento e Ingresso

> Spec retroativa: documenta o design conforme implementado, escrita depois do código (não passou pelo ciclo de brainstorming antes de codar, diferente dos Sprints 1–3).

## Contexto

Sprint 4 do plano de 7 sprints do projeto. Uma reserva `pendente` (Sprint 3) precisa ser paga para virar `paga` e gerar um `Ticket` com QR code. A integração usa Stripe Checkout de verdade (não só uma simulação), com um modo `simulate` para testar localmente sem depender da rede/API do Stripe.

## Fluxo de pagamento

`POST /api/v1/reservations/<id>/pay/` — só o dono da reserva, só se `status=pendente` (aplicando a expiração preguiçosa do Sprint 3 primeiro: se já expirou, cancela e responde 400).

O corpo aceita `simulate`, com três valores possíveis:

- **`success`** (default) — confirma o pagamento imediatamente, sem tocar no Stripe. Útil para testes locais e para o botão "Simular sucesso" no frontend.
- **`fail`** — cria um `Payment` com `status=recusado` e marca a reserva como `recusada`.
- **`stripe`** — cria uma `stripe.checkout.Session` de verdade (`payment_method_types=['card']`, `mode='payment'`, valor = `quantity * event.price`, `client_reference_id=reserva.id` para linkar de volta) e devolve `checkout_url` para o frontend redirecionar o cliente.

## Confirmação de pagamento (`confirm_payment_and_generate_ticket`)

Função compartilhada entre o caminho síncrono (`simulate=success`) e o assíncrono (webhook do Stripe). Dentro de uma transação atômica:

1. Busca a `Reservation` com `select_for_update()`, filtrando `status=pendente`.
2. Verifica se `expires_at` já passou — se sim, marca `cancelada` e sai sem confirmar nada.
3. Cria o `Payment` (`status=confirmado`), muda a reserva para `paga`.
4. Cria o `Ticket` (código UUID) e assina com HMAC-SHA256 (`hmac.new(SECRET_KEY, f"{code}:{event_id}")`), guardando a assinatura em `Ticket.signature`.

O lock e a checagem de expiração existem especificamente porque o webhook do Stripe pode chegar bem depois da reserva ter sido criada (o cliente pode demorar no checkout hospedado), e o Stripe pode reentregar o mesmo webhook mais de uma vez (comportamento documentado da própria Stripe) — sem essas duas proteções, uma confirmação tardia ou duplicada furava a garantia de não-overselling do Sprint 3.

## Webhook do Stripe

`POST /api/v1/reservations/webhook/` — `AllowAny` (não é uma requisição de usuário logado, vem do servidor do Stripe), autenticidade garantida por `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)` em vez de qualquer cookie/token nosso. Em `checkout.session.completed`, lê `client_reference_id` (o id da reserva) e chama `confirm_payment_and_generate_ticket`.

## Formato do ingresso (QR)

`Ticket` guarda `code` (UUID) e `signature` (HMAC-SHA256 de `code:event_id`, chave = `SECRET_KEY` do Django). O `TicketSerializer` expõe um campo calculado `qr_token = "{code}.{signature}"` — essa string completa é o valor codificado no QR code exibido ao cliente, e é o mesmo formato que a validação de portaria (Sprint 5) espera receber de volta.

## Fora de escopo

- Reembolso/estorno de pagamento.
- Retry automático de pagamento recusado (o cliente teria que criar uma nova reserva).
- Idempotency key no `stripe.checkout.Session.create()` (mitigaria sessões duplicadas por duplo clique — não é uma falha de segurança, só criaria uma sessão Stripe órfã).
