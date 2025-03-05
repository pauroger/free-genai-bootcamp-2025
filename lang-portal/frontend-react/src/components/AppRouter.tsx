import { Routes, Route, Navigate } from 'react-router-dom'
import { useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

import Dashboard from '@/pages/Dashboard'
import StudyActivities from '@/pages/StudyActivities'
import StudyActivityShow from '@/pages/StudyActivityShow'
import StudyActivityLaunch from '@/pages/StudyActivityLaunch'
import Words from '@/pages/Words'
import WordShow from '@/pages/WordShow'
import Groups from '@/pages/Groups'
import GroupShow from '@/pages/GroupShow'
import Sessions from '@/pages/Sessions'
import StudySessionShow from '@/pages/StudySessionShow'
import Settings from '@/pages/Settings'

function ConditionalLaunchRoute() {
  // Simply render the launch component for all IDs
  return <StudyActivityLaunch />
}

export default function AppRouter() {
  return (
    <div className="min-h-screen">
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/study-activities" element={<StudyActivities />} />
          <Route path="/study-activities/:id" element={<StudyActivityShow />} />
          <Route path="/study-activities/:id/launch" element={<ConditionalLaunchRoute />} />
          <Route path="/words" element={<Words />} />
          <Route path="/words/:id" element={<WordShow />} />
          <Route path="/groups" element={<Groups />} />
          <Route path="/groups/:id" element={<GroupShow />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/sessions/:id" element={<StudySessionShow />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
