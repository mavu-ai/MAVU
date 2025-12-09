import React, { useState, useEffect } from 'react'
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Divider,
  Grid,
} from '@mui/material'
import { authService } from '../services/authService'

interface ProfileProps {
  open: boolean
  onClose: () => void
  uiMode?: string
  onUiModeChange: (mode: 'light' | 'dark' | 'system') => void
  onLogout?: () => void
}

interface UserPreferences {
  language: string
  night_mode: boolean
  skin_id: number
  ui_mode: string
}

const Profile: React.FC<ProfileProps> = ({ open, onClose, onUiModeChange, onLogout }) => {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [preferences, setPreferences] = useState<UserPreferences>({
    language: 'en',
    night_mode: false,
    skin_id: 1,
    ui_mode: 'system',
  })
  const [originalSkinId, setOriginalSkinId] = useState<number>(1)

  useEffect(() => {
    if (open) {
      loadPreferences()
    }
  }, [open])

  const loadPreferences = async () => {
    setLoading(true)
    setError(null)

    try {
      const headers = authService.getAuthHeaders()
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/profile/preferences`,
        {
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to load preferences')
      }

      const data = await response.json()
      setPreferences(data)
      setOriginalSkinId(data.skin_id)
    } catch (err) {
      console.error('Error loading preferences:', err)
      setError('Failed to load preferences')
    } finally {
      setLoading(false)
    }
  }

  const savePreferences = async () => {
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const headers = authService.getAuthHeaders()
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/profile/preferences`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
          body: JSON.stringify(preferences),
        }
      )

      if (!response.ok) {
        throw new Error('Failed to save preferences')
      }

      const data = await response.json()
      const voiceChanged = data.skin_id !== originalSkinId

      console.log('Preferences saved:', {
        originalSkinId,
        newSkinId: data.skin_id,
        voiceChanged,
        allPreferences: data
      })

      setPreferences(data)
      setOriginalSkinId(data.skin_id)

      // Update UI mode in parent component
      onUiModeChange(data.ui_mode)

      if (voiceChanged) {
        setSuccess('Voice changed! PLEASE REFRESH THE PAGE (F5 or Ctrl+R) to apply the new voice.')
        console.warn('Voice changed! User must refresh page to hear new voice.')
        // Don't auto-close so user can see the message
      } else {
        setSuccess('Preferences saved!')
        // Close after a brief moment so user sees the success message
        setTimeout(() => {
          onClose()
        }, 800)
      }
    } catch (err) {
      console.error('Error saving preferences:', err)
      setError('Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  const handleUiModeChange = (mode: string) => {
    setPreferences({ ...preferences, ui_mode: mode })
  }

  const handleLogout = () => {
    authService.logout()
    if (onLogout) {
      onLogout()
    } else {
      // Fallback: reload the page
      window.location.reload()
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Profile & Preferences</DialogTitle>
      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ pt: 2 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
                {success}
              </Alert>
            )}

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Appearance
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>UI Theme</InputLabel>
                  <Select
                    value={preferences.ui_mode}
                    label="UI Theme"
                    onChange={(e) => handleUiModeChange(e.target.value)}
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="system">System (Auto)</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Choose your preferred theme or follow system settings
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Language & Settings
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={preferences.language}
                    label="Language"
                    onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Español</MenuItem>
                    <MenuItem value="fr">Français</MenuItem>
                    <MenuItem value="de">Deutsch</MenuItem>
                    <MenuItem value="it">Italiano</MenuItem>
                    <MenuItem value="pt">Português</MenuItem>
                    <MenuItem value="ru">Русский</MenuItem>
                    <MenuItem value="zh">中文</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Character Voice</InputLabel>
                  <Select
                    value={preferences.skin_id}
                    label="Character Voice"
                    onChange={(e) => setPreferences({ ...preferences, skin_id: Number(e.target.value) })}
                  >
                    <MenuItem value={1}>Alex - Clear and articulate (Male)</MenuItem>
                    <MenuItem value={2}>Maya - Warm and expressive (Female)</MenuItem>
                    <MenuItem value={3}>Robo - Balanced and robotic (Neutral)</MenuItem>
                    <MenuItem value={4}>Ash - Strong and confident (Male)</MenuItem>
                    <MenuItem value={5}>Melody - Lyrical and musical (Female)</MenuItem>
                    <MenuItem value={6}>Coral - Bright and cheerful (Female)</MenuItem>
                    <MenuItem value={7}>Sage - Wise and calm (Male)</MenuItem>
                    <MenuItem value={8}>Aria - Poetic and artistic (Female)</MenuItem>
                    <MenuItem value={9}>Marina - Calm and flowing (Female)</MenuItem>
                    <MenuItem value={10}>Cedar - Deep and grounded (Male)</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Choose your AI assistant character and voice style
                </Typography>
              </Grid>
            </Grid>
          </Box>
        )}
      </DialogContent>
      <DialogActions sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}>
        <Button
          onClick={handleLogout}
          color="error"
          disabled={saving}
        >
          Logout
        </Button>
        <Box>
          <Button onClick={onClose} disabled={saving} sx={{ mr: 1 }}>
            Cancel
          </Button>
          <Button
            onClick={savePreferences}
            variant="contained"
            disabled={loading || saving}
            startIcon={saving && <CircularProgress size={20} />}
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  )
}

export default Profile
