import { Link } from 'react-router-dom'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { StudySession } from '../services/api'

export type StudySessionSortKey = 'id' | 'activity_name' | 'group_name' | 'start_time' | 'end_time' | 'review_items_count'

interface StudySessionsTableProps {
  sessions: StudySession[]
  sortKey: StudySessionSortKey
  sortDirection: 'asc' | 'desc'
  onSort: (key: StudySessionSortKey) => void
}

export default function StudySessionsTable({ 
  sessions, 
  sortKey, 
  sortDirection, 
  onSort 
}: StudySessionsTableProps) {
  return (
    <div className="bg-card rounded-lg shadow overflow-x-auto border border-border">
      <table className="min-w-full divide-y divide-border">
        <thead className="bg-muted">
          <tr>
            {(['id', 'activity_name', 'group_name', 'start_time', 'end_time', 'review_items_count'] as const).map((key) => (
              <th
                key={key}
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent"
                onClick={() => onSort(key)}
              >
                <div className="flex items-center">
                  {key === 'review_items_count' ? '# Review Items' : key.replace(/_([a-z])/g, ' $1').trim()}
                  {sortKey === key && (
                    sortDirection === 'asc' ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sessions.map((session) => (
            <tr key={session.id} className="bg-card hover:bg-accent/50">
              <td className="px-6 py-4 whitespace-nowrap">
                <Link to={`/sessions/${session.id}`} className="text-primary hover:underline">
                  {session.id}
                </Link>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Link to={`/study-activities/${session.activity_id}`} className="text-primary hover:underline">
                  {session.activity_name}
                </Link>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Link to={`/groups/${session.group_id}`} className="text-primary hover:underline">
                  {session.group_name}
                </Link>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-card-foreground">{session.start_time}</td>
              <td className="px-6 py-4 whitespace-nowrap text-card-foreground">{session.end_time}</td>
              <td className="px-6 py-4 whitespace-nowrap text-card-foreground">{session.review_items_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}