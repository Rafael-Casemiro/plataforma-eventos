interface PaginationProps {
  page: number
  count: number
  pageSize: number
  hasNext: boolean
  hasPrevious: boolean
  onPageChange: (page: number) => void
}

export function Pagination({
  page,
  count,
  pageSize,
  hasNext,
  hasPrevious,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.max(Math.ceil(count / pageSize), 1)

  if (totalPages <= 1) {
    return null
  }

  return (
    <div className="mt-8 flex items-center justify-center gap-4">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={!hasPrevious}
        className="rounded-lg border border-black/10 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Anterior
      </button>
      <span className="text-sm text-neutral-500">
        Página {page} de {totalPages}
      </span>
      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={!hasNext}
        className="rounded-lg border border-black/10 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Próxima
      </button>
    </div>
  )
}
