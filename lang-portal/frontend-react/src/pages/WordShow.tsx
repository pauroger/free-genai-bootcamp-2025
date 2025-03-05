import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchWordDetails, type Word } from '../services/api'
import { useNavigation } from '../context/NavigationContext'
import { Button } from '@/components/ui/button'

export default function WordShow() {
  const { id } = useParams<{ id: string }>()
  const [word, setWord] = useState<Word | null>(null)
  const { setCurrentWord } = useNavigation()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadWord = async () => {
      if (!id) return
      
      setIsLoading(true)
      setError(null)
      try {
        const wordData = await fetchWordDetails(parseInt(id, 10))
        setWord(wordData)
        setCurrentWord(wordData)
      } catch (err) {
        setError('Failed to load word details')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }

    loadWord()
  }, [id, setCurrentWord])

  useEffect(() => {
    return () => {
      setCurrentWord(null)
    }
  }, [setCurrentWord])

  if (isLoading) {
    return <div className="text-center py-4 text-muted-foreground">Loading...</div>
  }

  if (error || !word) {
    return <div className="text-destructive text-center py-4">{error || 'Word not found'}</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-foreground">Word Details</h1>
        <Button variant="outline" asChild>
          <Link to="/words">
            Back to Words
          </Link>
        </Button>
      </div>

      <div className="bg-card text-card-foreground rounded-lg shadow overflow-hidden border border-border">
        <div className="p-6 space-y-4">

          <div>
            <h2 className="text-lg font-semibold text-foreground">German</h2>
            <p className="mt-1 text-xl text-card-foreground">{word.german}</p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-foreground">English</h2>
            <p className="mt-1 text-xl text-card-foreground">{word.english}</p>
          </div>

          <div className="pt-4 border-t border-border">
            <h2 className="text-lg font-semibold text-foreground">Study Statistics</h2>
            <div className="mt-2 grid grid-cols-2 gap-4">
              <div className="p-4 bg-accent rounded-lg">
                <p className="text-sm text-muted-foreground">Correct Answers</p>
                <p className="mt-1 text-2xl font-semibold text-success-500">{word.correct_count}</p>
              </div>
              <div className="p-4 bg-accent rounded-lg">
                <p className="text-sm text-muted-foreground">Wrong Answers</p>
                <p className="mt-1 text-2xl font-semibold text-destructive">{word.wrong_count}</p>
              </div>
            </div>
          </div>

          {word.groups && word.groups.length > 0 && (
            <div className="pt-4 border-t border-border">
              <h2 className="text-lg font-semibold text-foreground">Word Groups</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {word.groups.map(group => (
                  <Link
                    key={group.id}
                    to={`/groups/${group.id}`}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary/20 text-primary hover:bg-primary/30"
                  >
                    {group.name}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}