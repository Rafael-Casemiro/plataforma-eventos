import axios, {
     type AxiosError,
     type AxiosInstance,
     type InternalAxiosRequestConfig
} from 'axios';

interface CustomInternalAxiosRequestConfig extends InternalAxiosRequestConfig {
     _retry?: boolean;
}

export const api: AxiosInstance = axios.create({
     baseURL: import.meta.env.VITE_API_URL,
     withCredentials: true,
     xsrfCookieName: 'csrftoken',
     xsrfHeaderName: 'X-CSRFToken',
     withXSRFToken: true
});

// Em producao, frontend e backend ficam em dominios diferentes: o JS do frontend
// nao consegue ler o cookie csrftoken (pertence ao dominio do backend), entao o
// mecanismo automatico xsrfCookieName do axios nunca funciona ali. Guardamos o
// token em memoria (obtido explicitamente no corpo de /auth/me/) e o anexamos
// manualmente. Em dev (mesmo host, portas diferentes) o xsrfCookieName acima
// já resolve sozinho, mas isso aqui funciona nos dois casos.
let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
     csrfToken = token;
}

api.interceptors.request.use((config) => {
     if (csrfToken) {
          config.headers.set('X-CSRFToken', csrfToken);
     }
     return config;
});

let isRefreshing = false;
let failedQueue: Array<{
     resolve: (value?: unknown) => void;
     reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null = null): void => {
     failedQueue.forEach((prom) => {
          if (error) {
               prom.reject(error);
          } else {
               prom.resolve();
          }
     });
     failedQueue = [];
};

api.interceptors.response.use(
     (response) => response,
     async (error: AxiosError) => {
          const originalRequest = error.config as CustomInternalAxiosRequestConfig | undefined;

          if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
               if (originalRequest.url?.includes('/auth/refresh/')) {
                    return Promise.reject(error);
               }

               originalRequest._retry = true;

               if (isRefreshing) {
                    return new Promise((resolve, reject) => {
                         failedQueue.push({resolve, reject});
                    })
                         .then(() => api(originalRequest))
                         .catch((err: unknown) => Promise.reject(err));
               }
               isRefreshing = true;

               try {
                    await api.post('/auth/refresh/');
                    processQueue(null);
                    return await api(originalRequest);
               } catch (refreshError) {
                    processQueue(refreshError as AxiosError);
                    return Promise.reject(refreshError);
               } finally {
                    isRefreshing = false;
               }
          }
          return Promise.reject(error);
     }
)