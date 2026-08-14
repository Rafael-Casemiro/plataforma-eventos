import { useState, type FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import type { AxiosError } from 'axios'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Cadastro() {
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)

    if (password !== passwordConfirm) {
      setError('As senhas não coincidem.')
      return
    }

    setIsSubmitting(true)

    try {
      await api.post('/auth/register/', {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        password_confirm: passwordConfirm,
      })

      // Faz login automático após o cadastro e redireciona
      await login({ email, password })
      navigate('/')
    } catch (err) {
      const axiosError = err as AxiosError<{
        detail?: string
        email?: string[]
        password?: string[]
        password_confirm?: string[]
      }>
      const data = axiosError.response?.data
      const fieldError =
        data?.email?.[0] || data?.password?.[0] || data?.password_confirm?.[0]
      setError(
        fieldError || data?.detail || 'Não foi possível realizar o cadastro. Verifique seus dados.',
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
          Criar Conta
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Cadastre-se na Plataforma de Eventos.
        </p>

        {error && (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600">
            {error}
          </p>
        )}

        <div className="mt-6 flex gap-4">
          <label className="block w-full text-sm font-medium text-neutral-700">
            Nome
            <input
              type="text"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-black/10 bg-white/80 px-3 py-2 outline-none focus:border-accent"
            />
          </label>
          <label className="block w-full text-sm font-medium text-neutral-700">
            Sobrenome
            <input
              type="text"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-black/10 bg-white/80 px-3 py-2 outline-none focus:border-accent"
            />
          </label>
        </div>

        <label className="mt-4 block text-sm font-medium text-neutral-700">
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
            minLength={8}
            className="mt-1 w-full rounded-lg border border-black/10 bg-white/80 px-3 py-2 outline-none focus:border-accent"
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-neutral-700">
          Confirmar senha
          <input
            type="password"
            value={passwordConfirm}
            onChange={(event) => setPasswordConfirm(event.target.value)}
            required
            minLength={8}
            className="mt-1 w-full rounded-lg border border-black/10 bg-white/80 px-3 py-2 outline-none focus:border-accent"
          />
        </label>

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-6 w-full rounded-lg bg-accent py-2 font-medium text-white transition disabled:opacity-60"
        >
          {isSubmitting ? 'Cadastrando...' : 'Cadastrar'}
        </button>

        <p className="mt-4 text-center text-sm text-neutral-500">
          Já tem uma conta?{' '}
          <Link to="/login" className="text-accent hover:underline">
            Fazer login
          </Link>
        </p>
      </form>
    </main>
  )
}
