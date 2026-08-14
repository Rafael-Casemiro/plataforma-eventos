import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import type { AxiosError } from 'axios'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from =
    (location.state as { from?: { pathname: string } } | null)?.from
      ?.pathname ?? '/'

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await login({ email, password })
      navigate(from, { replace: true })
    } catch (err) {
      const axiosError = err as AxiosError<{ non_field_errors?: string[] }>
      setError(
        axiosError.response?.data?.non_field_errors?.[0] ??
          'Email ou senha inválidos.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 via-paper to-paper px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-2xl border border-white/60 bg-white/70 p-8 shadow-lg backdrop-blur-md"
      >
        <h1 className="font-display text-2xl font-semibold text-neutral-900">
          Entrar
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Acesse sua conta para continuar.
        </p>

        {error && (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600">
            {error}
          </p>
        )}

        <label className="mt-6 block text-sm font-medium text-neutral-700">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            className="mt-1 w-full rounded-lg border border-black/10 bg-white/80 px-3 py-2 outline-none focus:border-accent"
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-neutral-700">
          Senha
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            className="mt-1 w-full rounded-lg border border-black/10 bg-white/80 px-3 py-2 outline-none focus:border-accent"
          />
        </label>

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-6 w-full rounded-lg bg-accent py-2 font-medium text-white transition disabled:opacity-60"
        >
          {isSubmitting ? 'Entrando...' : 'Entrar'}
        </button>

        <p className="mt-4 text-center text-sm text-neutral-500">
          Ainda não tem uma conta?{' '}
          <Link to="/cadastro" className="text-accent hover:underline">
            Cadastre-se
          </Link>
        </p>
      </form>
    </main>
  )
}
