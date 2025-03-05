import { useState, useEffect } from 'react'
import { fetchWords, type Word } from '../services/api'
import WordsTable, { WordSortKey } from '../components/WordsTable'
import Pagination from '../components/Pagination'

export default function Words() {
  const [words, setWords] = useState<Word[]>([])
  const [sortKey, setSortKey] = useState<WordSortKey>('german')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadWords = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await fetchWords(currentPage, sortKey, sortDirection)
        setWords(response.words)
        setTotalPages(response.total_pages)
      } catch (err) {
        setError('Failed to load words')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }

    loadWords()
  }, [currentPage, sortKey, sortDirection])

  const handleSort = (key: WordSortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  if (isLoading) {
    return <div className="text-center py-4 text-muted-foreground">Loading...</div>
  }

  if (error) {
    return <div className="text-destructive text-center py-4">{error}</div>
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-foreground">Words</h1>
      
      <WordsTable 
        words={words}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={handleSort}
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </div>
  )
}