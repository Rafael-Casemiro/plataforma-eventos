import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { Reservation } from '../api/types'
import { QRCodeSVG } from 'qrcode.react'

export default function MinhasReservas() {
  const [reservas, setReservas] = useState<Reservation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { logout } = useAuth()

  useEffect(() => {
    const fetchReservas = async () => {
      try {
        const response = await api.get<{reservas: Reservation[]}>('/reservations/mine/')
        setReservas(response.data.reservas)
      } catch (err) {
        setError('Não foi possível carregar as reservas.')
      } finally {
        setIsLoading(false)
      }
    }
    fetchReservas()
  }, [])

  const handlePayment = async (id: number, simulate: 'success' | 'fail' | 'stripe') => {
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
      alert(simulate === 'success' ? 'Pagamento confirmado!' : 'Pagamento recusado.')
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao processar pagamento.')
    }
  }

  return (
    <main className="min-h-screen bg-paper px-4 py-10">
      <div className="mx-auto max-w-4xl">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm font-medium text-neutral-500 hover:text-neutral-900">
              ← Voltar
            </Link>
            <h1 className="font-display text-3xl font-medium text-neutral-900">
              Minhas Reservas
            </h1>
          </div>

          <button
            type="button"
            onClick={() => logout()}
            className="text-neutral-500 text-sm"
          >
            Sair
          </button>
        </header>

        {isLoading ? (
          <p className="mt-10 text-center text-neutral-500">Carregando...</p>
        ) : error ? (
          <p className="mt-10 text-center text-accent">{error}</p>
        ) : reservas.length === 0 ? (
          <p className="mt-10 text-center text-neutral-500">
            Você ainda não possui reservas.
          </p>
        ) : (
          <ul className="mt-8 flex flex-col gap-4">
            {reservas.map((reserva) => (
              <li
                key={reserva.id}
                className="flex flex-col sm:flex-row items-center justify-between rounded-2xl border border-black/10 bg-white p-5 shadow-sm"
              >
                <div>
                  <h2 className="font-display text-lg font-medium text-neutral-900">
                    Reserva #{reserva.id} (Evento: {reserva.event})
                  </h2>
                  <p className="mt-1 text-sm text-neutral-500">
                    Quantidade: {reserva.quantity} ingresso(s)
                  </p>
                  <p className="mt-1 text-sm text-neutral-500">
                    Status:{' '}
                    <span
                      className={`font-medium uppercase ${
                        reserva.status === 'pendente'
                          ? 'text-yellow-600'
                          : reserva.status === 'paga'
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {reserva.status}
                    </span>
                  </p>
                </div>

                <div className="mt-4 sm:mt-0 flex flex-col items-end">
                  {reserva.status === 'pendente' && (
                    <div className="flex flex-col items-end">
                      <p className="text-xs text-neutral-400 mb-2">
                        Expira em: {new Date(reserva.expires_at).toLocaleTimeString('pt-BR')}
                      </p>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handlePayment(reserva.id, 'fail')}
                          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700">
                          Simular Recusa
                        </button>
                        <button 
                          onClick={() => handlePayment(reserva.id, 'stripe')}
                          className="rounded-lg bg-[#635BFF] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#4b45cc] shadow-md">
                          Pagar com Stripe
                        </button>
                      </div>
                    </div>
                  )}
                  {reserva.status === 'paga' && reserva.ticket && (
                    <div className="flex flex-col items-center">
                      <QRCodeSVG value={reserva.ticket.qr_token} size={96} />
                      <button 
                        onClick={() => {
                          navigator.clipboard.writeText(reserva.ticket!.qr_token)
                          alert('Token copiado!')
                        }}
                        className="mt-2 text-xs text-accent underline hover:text-neutral-900 cursor-pointer"
                        title="Copiar token completo para testar"
                      >
                        Copiar Token
                      </button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
