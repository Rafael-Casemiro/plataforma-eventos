import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { SharedTicket } from '../api/types'

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w342'

export default function IngressoCompartilhado() {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [ingresso, setIngresso] = useState<SharedTicket | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchIngresso = async () => {
      try {
        const response = await api.get<SharedTicket>(
          `/reservations/share/${shareToken}/`,
        )
        setIngresso(response.data)
      } catch {
        setError('Ingresso não encontrado.')
      } finally {
        setIsLoading(false)
      }
    }
    fetchIngresso()
  }, [shareToken])

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm overflow-hidden rounded-2xl border border-black/10 bg-white shadow-sm">
        {isLoading ? (
          <p className="p-8 text-center text-neutral-500">Carregando...</p>
        ) : error || !ingresso ? (
          <p className="p-8 text-center text-accent">{error}</p>
        ) : (
          <>
            {ingresso.poster_path && (
              <img
                src={`${TMDB_IMAGE_BASE}${ingresso.poster_path}`}
                alt=""
                className="aspect-[2/3] w-full object-cover"
              />
            )}
            <div className="p-6">
              <h1 className="font-display text-xl font-medium text-neutral-900">
                {ingresso.title}
              </h1>
              <p className="mt-1 text-sm text-neutral-500">
                {ingresso.location}
              </p>
              <p className="mt-1 text-sm text-neutral-500">
                {new Date(ingresso.date).toLocaleString('pt-BR')}
              </p>
              <p className="mt-3 font-display text-accent">
                {ingresso.quantity} ingresso(s)
              </p>
            </div>
          </>
        )}
      </div>

      <Link
        to="/"
        className="fixed bottom-6 text-sm font-medium text-neutral-500 hover:text-neutral-900"
      >
        ← Ver mais eventos
      </Link>
    </main>
  )
}
