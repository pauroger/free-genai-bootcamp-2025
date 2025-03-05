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

  useEffect(() => {
    fetch(`http://127.0.0.1:5000/study-activities/${id}/launch`)
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch launch data')
        return response.json()
      })
      .then(data => {
        setLaunchData(data)
        setCurrentStudyActivity(data.activity)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [id, setCurrentStudyActivity])

  // Clean up when unmounting
  useEffect(() => {
    return () => {
      setCurrentStudyActivity(null)
    }
  }, [setCurrentStudyActivity])

  const handleLaunch = async () => {
    if (!launchData?.activity) return;
    
    // If activity is not id 1, or if a group is selected when required
    if (launchData.activity.id !== 1 || selectedGroup) {
      try {
        // For activities other than id 1, use the first group or a default
        const groupId = launchData.activity.id === 1 
          ? parseInt(selectedGroup) 
          : (launchData.groups[0]?.id || 1);
        
        // Create a study session first
        const result = await createStudySession(groupId, launchData.activity.id);
        console.log("createStudySession result:", result);
        const sessionId = result.session_id;
        
        // Replace any instances of $group_id with the actual group id and add session_id
        const launchUrl = new URL(launchData.activity.launch_url);
        launchUrl.searchParams.set('group_id', groupId.toString());
        launchUrl.searchParams.set('session_id', sessionId.toString());
        
        // Open the modified URL in a new tab
        window.open(launchUrl.toString(), '_blank');
        
        // Navigate to the session show page
        navigate(`/sessions/${sessionId}`);
      } catch (error) {
        console.error('Failed to launch activity:', error);
      }
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