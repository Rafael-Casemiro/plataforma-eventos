import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import type { AxiosError } from 'axios'
import { useAuth } from '../context/AuthContext'

const DEMO_PASSWORD = 'senha123'
const DEMO_ACCOUNTS = [
  { label: 'Organizador', email: 'organizador1.seed@example.com' },
  { label: 'Cliente', email: 'cliente1.seed@example.com' },
  { label: 'Portaria', email: 'portaria1.seed@example.com' },
]

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

  const fillDemoAccount = (demoEmail: string) => {
    setEmail(demoEmail)
    setPassword(DEMO_PASSWORD)
    setError(null)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gradient-to-br from-emerald-50 via-paper to-paper px-4 py-10">
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

      <div className="w-full max-w-sm rounded-2xl border border-white/60 bg-white/70 p-5 shadow-lg backdrop-blur-md">
        <p className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
          Contas de demonstração
        </p>
        <p className="mt-1 text-xs text-neutral-500">
          Senha de todas: <span className="font-mono">{DEMO_PASSWORD}</span>
        </p>
        <div className="mt-3 flex flex-col gap-2">
          {DEMO_ACCOUNTS.map((account) => (
            <button
              key={account.email}
              type="button"
              onClick={() => fillDemoAccount(account.email)}
              className="flex items-center justify-between rounded-lg border border-black/10 bg-white/80 px-3 py-2 text-left text-sm transition hover:border-accent"
            >
              <span className="font-mono text-neutral-700">{account.email}</span>
              <span className="text-accent">{account.label}</span>
            </button>
          ))}
        </div>
      </div>
    </main>
  )
}
