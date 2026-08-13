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

function toDatetimeLocalValue(isoDate: string): string {
  const date = new Date(isoDate)
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export default function PainelOrganizador() {
  const { logout } = useAuth()
  const [form, setForm] = useState<EventFormState>(initialState)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
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

  const handleEdit = (evento: Event) => {
    setEditingId(evento.id)
    setForm({
      title: evento.title,
      description: evento.description,
      date: toDatetimeLocalValue(evento.date),
      location: evento.location,
      capacity: String(evento.capacity),
      price: evento.price,
      external_ref: String(evento.external_ref),
      external_title: evento.external_title,
      poster_path: evento.poster_path,
      is_published: evento.is_published,
    })
    setIsPickingMovie(false)
    setError(null)
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setForm(initialState)
    setIsPickingMovie(true)
    setError(null)
  }

  const handleDelete = async (evento: Event) => {
    if (!window.confirm(`Remover o evento "${evento.title}"?`)) {
      return
    }

    setDeletingId(evento.id)
    setError(null)

    try {
      await api.delete(`/events/${evento.id}/`)
      setEventos((prev) => prev.filter((item) => item.id !== evento.id))
      if (editingId === evento.id) {
        handleCancelEdit()
      }
    } catch {
      setError('Não foi possível remover o evento.')
    } finally {
      setDeletingId(null)
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)

    if (!form.external_ref) {
      setError('Escolha um filme da TMDb antes de criar o evento.')
      return
    }

    setIsSubmitting(true)

    const payload = {
      ...form,
      capacity: Number(form.capacity),
      external_ref: Number(form.external_ref),
    }

    try {
      if (editingId) {
        const response = await api.patch<Event>(
          `/events/${editingId}/`,
          payload,
        )
        setEventos((prev) =>
          prev.map((evento) =>
            evento.id === editingId ? response.data : evento,
          ),
        )
        setEditingId(null)
      } else {
        const response = await api.post<Event>('/events/create/', payload)
        setEventos((prev) => [response.data, ...prev])
      }
      setForm(initialState)
      setIsPickingMovie(true)
    } catch (err) {
      const axiosError = err as AxiosError<Record<string, string[]>>
      const data = axiosError.response?.data
      const firstError = data ? Object.values(data)[0]?.[0] : undefined
      setError(
        firstError ??
          (editingId
            ? 'Não foi possível salvar as alterações.'
            : 'Não foi possível criar o evento.'),
      )
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
        <p className="mt-1 text-sm text-neutral-500">
          {editingId ? 'Edite os dados do evento.' : 'Crie um novo evento.'}
        </p>

        {error && (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-6 grid gap-5 rounded-2xl border border-black/10 bg-white p-6 shadow-sm">
          <div>
            <p className="text-sm font-medium text-neutral-700">
              Filme (TMDb)
            </p>

            {form.external_ref && !isPickingMovie ? (
              <div className="mt-1 flex items-center gap-3 rounded-lg border border-black/10 p-3">
                {form.poster_path && (
                  <img
                    src={`${TMDB_IMAGE_BASE}${form.poster_path}`}
                    alt=""
                    className="h-16 w-11 rounded object-cover"
                  />
                )}
                <div className="flex-1">
                  <p className="font-medium text-neutral-900">
                    {form.external_title}
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
              <p className="mt-1 text-sm text-rose-600">{movieError}</p>
            ) : (
              <div className="mt-2 grid max-h-64 grid-cols-3 gap-3 overflow-y-auto rounded-lg border border-black/10 p-3 sm:grid-cols-4">
                {movies.map((movie) => (
                  <button
                    type="button"
                    key={movie.id}
                    onClick={() => handleSelectMovie(movie)}
                    className="rounded-lg text-left transition hover:ring-2 hover:ring-accent/60"
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

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 rounded-lg bg-accent py-2 font-medium text-white disabled:opacity-60"
            >
              {isSubmitting
                ? 'Salvando...'
                : editingId
                  ? 'Salvar alterações'
                  : 'Criar evento'}
            </button>

            {editingId && (
              <button
                type="button"
                onClick={handleCancelEdit}
                className="text-sm text-neutral-500"
              >
                Cancelar edição
              </button>
            )}
          </div>
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
            <ul className="mt-4 grid gap-4">
              {eventos.map((evento) => (
                <li
                  key={evento.id}
                  className="flex items-center justify-between gap-3 rounded-2xl border border-black/10 bg-white p-5 shadow-sm transition hover:shadow-md"
                >
                  <div>
                    <p className="font-display font-medium text-neutral-900">
                      {evento.title}
                    </p>
                    <p className="text-sm text-neutral-500">
                      {evento.is_published ? 'Publicado' : 'Rascunho'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleEdit(evento)}
                      className="text-sm font-medium text-accent"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(evento)}
                      disabled={deletingId === evento.id}
                      className="text-sm text-neutral-500 disabled:opacity-60"
                    >
                      {deletingId === evento.id ? 'Removendo...' : 'Excluir'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </main>
  )
}
