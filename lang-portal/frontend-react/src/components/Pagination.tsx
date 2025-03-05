interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <div className="mt-4 flex justify-center space-x-2">
      <button
        onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        disabled={currentPage === 1}
        className="px-3 py-1 text-sm bg-primary/10 text-primary border border-primary/20 rounded-md 
                  hover:bg-primary/20 disabled:opacity-40 disabled:bg-muted disabled:text-muted-foreground"
      >
        Previous
      </button>
      <span className="px-3 py-1 text-sm bg-card text-card-foreground border border-border rounded-md">
        Page {currentPage} of {totalPages}
      </span>
      <button
        onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
        disabled={currentPage === totalPages}
        className="px-3 py-1 text-sm bg-primary/10 text-primary border border-primary/20 rounded-md
                  hover:bg-primary/20 disabled:opacity-40 disabled:bg-muted disabled:text-muted-foreground"
      >
        Next
      </button>
    </div>
  )
}