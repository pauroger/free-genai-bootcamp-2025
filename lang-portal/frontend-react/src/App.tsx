import { ThemeProvider } from "@/components/theme-provider"
import { BrowserRouter as Router } from 'react-router-dom'
import AppSidebar from '@/components/Sidebar'
import Breadcrumbs from '@/components/Breadcrumbs'
import AppRouter from '@/components/AppRouter'
import { NavigationProvider } from '@/context/NavigationContext'

import {
  SidebarInset,
  SidebarProvider
} from "@/components/ui/sidebar"

export default function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="language-portal-theme">
      <NavigationProvider>
        <Router>
          <SidebarProvider>
            <AppSidebar />
            <SidebarInset className="px-6 py-4">
              <Breadcrumbs />
              <div className="pt-4">
                <AppRouter />
              </div>
            </SidebarInset>
          </SidebarProvider>  
        </Router>
      </NavigationProvider>
    </ThemeProvider>
  )
}