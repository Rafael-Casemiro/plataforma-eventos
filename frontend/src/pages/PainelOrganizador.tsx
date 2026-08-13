import { useEffect, useState, type FormEvent } from 'react'
import type { AxiosError } from 'axios'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { Event, TmdbMovie } from '../api/types'

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w200'

interface EventFormState {
  title: string
  description: string
  date: string
  location: string
  capacity: string
  price: string
  external_ref: string
  external_title: string
  poster_path: string
  is_published: boolean
}

const initialState: EventFormState = {
  title: '',
  description: '',
  date: '',
  location: '',
  capacity: '',
  price: '',
  external_ref: '',
  external_title: '',
  poster_path: '',
  is_published: true,
}

export default function PainelOrganizador() {
  const { logout } = useAuth()
  const [form, setForm] = useState<EventFormState>(initialState)
  const [error, setError] = useState<string | null>(null)
  const [eventos, setEventos] = useState<Event[]>([])
  const [isLoadingEventos, setIsLoadingEventos] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [movies, setMovies] = useState<TmdbMovie[]>([])
  const [isLoadingMovies, setIsLoadingMovies] = useState(true)
  const [movieError, setMovieError] = useState<string | null>(null)
  const [isPickingMovie, setIsPickingMovie] = useState(true)

  useEffect(() => {
    const fetchMeusEventos = async () => {
      try {
        const response = await api.get<{ eventos: Event[] }>('/events/mine/')
        setEventos(response.data.eventos)
      } finally {
        setIsLoadingEventos(false)
      }
    }

    const fetchMovies = async () => {
      setIsLoadingMovies(true)
      setMovieError(null)
      try {
        const response = await api.get<TmdbMovie[]>('/events/catalog/')
        setMovies(response.data)
      } catch {
        setMovieError('Não foi possível buscar os filmes em cartaz na TMDb.')
      } finally {
        setIsLoadingMovies(false)
      }
    }

    fetchMeusEventos()
    fetchMovies()
  }, [])

  const handleChange = (
    field: keyof EventFormState,
    value: string | boolean,
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSelectMovie = (movie: TmdbMovie) => {
    setForm((prev) => ({
      ...prev,
      external_ref: String(movie.id),
      external_title: movie.titulo,
      poster_path: movie.poster_path,
      title: prev.title || movie.titulo,
    }))
    setIsPickingMovie(false)
  }

  const selectedMovie = form.external_ref
    ? movies.find((movie) => movie.id === Number(form.external_ref))
    : undefined

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)

    if (!form.external_ref) {
      setError('Escolha um filme da TMDb antes de criar o evento.')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await api.post<Event>('/events/create/', {
        ...form,
        capacity: Number(form.capacity),
        external_ref: Number(form.external_ref),
      })
      setEventos((prev) => [response.data, ...prev])
      setForm(initialState)
      setIsPickingMovie(true)
    } catch (err) {
      const axiosError = err as AxiosError<Record<string, string[]>>
      const data = axiosError.response?.data
      const firstError = data ? Object.values(data)[0]?.[0] : undefined
      setError(firstError ?? 'Não foi possível criar o evento.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen bg-paper px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <header className="flex items-center justify-between">
          <Link to="/" className="text-sm font-medium text-accent">
            ← Em cartaz
          </Link>
          <button
            type="button"
            onClick={() => logout()}
            className="text-sm text-neutral-500"
          >
            Sair
          </button>
        </header>

        <h1 className="mt-6 font-display text-3xl font-medium text-neutral-900">
          Painel do organizador
        </h1>
        <p className="mt-1 text-sm text-neutral-500">Crie um novo evento.</p>

        {error && (
          <p className="mt-4 rounded-lg bg-accent/10 px-3 py-2 text-sm text-accent">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
          <div>
            <p className="text-sm font-medium text-neutral-700">
              Filme (TMDb)
            </p>

            {selectedMovie && !isPickingMovie ? (
              <div className="mt-1 flex items-center gap-3 rounded-lg border border-black/10 p-3">
                {selectedMovie.poster_path && (
                  <img
                    src={`${TMDB_IMAGE_BASE}${selectedMovie.poster_path}`}
                    alt=""
                    className="h-16 w-11 rounded object-cover"
                  />
                )}
                <div className="flex-1">
                  <p className="font-medium text-neutral-900">
                    {selectedMovie.titulo}
                  </p>
                  <p className="text-xs text-neutral-500">
                    {selectedMovie.data_lancamento}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsPickingMovie(true)}
                  className="text-sm font-medium text-accent"
                >
                  Trocar
                </button>
              </div>
            ) : isLoadingMovies ? (
              <p className="mt-1 text-sm text-neutral-500">
                Buscando filmes em cartaz...
              </p>
            ) : movieError ? (
              <p className="mt-1 text-sm text-accent">{movieError}</p>
            ) : (
              <div className="mt-2 grid max-h-64 grid-cols-3 gap-2 overflow-y-auto rounded-lg border border-black/10 p-2 sm:grid-cols-4">
                {movies.map((movie) => (
                  <button
                    type="button"
                    key={movie.id}
                    onClick={() => handleSelectMovie(movie)}
                    className="rounded-lg text-left transition hover:opacity-80"
                  >
                    {movie.poster_path && (
                      <img
                        src={`${TMDB_IMAGE_BASE}${movie.poster_path}`}
                        alt=""
                        className="w-full rounded-lg object-cover"
                      />
                    )}
                    <p className="mt-1 line-clamp-2 text-xs text-neutral-700">
                      {movie.titulo}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          <label className="text-sm font-medium text-neutral-700">
            Título
            <input
              value={form.title}
              onChange={(event) => handleChange('title', event.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
            />
          </label>

          <label className="text-sm font-medium text-neutral-700">
            Descrição
            <textarea
              value={form.description}
              onChange={(event) =>
                handleChange('description', event.target.value)
              }
              className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
            />
          </label>

          <div className="grid grid-cols-2 gap-4">
            <label className="text-sm font-medium text-neutral-700">
              Data e hora
              <input
                type="datetime-local"
                value={form.date}
                onChange={(event) => handleChange('date', event.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
              />
            </label>

            <label className="text-sm font-medium text-neutral-700">
              Local
              <input
                value={form.location}
                onChange={(event) =>
                  handleChange('location', event.target.value)
                }
                required
                className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
              />
            </label>

            <label className="text-sm font-medium text-neutral-700">
              Capacidade
              <input
                type="number"
                min={1}
                value={form.capacity}
                onChange={(event) =>
                  handleChange('capacity', event.target.value)
                }
                required
                className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
              />
            </label>

            <label className="text-sm font-medium text-neutral-700">
              Preço
              <input
                type="number"
                min={0}
                step="0.01"
                value={form.price}
                onChange={(event) => handleChange('price', event.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
              />
            </label>
          </div>

          <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
            <input
              type="checkbox"
              checked={form.is_published}
              onChange={(event) =>
                handleChange('is_published', event.target.checked)
              }
            />
            Publicar imediatamente
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-accent py-2 font-medium text-white disabled:opacity-60"
          >
            {isSubmitting ? 'Criando...' : 'Criar evento'}
          </button>
        </form>

        <div className="mt-10">
          <h2 className="font-display text-xl font-medium text-neutral-900">
            Meus eventos
          </h2>

          {isLoadingEventos ? (
            <p className="mt-4 text-sm text-neutral-500">Carregando...</p>
          ) : eventos.length === 0 ? (
            <p className="mt-4 text-sm text-neutral-500">
              Você ainda não criou nenhum evento.
            </p>
          ) : (
            <ul className="mt-4 grid gap-3">
              {eventos.map((evento) => (
                <li
                  key={evento.id}
                  className="rounded-2xl border border-black/10 bg-white p-4 shadow-sm"
                >
                  <p className="font-display font-medium text-neutral-900">
                    {evento.title}
                  </p>
                  <p className="text-sm text-neutral-500">
                    {evento.is_published ? 'Publicado' : 'Rascunho'}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </main>
  )
}
