export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TmdbMovie {
  id: number
  titulo: string
  sinopse: string
  data_lancamento: string
  nota: number
  poster_path: string
}

export interface Event {
  id: number
  title: string
  organizer: number
  description: string
  date: string
  location: string
  capacity: number
  price: string
  external_ref: number
  external_title: string
  poster_path: string
  is_published: boolean
  created_at: string
  updated_at: string
  vagas_disponiveis: number
}

export interface Ticket {
  id: number
  code: string
  used_at: string | null
  share_token: string
  qr_token: string
  short_code: string
}

export interface Reservation {
  id: number
  customer: number
  event: number
  event_title: string
  event_date: string
  event_location: string
  event_poster_path: string
  quantity: number
  status: 'pendente' | 'paga' | 'recusada' | 'cancelada'
  created_at: string
  expires_at: string
  tickets: Ticket[]
}

export interface SharedTicket {
  title: string
  date: string
  location: string
  poster_path: string
  quantity: number
}
