import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useNavigation } from '@/context/NavigationContext'
import { createStudySession } from '@/services/api'

type Group = {
  id: number
  name: string
}

type StudyActivity = {
  id: number
  title: string
  launch_url: string
  preview_url: string
}

type LaunchData = {
  activity: StudyActivity
  groups: Group[]
}

export default function StudyActivityLaunch() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { setCurrentStudyActivity } = useNavigation()
  const [launchData, setLaunchData] = useState<LaunchData | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Add debug logging
  console.log("StudyActivityLaunch mounted, id:", id)

  useEffect(() => {
    console.log("Fetching launch data for activity:", id)
    fetch(`http://127.0.0.1:5000/study-activities/${id}/launch`)
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch launch data')
        return response.json()
      })
      .then(data => {
        console.log("Received launch data:", data)
        setLaunchData(data)
        setCurrentStudyActivity(data.activity)
        setLoading(false)
        
        // For non-ID-1 activities, pre-select the first group
        if (data.activity.id !== 1 && data.groups && data.groups.length > 0) {
          setSelectedGroup(data.groups[0].id.toString())
        }
      })
      .catch(err => {
        console.error("Error fetching launch data:", err)
        setError(err.message)
        setLoading(false)
      })
  }, [id, setCurrentStudyActivity])

  useEffect(() => {
    return () => {
      setCurrentStudyActivity(null)
    }
  }, [setCurrentStudyActivity])

  const handleLaunch = async () => {
    console.log("Launch button clicked")
    
    if (!launchData?.activity) {
      console.error("No activity data available")
      return
    }
    
    console.log("Launch data:", launchData)
    console.log("Selected group:", selectedGroup)
    
    try {
      // For activities other than id 1, use first group or default
      const groupId = launchData.activity.id === 1 
        ? parseInt(selectedGroup) 
        : (launchData.groups[0]?.id || 1)
      
      console.log("Using group ID:", groupId)
      
      // Create study session
      const result = await createStudySession(groupId, launchData.activity.id)
      console.log("Study session created:", result)
      
      if (!result || !result.session_id) {
        throw new Error("Failed to get session ID from API")
      }
      
      const sessionId = result.session_id
      
      // Build launch URL
      let launchUrlString = launchData.activity.launch_url
      try {
        const launchUrl = new URL(launchUrlString)
        launchUrl.searchParams.set('group_id', groupId.toString())
        launchUrl.searchParams.set('session_id', sessionId.toString())
        launchUrlString = launchUrl.toString()
      } catch (urlError) {
        console.error("URL parsing error:", urlError)
        // Fallback for invalid URLs
        launchUrlString = `${launchData.activity.launch_url}?group_id=${groupId}&session_id=${sessionId}`
      }
      
      console.log("Opening URL:", launchUrlString)
      window.open(launchUrlString, '_blank')
      
      // Delay navigation slightly to ensure window.open works
      setTimeout(() => {
        console.log("Navigating to session:", sessionId)
        navigate(`/sessions/${sessionId}`)
      }, 100)
    } catch (error) {
      console.error('Failed to launch activity:', error)
      setError(`Launch failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  if (loading) {
    return <div className="text-center text-muted-foreground">Loading...</div>
  }

  if (error) {
    return <div className="text-destructive">Error: {error}</div>
  }

  if (!launchData) {
    return <div className="text-destructive">Activity not found</div>
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-foreground">{launchData.activity.title}</h1>
      
      <div className="space-y-4">
        {launchData.activity.id === 1 ? (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Select Word Group</label>
              <Select onValueChange={setSelectedGroup} value={selectedGroup}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a word group" />
                </SelectTrigger>
                <SelectContent>
                  {launchData.groups.map((group) => (
                    <SelectItem key={group.id} value={group.id.toString()}>
                      {group.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button 
              onClick={handleLaunch}
              disabled={!selectedGroup}
              className="w-full"
            >
              Launch Now
            </Button>
          </>
        ) : (
          <Button 
            onClick={handleLaunch}
            className="w-full"
          >
            Launch Now
          </Button>
        )}
      </div>
    </div>
  )
}