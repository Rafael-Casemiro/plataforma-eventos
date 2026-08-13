import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { Navbar } from '../components/Navbar'
import type { Reservation } from '../api/types'
import { QRCodeSVG } from 'qrcode.react'

function formatCountdown(expiresAt: string, now: number): string {
  const remainingMs = new Date(expiresAt).getTime() - now
  if (remainingMs <= 0) return 'Expirado'
  const totalSeconds = Math.floor(remainingMs / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export default function MinhasReservas() {
  const [reservas, setReservas] = useState<Reservation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [now, setNow] = useState(() => Date.now())
  const [paymentError, setPaymentError] = useState<{ id: number; message: string } | null>(null)
  const [copiedLabel, setCopiedLabel] = useState<{ id: number; type: 'token' | 'link' } | null>(null)
  const refetchedIds = useRef(new Set<number>())

  const fetchReservas = useCallback(async () => {
    try {
      const response = await api.get<{ reservas: Reservation[] }>(
        '/reservations/mine/',
      )
      setReservas(response.data.reservas)
    } catch {
      setError('Não foi possível carregar as reservas.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReservas()
  }, [fetchReservas])

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const recemExpiradas = reservas.filter(
      (reserva) =>
        reserva.status === 'pendente' &&
        new Date(reserva.expires_at).getTime() - now <= 0 &&
        !refetchedIds.current.has(reserva.id),
    )
    if (recemExpiradas.length > 0) {
      recemExpiradas.forEach((reserva) => refetchedIds.current.add(reserva.id))
      fetchReservas()
    }
  }, [now, reservas, fetchReservas])

  const handlePayment = async (id: number, simulate: 'success' | 'fail' | 'stripe') => {
    setPaymentError(null)
    try {
      // @ts-ignore (ignoring missing checkout_url in Reservation type for brevity)
      const response = await api.post(`/reservations/${id}/pay/`, { simulate })

      if (simulate === 'stripe' && response.data.checkout_url) {
        window.location.href = response.data.checkout_url
        return
      }

      setReservas((prev) =>
        prev.map((res) => (res.id === id ? response.data : res)),
      )
    } catch (err: any) {
      setPaymentError({
        id,
        message: err.response?.data?.detail || 'Erro ao processar pagamento.',
      })
    }
  }

  const handleCopy = (id: number, type: 'token' | 'link', value: string) => {
    navigator.clipboard.writeText(value)
    setCopiedLabel({ id, type })
    setTimeout(() => setCopiedLabel(null), 2000)
  }

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-paper px-4 py-10">
        <div className="mx-auto max-w-4xl">
        <h1 className="font-display text-3xl font-medium text-neutral-900">
          Minhas Reservas
        </h1>

        {isLoading ? (
          <p className="mt-10 text-center text-neutral-500">Carregando...</p>
        ) : error ? (
          <p className="mt-10 text-center text-rose-600">{error}</p>
        ) : reservas.length === 0 ? (
          <p className="mt-10 text-center text-neutral-500">
            Você ainda não possui reservas.
          </p>
        ) : (
          <ul className="mt-8 flex flex-col gap-4">
            {reservas.map((reserva) => {
              const statusBadge =
                reserva.status === 'pendente'
                  ? 'bg-amber-100 text-amber-700'
                  : reserva.status === 'paga'
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-rose-100 text-rose-700'

              return (
                <li
                  key={reserva.id}
                  className={
                    reserva.status === 'pendente'
                      ? 'rounded-2xl border-2 border-amber-300 bg-amber-50/60 p-5 shadow-sm'
                      : reserva.status === 'paga'
                        ? 'rounded-2xl bg-gradient-to-br from-emerald-50 via-white to-emerald-100/60 p-5 shadow-sm'
                        : 'rounded-2xl border border-black/10 bg-white p-5 shadow-sm'
                  }
                >
                  <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
                    <div>
                      <h2 className="font-display text-lg font-semibold text-neutral-900">
                        {reserva.event_title}
                      </h2>
                      <p className="mt-1 text-sm text-neutral-500">
                        {reserva.event_location} —{' '}
                        {new Date(reserva.event_date).toLocaleString('pt-BR', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                      <p className="mt-1 text-sm text-neutral-500">
                        Quantidade: {reserva.quantity} ingresso(s)
                      </p>
                      <span
                        className={`mt-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${statusBadge}`}
                      >
                        {reserva.status}
                      </span>
                    </div>

                    {reserva.status === 'pendente' && (
                      <div className="flex flex-col items-center sm:items-end">
                        <p className="text-xs font-medium uppercase tracking-wide text-amber-600">
                          Expira em
                        </p>
                        <p className="font-display text-2xl font-semibold text-amber-700">
                          {formatCountdown(reserva.expires_at, now)}
                        </p>
                        <div className="mt-3 flex gap-2">
                          <button
                            onClick={() => handlePayment(reserva.id, 'fail')}
                            className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-rose-700">
                            Simular Recusa
                          </button>
                          <button
                            onClick={() => handlePayment(reserva.id, 'stripe')}
                            className="rounded-lg bg-[#635BFF] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#4b45cc] shadow-md">
                            Pagar com Stripe
                          </button>
                        </div>
                        {paymentError && paymentError.id === reserva.id && (
                          <p className="mt-2 text-xs font-medium text-rose-600">
                            {paymentError.message}
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {reserva.status === 'paga' && reserva.ticket && (
                    <div className="mt-4 flex flex-col items-center rounded-2xl border border-white/60 bg-white/70 p-6 shadow-lg backdrop-blur-md">
                      <QRCodeSVG value={reserva.ticket.qr_token} size={140} />
                      <p className="mt-3 text-center text-xs text-neutral-500">
                        Sem câmera na portaria? Informe este código:
                      </p>
                      <p className="mt-1 font-mono text-lg font-semibold tracking-widest text-neutral-900">
                        {reserva.ticket.short_code}
                      </p>
                      <button
                        onClick={() => handleCopy(reserva.id, 'token', reserva.ticket!.qr_token)}
                        className="mt-3 text-xs text-accent underline hover:text-neutral-900 cursor-pointer"
                        title="Copiar token completo para testar"
                      >
                        {copiedLabel?.id === reserva.id && copiedLabel.type === 'token'
                          ? 'Copiado!'
                          : 'Copiar Token'}
                      </button>
                      <button
                        onClick={() =>
                          handleCopy(
                            reserva.id,
                            'link',
                            `${window.location.origin}/ingresso/${reserva.ticket!.share_token}`,
                          )
                        }
                        className="mt-1 text-xs text-accent underline hover:text-neutral-900 cursor-pointer"
                        title="Copiar link publico do ingresso"
                      >
                        {copiedLabel?.id === reserva.id && copiedLabel.type === 'link'
                          ? 'Copiado!'
                          : 'Copiar link para compartilhar'}
                      </button>
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
        </div>
      </main>
    </>
  )
}
