import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useNavigation } from '@/context/NavigationContext'
import StudySessionsTable from '@/components/StudySessionsTable'
import Pagination from '@/components/Pagination'
import { StudySessionSortKey } from '@/components/StudySessionsTable'
import { Button } from '@/components/ui/button'

type Session = {
  id: number
  group_name: string
  group_id: number
  activity_id: number
  activity_name: string
  start_time: string
  end_time: string
  review_items_count: number
}

type StudyActivity = {
  id: number
  preview_url: string
  title: string
  description: string
  launch_url: string
}

type PaginatedSessions = {
  items: Session[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

const ITEMS_PER_PAGE = 10

export default function StudyActivityShow() {
  const { id } = useParams<{ id: string }>()
  const { setCurrentStudyActivity } = useNavigation()
  const [activity, setActivity] = useState<StudyActivity | null>(null)
  const [sessionData, setSessionData] = useState<PaginatedSessions | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<StudySessionSortKey>('start_time')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return
      
      setLoading(true)
      setError(null)
      try {
        const response = await fetch(`http://127.0.0.1:5000/study-activities/${id}`)
        if (!response.ok) {
          throw new Error('Failed to fetch study activity')
        }
        const data = await response.json()
        setActivity(data)
        setCurrentStudyActivity(data)
        
        // Fetch sessions for the current page
        const sessionsResponse = await fetch(
          `http://127.0.0.1:5000/study-activities/${id}/sessions?page=${currentPage}&per_page=${ITEMS_PER_PAGE}`
        )
        if (!sessionsResponse.ok) {
          throw new Error('Failed to fetch sessions')
        }
        const sessionsData = await sessionsResponse.json()
        setSessionData({
          items: sessionsData.items.map((item: Session) => ({
            id: item.id,
            group_name: item.group_name,
            group_id: item.group_id,
            activity_id: item.activity_id,
            activity_name: item.activity_name,
            start_time: item.start_time,
            end_time: item.end_time,
            review_items_count: item.review_items_count
          })),
          total: sessionsData.total,
          page: sessionsData.page,
          per_page: sessionsData.per_page,
          total_pages: sessionsData.total_pages
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id, currentPage, setCurrentStudyActivity])

  // Clean up when unmounting
  useEffect(() => {
    return () => {
      setCurrentStudyActivity(null)
    }
  }, [setCurrentStudyActivity])

  const handleSort = (key: StudySessionSortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  if (loading) {
    return <div className="text-center py-4 text-muted-foreground">Loading...</div>
  }

  if (error || !activity) {
    return <div className="text-destructive text-center py-4">{error || 'Activity not found'}</div>
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-foreground">{activity.title}</h1>
        <Button variant="outline" asChild>
          <Link to="/study-activities">
            Back to Activities
          </Link>
        </Button>
      </div>
      
      <div className="bg-card text-card-foreground rounded-lg shadow-md overflow-hidden border border-border">
        <div className="relative">
          <img 
            src={activity.preview_url} 
            alt={activity.title} 
            className="inset-0 w-[600px] h-[400px] aspect-ratio bg-muted"
          />
        </div>
        <div className="p-6">
          <p className="text-card-foreground mb-4">{activity.description}</p>
          <div className="space-y-4">
            <div className="flex">
              <Button asChild>
                <Link to={`/study-activities/${id}/launch`}>
                  Launch
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {sessionData && sessionData.items.length > 0 && (
        <div className="bg-card text-card-foreground rounded-lg shadow-md p-6 border border-border">
          <h2 className="text-xl font-semibold mb-4 text-foreground">Study Sessions</h2>
          <StudySessionsTable
            sessions={sessionData.items}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
          {sessionData.total_pages > 1 && (
            <div className="mt-4">
              <Pagination
                currentPage={currentPage}
                totalPages={sessionData.total_pages}
                onPageChange={setCurrentPage}
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}