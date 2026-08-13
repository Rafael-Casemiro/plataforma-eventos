import { useEffect, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Navbar } from '../components/Navbar'
import type { Event } from '../api/types'

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w342'

export default function ListagemPublica() {
  const [eventos, setEventos] = useState<Event[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [date, setDate] = useState('')
  const [priceMin, setPriceMin] = useState('')
  const [priceMax, setPriceMax] = useState('')
  const [loadError, setLoadError] = useState<string | null>(null)
  const [reservationError, setReservationError] = useState<string | null>(null)

  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const fetchEventos = async (filters: Record<string, string>) => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value !== ''),
      )
      const response = await api.get<{ eventos: Event[] }>('/events/', {
        params,
      })
      setEventos(response.data.eventos)
    } catch {
      setEventos([])
      setLoadError('Não foi possível carregar os eventos.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchEventos({})
  }, [])

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    fetchEventos({
      search,
      date,
      price_min: priceMin,
      price_max: priceMax,
    })
  }

  const handleReservation = async (eventId: number) => {
    setReservationError(null)

    if (!user) {
      navigate('/login', { state: { from: location } })
      return
    }

    try {
      await api.post('/reservations/', {
        event: eventId,
        quantity: 1
      })
      navigate('/reservas')
    } catch (error: any) {
      setReservationError(
        error.response?.data?.detail || 'Erro ao efetuar reserva.',
      )
    }
  }

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-paper px-4 py-10">
        <div className="mx-auto max-w-5xl">
          <h1 className="font-display text-3xl font-medium text-neutral-900">
            Em cartaz
          </h1>

        {reservationError && (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600">
            {reservationError}
          </p>
        )}

        <form
          onSubmit={handleSubmit}
          className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4"
        >
          <input
            type="text"
            placeholder="Buscar por título"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="col-span-2 rounded-lg border border-black/10 px-3 py-2 text-sm sm:col-span-1"
          />
          <input
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="rounded-lg border border-black/10 px-3 py-2 text-sm"
          />
          <input
            type="number"
            placeholder="Preço min"
            value={priceMin}
            onChange={(event) => setPriceMin(event.target.value)}
            className="rounded-lg border border-black/10 px-3 py-2 text-sm"
          />
          <input
            type="number"
            placeholder="Preço max"
            value={priceMax}
            onChange={(event) => setPriceMax(event.target.value)}
            className="rounded-lg border border-black/10 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="col-span-2 rounded-lg bg-accent py-2 text-sm font-medium text-white sm:col-span-4"
          >
            Filtrar
          </button>
        </form>

        {isLoading ? (
          <p className="mt-10 text-center text-neutral-500">Carregando...</p>
        ) : loadError ? (
          <p className="mt-10 text-center text-rose-600">{loadError}</p>
        ) : eventos.length === 0 ? (
          <p className="mt-10 text-center text-neutral-500">
            Nenhum evento encontrado.
          </p>
        ) : (
          <ul className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {eventos.map((evento) => (
              <li
                key={evento.id}
                className="overflow-hidden rounded-2xl border border-black/10 bg-white shadow-sm"
              >
                <div className="relative">
                  {evento.poster_path ? (
                    <img
                      src={`${TMDB_IMAGE_BASE}${evento.poster_path}`}
                      alt={evento.title}
                      className="aspect-[2/3] w-full object-cover"
                    />
                  ) : (
                    <div className="flex aspect-[2/3] w-full items-center justify-center bg-neutral-200">
                      <span className="font-display text-4xl text-neutral-400">
                        {evento.title.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}

                  {evento.vagas_disponiveis <= 0 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                      <span className="font-display text-xl font-semibold uppercase tracking-wide text-white">
                        Esgotado
                      </span>
                    </div>
                  )}
                </div>

                <div className="p-5">
                  <h2 className="font-display text-lg font-medium text-neutral-900">
                    {evento.title}
                  </h2>
                  <p className="mt-1 text-sm text-neutral-500">
                    {evento.location}
                  </p>
                  <p className="mt-1 text-sm text-neutral-500">
                    {new Date(evento.date).toLocaleString('pt-BR')}
                  </p>
                  {evento.vagas_disponiveis > 0 && (
                    <p className="mt-1 text-xs text-neutral-400">
                      Restam {evento.vagas_disponiveis} vaga(s)
                    </p>
                  )}
                  <div className="mt-3 flex items-center justify-between">
                    <p className="font-display text-accent">
                      R$ {evento.price}
                    </p>
                    <button
                      onClick={() => handleReservation(evento.id)}
                      disabled={evento.vagas_disponiveis <= 0}
                      className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-300"
                    >
                      {evento.vagas_disponiveis <= 0 ? 'Esgotado' : 'Reservar'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
        </div>
      </main>
    </>
  )
}
