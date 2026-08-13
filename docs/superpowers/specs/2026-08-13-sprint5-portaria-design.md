# Sprint 5 — Portaria

> Spec retroativa: documenta o design conforme implementado, escrita depois do código (não passou pelo ciclo de brainstorming antes de codar, diferente dos Sprints 1–3).

## Contexto

Sprint 5 do plano de 7 sprints do projeto. Com o `Ticket` já gerado e assinado (Sprint 4), falta o fluxo de validação na entrada do evento: alguém do papel `portaria` escaneia (ou digita) o token do ingresso, e o sistema decide se libera a entrada.

## Endpoint

`POST /api/v1/reservations/validate-ticket/` — restrito a `role=portaria` (`IsPortaria`, já existente em `users/permissions.py`).

Body: `{"token": "<code>.<signature>", "event_id": <id>}`.

## Validação

Dentro de uma transação atômica:

1. Separa `token` em `code` e `signature` pelo `.` — formato inválido (não tem exatamente 2 partes) → `inválido`.
2. Busca o `Ticket` pelo `code` com `select_for_update()` — travar a linha impede que dois scanners validando o mesmo ingresso ao mesmo tempo (ex: duas catracas, ou o mesmo QR fotografado duas vezes em sequência rápida) ambos leiam "ainda não usado" antes de qualquer um commitar. Não encontrado → `inválido`.
3. Confere se o ingresso é do evento informado (`ticket.reservation.event_id == event_id`) — impede usar o ingresso de um evento para entrar em outro. Não bate → `evento errado`.
4. Recalcula a assinatura esperada (`HMAC-SHA256` de `code:event_id`, mesma chave `SECRET_KEY`) e compara com `hmac.compare_digest` (comparação em tempo constante, evita ataque de timing). Não bate → `inválido`.
5. Confere `used_at` — já preenchido → `já utilizado`.
6. Tudo certo: marca `used_at=agora`, libera a entrada → `válido`.

## Os 4 estados

`válido` (200), `inválido` (400 — formato, ingresso inexistente ou assinatura não confere), `evento errado` (400), `já utilizado` (409). O front (`Portaria.tsx`) usa esses 4 valores diretamente para colorir o resultado (verde/vermelho/laranja/azul).

## Frontend

`Portaria.tsx` — leitor de câmera via `@yudiel/react-qr-scanner` (biblioteca escolhida por ler QR direto da câmera do navegador, sem precisar de app nativo) com campo de texto como alternativa manual (útil pra testar sem câmera, ou se o QR não escanear). Cada leitura chama `validate-ticket/` e mostra o resultado colorido; ignora reads repetidos do mesmo token enquanto o resultado anterior ainda está na tela (evita reenviar a mesma leitura várias vezes por segundo enquanto a câmera continua enquadrando o mesmo QR).

## Fora de escopo

- Reverter um ingresso marcado como usado por engano (precisaria de ação manual no Django Admin).
- Contagem de check-ins em tempo real / dashboard de ocupação do evento.
- Restringir qual portaria pode validar qual evento (hoje qualquer usuário `portaria` valida ingresso de qualquer evento).
