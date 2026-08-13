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
}

export interface Ticket {
  id: number
  code: string
  used_at: string | null
  share_token: string
  qr_token: string
}

export interface Reservation {
  id: number
  customer: number
  event: number
  quantity: number
  status: 'pendente' | 'paga' | 'recusada' | 'cancelada'
  created_at: string
  expires_at: string
  ticket?: Ticket
}
