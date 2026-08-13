import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './routes/ProtectedRoute'
import Login from './pages/Login'
import ListagemPublica from './pages/ListagemPublica'
import PainelOrganizador from './pages/PainelOrganizador'
import MinhasReservas from './pages/MinhasReservas'
import Portaria from './pages/Portaria'
import IngressoCompartilhado from './pages/IngressoCompartilhado'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<ListagemPublica />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/ingresso/:shareToken"
            element={<IngressoCompartilhado />}
          />
          <Route
            path="/reservas"
            element={
              <ProtectedRoute>
                <MinhasReservas />
              </ProtectedRoute>
            }
          />
          <Route
            path="/painel"
            element={
              <ProtectedRoute allowedRoles={['organizador']}>
                <PainelOrganizador />
              </ProtectedRoute>
            }
          />
          <Route
            path="/portaria"
            element={
              <ProtectedRoute allowedRoles={['portaria']}>
                <Portaria />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
