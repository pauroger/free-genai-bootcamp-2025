import { useState } from 'react'
import { useTheme } from '@/components/theme-provider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function Settings() {
  const { theme, setTheme } = useTheme()
  const [showResetDialog, setShowResetDialog] = useState(false)
  const [resetConfirmation, setResetConfirmation] = useState('')

  const handleReset = async () => {
    if (resetConfirmation.toLowerCase() === 'reset me') {
      try {
        const response = await fetch('http://127.0.0.1:5000/study_sessions/reset', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to reset history');
        }

        // Reset was successful
        setShowResetDialog(false);
        setResetConfirmation('');
        
        // Show success message
        alert('Study history has been cleared successfully');
      } catch (error) {
        console.error('Error resetting history:', error);
        alert('Failed to reset history. Please try again.');
      }
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Settings</h1>
      
      <div className="flex items-center justify-between p-4 bg-card rounded-lg border border-border">
        <span className="text-card-foreground">Theme</span>
        <Select
          value={theme}
          onValueChange={(value) => setTheme(value as 'light' | 'dark' | 'system')}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select theme" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="light">Light</SelectItem>
            <SelectItem value="dark">Dark</SelectItem>
            <SelectItem value="system">System</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="p-4 bg-card rounded-lg border border-border">
        <h2 className="text-lg font-semibold mb-2 text-foreground">Reset Data</h2>
        <p className="mb-4 text-muted-foreground">This will reset all study history and statistics.</p>
        <Button 
          variant="destructive"
          onClick={() => setShowResetDialog(true)}
        >
          Reset History
        </Button>
      </div>

      {showResetDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card text-card-foreground p-6 rounded-lg border border-border max-w-md w-full">
            <h2 className="text-xl font-bold mb-4 text-foreground">Confirm Reset</h2>
            <p className="mb-4 text-muted-foreground">
              Type "reset me" to confirm database reset:
            </p>
            <Input
              type="text"
              value={resetConfirmation}
              onChange={(e) => setResetConfirmation(e.target.value)}
              className="mb-4"
            />
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setShowResetDialog(false)}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleReset}
              >
                Confirm Reset
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}