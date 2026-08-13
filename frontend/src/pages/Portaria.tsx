import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Scanner } from '@yudiel/react-qr-scanner'

export default function Portaria() {
  const [eventId, setEventId] = useState<string>('12')
  const [manualToken, setManualToken] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'válido' | 'inválido' | 'já utilizado' | 'evento errado'>('idle')
  const [message, setMessage] = useState('')
  const [lastScanned, setLastScanned] = useState('')

  const handleValidate = async (token: string) => {
    if (!token || !eventId) return
    if (token === lastScanned && status !== 'idle' && status !== 'loading') return 
    
    setLastScanned(token)
    setStatus('loading')
    setMessage('Consultando servidor...')

    try {
      const response = await api.post('/reservations/validate-ticket/', { 
        token, 
        event_id: parseInt(eventId) 
      })
      
      setStatus(response.data.status)
      setMessage(response.data.detail)
    } catch (err: any) {
      const errStatus = err.response?.data?.status || 'inválido'
      const errDetail = err.response?.data?.detail || 'Erro ao comunicar com o servidor.'
      setStatus(errStatus)
      setMessage(errDetail)
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'válido': return 'bg-green-100 text-green-800 border-green-500'
      case 'inválido': return 'bg-red-100 text-red-800 border-red-500'
      case 'já utilizado': return 'bg-orange-100 text-orange-800 border-orange-500'
      case 'evento errado': return 'bg-blue-100 text-blue-800 border-blue-500'
      case 'loading': return 'bg-neutral-100 text-neutral-800 border-neutral-300 animate-pulse'
      default: return 'bg-neutral-100 text-neutral-800 border-neutral-300'
    }
  }

  return (
    <main className="min-h-screen bg-paper px-4 py-10">
      <div className="mx-auto max-w-lg">
        <header className="flex items-center gap-4 mb-8">
          <Link to="/" className="text-sm font-medium text-neutral-500 hover:text-neutral-900">
            ← Voltar
          </Link>
          <h1 className="font-display text-3xl font-medium text-neutral-900">
            Portaria Virtual
          </h1>
        </header>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-black/10 flex flex-col gap-6">
          
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Validar ingressos para qual Evento ID?
            </label>
            <input 
              type="number"
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
              className="w-full rounded-lg border-neutral-300 shadow-sm focus:border-accent focus:ring-accent sm:text-sm p-2 border"
            />
          </div>

          <div className="rounded-xl overflow-hidden border border-black/10 bg-black aspect-square max-h-96 relative">
            <Scanner 
              onScan={(detected) => {
                if (detected && detected.length > 0) {
                  handleValidate(detected[0].rawValue)
                }
              }}
              onError={(error) => console.error(error)}
              formats={['qr_code']}
              components={{ audio: false, finder: false }}
            />
          </div>

          <div className="flex gap-2">
            <input 
              type="text"
              placeholder="Ou digite o token (UUID.HMAC)..."
              value={manualToken}
              onChange={(e) => setManualToken(e.target.value)}
              className="flex-1 rounded-lg border-neutral-300 shadow-sm focus:border-accent focus:ring-accent sm:text-sm p-2 border font-mono text-xs"
            />
            <button 
              onClick={() => handleValidate(manualToken)}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-800">
              Validar
            </button>
          </div>

          {status !== 'idle' && (
            <div className={`mt-2 p-4 rounded-xl border-2 text-center transition-all ${getStatusColor()}`}>
              <p className="font-display font-medium text-lg uppercase tracking-wider mb-1">
                {status}
              </p>
              <p className="text-sm font-medium opacity-90">
                {message}
              </p>
              {status !== 'loading' && (
                <button 
                  onClick={() => {
                    setStatus('idle')
                    setLastScanned('')
                  }}
                  className="mt-3 text-xs underline opacity-70 hover:opacity-100">
                  Limpar e ler próximo
                </button>
              )}
            </div>
          )}

        </div>
      </div>
    </main>
  )
}
