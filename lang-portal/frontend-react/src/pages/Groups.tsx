import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { fetchGroups, type Group } from '../services/api'
import Pagination from '../components/Pagination'

type SortKey = 'name' | 'word_count'

export default function Groups() {
  const [groups, setGroups] = useState<Group[]>([])
  const [sortKey, setSortKey] = useState<SortKey>('word_count')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadGroups = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await fetchGroups(currentPage, sortKey, sortDirection)
        setGroups(response.groups)
        setTotalPages(response.total_pages)
      } catch (err) {
        setError('Failed to load groups')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }

    loadGroups()
  }, [currentPage, sortKey, sortDirection])

  const handleSort = (key: SortKey) => {
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
      <h1 className="text-2xl font-bold text-foreground">Word Groups</h1>
      <div className="bg-card text-card-foreground rounded-lg shadow overflow-hidden border border-border">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted">
            <tr>
              {(['name', 'word_count'] as const).map((key) => (
                <th
                  key={key}
                  className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent"
                  onClick={() => handleSort(key)}
                >
                  <div className="flex items-center space-x-1">
                    <span>
                      {key === 'name' ? 'Name' : 'Word Count'}
                    </span>
                    <span className="inline-block">
                      {sortKey === key && (
                        sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                      )}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-card divide-y divide-border">
            {groups.map((group) => (
              <tr key={group.id} className="hover:bg-accent/50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link
                    to={`/groups/${group.id}`}
                    className="text-primary hover:underline"
                  >
                    {group.group_name}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                  {group.word_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </div>
  )
}