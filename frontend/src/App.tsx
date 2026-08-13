import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './routes/ProtectedRoute'
import Login from './pages/Login'
import ListagemPublica from './pages/ListagemPublica'
import PainelOrganizador from './pages/PainelOrganizador'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<ListagemPublica />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/painel"
            element={
              <ProtectedRoute allowedRoles={['organizador']}>
                <PainelOrganizador />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
