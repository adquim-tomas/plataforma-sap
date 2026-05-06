import axios from "axios"

export const TOKEN_KEY = "pp_token"

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export const api = axios.create({
  baseURL,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si el backend rechaza la sesión, limpiamos y mandamos al login.
    // Excepción: el propio /auth/login devuelve 401 con credenciales malas —
    // en ese caso queremos que el componente de login muestre el error
    // sin redirección masiva.
    const url: string | undefined = error.config?.url
    const isLoginRequest = url?.endsWith("/api/v1/auth/login")
    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem(TOKEN_KEY)
      if (window.location.pathname !== "/auth/login") {
        window.location.assign("/auth/login")
      }
    }
    return Promise.reject(error)
  }
)
