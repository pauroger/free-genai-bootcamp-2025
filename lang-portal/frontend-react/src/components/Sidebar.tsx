import * as React from "react"
import { useLocation, Link } from "react-router-dom"
import { WholeWord, Group, Home, Hourglass, BookOpenText, Settings } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

const navItems = [
  { icon: Home, name: 'Dashboard', path: '/dashboard' },
  { icon: BookOpenText, name: 'Study Activities', path: '/study-activities' },
  { icon: WholeWord, name: 'Words', path: '/words' },
  { icon: Group, name: 'Word Groups', path: '/groups' },
  { icon: Hourglass, name: 'Sessions', path: '/sessions' },
  { icon: Settings, name: 'Settings', path: '/settings' },
]

export default function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()
  
  const isActive = (path: string) => {
    // Handle root path
    if (path === '/dashboard' && location.pathname === '/') return true
    // Handle nested routes by checking if the current path starts with the nav item path
    return location.pathname.startsWith(path)
  }
  
  return (
    <Sidebar className="bg-sidebar border-r border-sidebar-border" {...props}>
      <SidebarHeader className="p-4 border-b border-sidebar-border">
        <div className="flex items-center space-x-2">
          <img 
            src="/icon.png" 
            alt="Language Portal Logo" 
            className="h-8 w-8 rounded-md shadow-sm"
          />
          <h1 className="text-xl font-bold font-heading text-sidebar-primary-foreground">
            Language Portal
          </h1>
        </div>
      </SidebarHeader>
      <SidebarContent className="py-2">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.name} className="mb-1">
                  <SidebarMenuButton 
                    asChild 
                    isActive={isActive(item.path)}
                    className={`
                      px-4 py-2 rounded-md transition-colors duration-200
                      ${isActive(item.path) 
                        ? 'bg-sidebar-accent text-sidebar-primary font-medium border-l-4 border-sidebar-primary' 
                        : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-primary-foreground'}
                    `}
                  >
                    <Link to={item.path} className="flex items-center gap-3">
                      <item.icon className={`h-5 w-5 ${isActive(item.path) ? 'text-sidebar-primary' : 'text-sidebar-foreground/70'}`} />
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail className="bg-sidebar-accent/30" />
    </Sidebar>
  )
}