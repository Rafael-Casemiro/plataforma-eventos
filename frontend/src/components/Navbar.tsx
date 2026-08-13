import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Navbar() {
  const { user, logout } = useAuth()

  return (
    <nav className="sticky top-0 z-10 border-b border-black/10 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link
          to="/"
          className="font-display text-xl font-semibold text-neutral-900"
        >
          Em Cartaz<span className="text-accent">.</span>
        </Link>

        <div className="flex items-center gap-5 text-sm">
          {user ? (
            <>
              <Link
                to="/reservas"
                className="font-medium text-neutral-600 hover:text-accent"
              >
                Minhas reservas
              </Link>
              {user.role === 'organizador' && (
                <Link
                  to="/painel"
                  className="font-medium text-neutral-600 hover:text-accent"
                >
                  Meu painel
                </Link>
              )}
              {user.role === 'portaria' && (
                <Link
                  to="/portaria"
                  className="font-medium text-neutral-600 hover:text-accent"
                >
                  Portaria
                </Link>
              )}
              <span className="hidden text-neutral-300 sm:inline">|</span>
              <span className="hidden text-neutral-500 sm:inline">
                {user.first_name}
              </span>
              <button
                type="button"
                onClick={() => logout()}
                className="font-medium text-neutral-500 hover:text-neutral-900"
              >
                Sair
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="rounded-lg bg-accent px-4 py-2 font-medium text-white transition-colors hover:bg-neutral-800"
            >
              Entrar
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
