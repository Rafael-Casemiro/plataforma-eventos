import { useState, type FormEvent } from 'react'
import type { AxiosError } from 'axios'
import { api } from '../api/client'
import type { Event } from '../api/types'

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
  const [form, setForm] = useState<EventFormState>(initialState)
  const [error, setError] = useState<string | null>(null)
  const [createdEvents, setCreatedEvents] = useState<Event[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (
    field: keyof EventFormState,
    value: string | boolean,
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const response = await api.post<Event>('/events/create/', {
        ...form,
        capacity: Number(form.capacity),
        external_ref: Number(form.external_ref),
      })
      setCreatedEvents((prev) => [response.data, ...prev])
      setForm(initialState)
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
        <h1 className="font-display text-3xl font-medium text-neutral-900">
          Painel do organizador
        </h1>
        <p className="mt-1 text-sm text-neutral-500">Crie um novo evento.</p>

        {error && (
          <p className="mt-4 rounded-lg bg-accent/10 px-3 py-2 text-sm text-accent">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
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

            <label className="text-sm font-medium text-neutral-700">
              Ref. TMDb
              <input
                type="number"
                value={form.external_ref}
                onChange={(event) =>
                  handleChange('external_ref', event.target.value)
                }
                required
                className="mt-1 w-full rounded-lg border border-black/10 px-3 py-2"
              />
            </label>

            <label className="text-sm font-medium text-neutral-700">
              Título original (TMDb)
              <input
                value={form.external_title}
                onChange={(event) =>
                  handleChange('external_title', event.target.value)
                }
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

        {createdEvents.length > 0 && (
          <div className="mt-10">
            <h2 className="font-display text-xl font-medium text-neutral-900">
              Criados nesta sessão
            </h2>
            <ul className="mt-4 grid gap-3">
              {createdEvents.map((evento) => (
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
          </div>
        )}
      </div>
    </main>
  )
}
