import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Navbar } from '../components/Navbar'
import { Scanner } from '@yudiel/react-qr-scanner'
import type { Event, PaginatedResponse } from '../api/types'

interface CheckInProgress {
  validados: number
  total: number
}

export default function Portaria() {
  const [eventos, setEventos] = useState<Event[]>([])
  const [eventId, setEventId] = useState<string>('')
  const [progress, setProgress] = useState<CheckInProgress | null>(null)
  const [manualToken, setManualToken] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'válido' | 'inválido' | 'já utilizado' | 'evento errado'>('idle')
  const [message, setMessage] = useState('')
  const [lastScanned, setLastScanned] = useState('')
  const [hasCameraError, setHasCameraError] = useState(false)

  useEffect(() => {
    const fetchEventos = async () => {
      try {
        const response = await api.get<PaginatedResponse<Event>>('/events/', {
          params: { page_size: 50 },
        })
        setEventos(response.data.results)
        if (response.data.results.length > 0) {
          setEventId(String(response.data.results[0].id))
        }
      } catch {
        setEventos([])
      }
    }
    fetchEventos()
  }, [])

  const fetchProgress = async (currentEventId: string) => {
    if (!currentEventId) return
    try {
      const response = await api.get<CheckInProgress>(
        `/reservations/check-in/${currentEventId}/`,
      )
      setProgress(response.data)
    } catch {
      setProgress(null)
    }
  }

  useEffect(() => {
    fetchProgress(eventId)
  }, [eventId])

  const handleValidate = async (token: string) => {
    if (!token || !eventId) return
    if (token === lastScanned && status !== 'idle' && status !== 'loading') return

    setLastScanned(token)
    setStatus('loading')
    setMessage('Consultando servidor...')

    try {
      const response = await api.post('/reservations/validate-ticket/', {
        token,
        event_id: parseInt(eventId),
      })

      setStatus(response.data.status)
      setMessage(response.data.detail)
      fetchProgress(eventId)
    } catch (err: any) {
      const errStatus = err.response?.data?.status || 'inválido'
      const errDetail = err.response?.data?.detail || 'Erro ao comunicar com o servidor.'
      setStatus(errStatus)
      setMessage(errDetail)
    }
  }

  const getStatusPanelClasses = () => {
    switch (status) {
      case 'válido': return 'bg-emerald-600'
      case 'inválido': return 'bg-rose-600'
      case 'já utilizado': return 'bg-amber-500'
      case 'evento errado': return 'bg-indigo-600'
      default: return 'bg-neutral-800'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'válido': return '✓'
      case 'inválido': return '✕'
      case 'já utilizado': return '⏳'
      case 'evento errado': return '⚠'
      default: return ''
    }
  }

  const isFinalState =
    status !== 'idle' && status !== 'loading'

  const eventoSelecionado = eventos.find((evento) => String(evento.id) === eventId)

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-paper px-4 py-10">
        <div className="mx-auto max-w-lg">
        <h1 className="mb-8 font-display text-3xl font-semibold text-neutral-900">
          Portaria Virtual
        </h1>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-black/10 flex flex-col gap-6">

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Sessão nesta entrada
            </label>
            <select
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
              className="w-full rounded-lg border-neutral-300 shadow-sm focus:border-accent focus:ring-accent sm:text-sm p-2 border"
            >
              {eventos.length === 0 && <option value="">Nenhum evento disponível</option>}
              {eventos.map((evento) => (
                <option key={evento.id} value={evento.id}>
                  {evento.title} — {new Date(evento.date).toLocaleString('pt-BR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </option>
              ))}
            </select>
          </div>

          {progress && (
            <div className="rounded-xl border border-black/10 p-4">
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  Validados
                </span>
                <span className="font-display text-2xl font-semibold text-neutral-900">
                  {progress.validados}
                  <span className="text-base font-normal text-neutral-400">/{progress.total}</span>
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200">
                <div
                  className="h-full rounded-full bg-emerald-600 transition-all"
                  style={{
                    width: progress.total > 0
                      ? `${(progress.validados / progress.total) * 100}%`
                      : '0%',
                  }}
                />
              </div>
              {eventoSelecionado && (
                <p className="mt-2 text-xs text-neutral-500">
                  {eventoSelecionado.location}
                </p>
              )}
            </div>
          )}

          {hasCameraError ? (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
              <p className="text-sm font-semibold text-amber-800">
                Sem câmera disponível
              </p>
              <p className="mt-1 text-sm text-amber-700">
                Este aparelho ou navegador não expôs uma câmera. Use a digitação
                abaixo — o código de 10 caracteres está impresso no ingresso.
              </p>
            </div>
          ) : (
            <div className="rounded-xl overflow-hidden border border-black/10 bg-black aspect-square max-h-96 relative">
              <Scanner
                onScan={(detected) => {
                  if (detected && detected.length > 0) {
                    handleValidate(detected[0].rawValue)
                  }
                }}
                onError={() => setHasCameraError(true)}
                formats={['qr_code']}
                components={{ finder: false }}
              />
            </div>
          )}

          <div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ou digite o código do ingresso"
                value={manualToken}
                onChange={(e) => setManualToken(e.target.value)}
                className="flex-1 rounded-lg border-neutral-300 shadow-sm focus:border-accent focus:ring-accent sm:text-sm p-2 border font-mono text-xs uppercase"
              />
              <button
                onClick={() => handleValidate(manualToken)}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-800">
                Validar
              </button>
            </div>
            <p className="mt-1 text-xs text-neutral-400">
              São 10 caracteres, impressos no ingresso. O ingresso precisa ser desta sessão.
            </p>
          </div>

          {status === 'loading' && (
            <p className="text-center text-sm font-medium text-neutral-500 animate-pulse">
              {message}
            </p>
          )}

        </div>
      </div>

      {isFinalState && (
        <div
          className={`fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 p-8 text-center text-white animate-state-pop ${getStatusPanelClasses()}`}
        >
          <span className="text-8xl leading-none">{getStatusIcon()}</span>
          <p className="font-display text-5xl font-bold uppercase tracking-wide sm:text-6xl">
            {status}
          </p>
          <p className="max-w-md text-lg font-medium opacity-90">
            {message}
          </p>
          <button
            onClick={() => {
              setStatus('idle')
              setLastScanned('')
            }}
            className="mt-4 rounded-full bg-white/20 px-6 py-3 text-sm font-semibold uppercase tracking-wide backdrop-blur-md transition hover:bg-white/30"
          >
            Limpar e ler próximo
          </button>
        </div>
        )}
      </main>
    </>
  )
}
