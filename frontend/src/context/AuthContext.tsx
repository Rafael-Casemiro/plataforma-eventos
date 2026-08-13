import {
     createContext,
     useContext,
     useEffect,
     useState,
     type ReactNode,
} from 'react';

import { api } from '../api/client';

interface User {
     id: number;
     email: string;
     first_name: string;
     last_name: string;
     role: 'organizador' | 'cliente' | 'portaria';
}

interface LoginData {
     email: string;
     password: string;
}

interface AuthContextData {
     user: User | null;
     isAuthenticated: boolean;
     isLoading: boolean;
     login: (data: LoginData) => Promise<void>;
     logout: () => Promise<void>
}

interface AuthProviderProps {
     children: ReactNode;
}

const AuthContext = createContext<AuthContextData | undefined>(undefined);


export function AuthProvider({ children }: AuthProviderProps) {
     const [user, setUser] = useState<User | null>(null);
     const [isLoading, setIsLoading] = useState(true);

     const isAuthenticated = user !== null;

     const loadUser = async () => {
          try {
               const response = await api.get<{ user: User }>('/auth/me/');
               setUser(response.data.user);
          } catch {
               setUser(null);
          } finally {
               setIsLoading(false);
          }
     };

     const login = async (data: LoginData) => {
          await api.post('/auth/login/', data);
          await loadUser();
     }

     const logout = async () => {
          try {
               await api.post('/auth/logout/');
          } finally {
               setUser(null);
          }
     };

     useEffect(() => {
          loadUser();
     }, []);

     return (
          <AuthContext.Provider
               value={{
                    user,
                    isAuthenticated,
                    isLoading,
                    login,
                    logout,
               }}
          >
               {children}
          </AuthContext.Provider>
     );
}

export function useAuth(): AuthContextData {
     const context = useContext(AuthContext);

     if(!context) {
          throw new Error('useAuth must be used within an AuthProvider');
     }

     return context;
}