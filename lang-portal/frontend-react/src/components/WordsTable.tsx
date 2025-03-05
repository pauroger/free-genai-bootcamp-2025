import { Link } from 'react-router-dom'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { Word } from '../services/api'

export type WordSortKey = 'german' | 'english' | 'correct_count' | 'wrong_count'

interface WordsTableProps {
  words: Word[]
  sortKey: WordSortKey
  sortDirection: 'asc' | 'desc'
  onSort: (key: WordSortKey) => void
}

export default function WordsTable({ words, sortKey, sortDirection, onSort }: WordsTableProps) {
  return (
    <div className="overflow-x-auto bg-card rounded-lg shadow border border-border">
      <table className="min-w-full divide-y divide-border">
        <thead className="bg-muted">
          <tr>
            {(['german', 'english', 'correct_count', 'wrong_count'] as const).map((key) => (
              <th
                key={key}
                className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent"
                onClick={() => onSort(key)}
              >
                <div className="flex items-center space-x-1">
                  <span>
                    {key === 'correct_count' ? 'Correct' :
                     key === 'wrong_count' ? 'Wrong' :
                     key.charAt(0).toUpperCase() + key.slice(1)}
                  </span>
                  {sortKey === key && (
                    sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-card divide-y divide-border">
          {words.map((word) => (
            <tr key={word.id} className="hover:bg-accent/50">
              <td className="px-6 py-4 whitespace-nowrap">
                <Link
                  to={`/words/${word.id}`}
                  className="text-primary hover:underline"
                >
                  {word.german}
                </Link>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                {word.english}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-success-500 font-medium">
                {word.correct_count}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-destructive font-medium">
                {word.wrong_count}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}