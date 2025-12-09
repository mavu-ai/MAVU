import React, { useState, useEffect } from 'react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Container from '@mui/material/Container'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import useMediaQuery from '@mui/material/useMediaQuery'

import VoiceChat from './components/VoiceChat'
import ContextUpload from './components/ContextUpload'
import ContextViewer from './components/ContextViewer'
import PromoCodeInput from './components/PromoCodeInput'
import Profile from './components/Profile'
import { WebSocketProvider } from './hooks/useWebSocket'
import { authService } from './services/authService'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)')
  const [tabValue, setTabValue] = useState(0)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [sessionToken, setSessionToken] = useState<string | null>(null)
  const [userId, setUserId] = useState<number | null>(null)
  const [uiMode, setUiMode] = useState<'light' | 'dark' | 'system'>('system')
  const [profileOpen, setProfileOpen] = useState(false)

  // Load UI mode preference from API
  useEffect(() => {
    const loadUiMode = async () => {
      if (!isAuthenticated) return

      try {
        const headers = authService.getAuthHeaders()
        const response = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/profile/preferences`,
          { headers: { 'Content-Type': 'application/json', ...headers } }
        )

        if (response.ok) {
          const data = await response.json()
          setUiMode(data.ui_mode || 'system')
        }
      } catch (error) {
        console.error('Failed to load UI mode:', error)
      }
    }

    loadUiMode()
  }, [isAuthenticated])

  useEffect(() => {
    // Validate existing session with backend
    const validateExistingSession = async () => {
      const authState = authService.getAuthState()

      if (!authState.isAuthenticated) {
        console.log('No local session found')
        return
      }

      console.log('Validating existing session...')
      const validationResult = await authService.validateSession()

      if (validationResult && validationResult.valid) {
        // Session is valid, update state
        setIsAuthenticated(true)
        setSessionToken(authState.sessionToken)
        setUserId(validationResult.user_id || authState.userId)
        console.log('Session validated successfully:', validationResult)
      } else {
        // Session is invalid, clear state and show promo code page
        console.log('Session validation failed, logging out')
        authService.logout()
        setIsAuthenticated(false)
        setSessionToken(null)
        setUserId(null)
      }
    }

    validateExistingSession()
  }, [])

  const handleAuthSuccess = () => {
    // Refresh auth state after successful registration
    const authState = authService.getAuthState()
    setIsAuthenticated(true)
    setSessionToken(authState.sessionToken)
    setUserId(authState.userId)
    console.log('Authentication successful:', authState)
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleUiModeChange = (mode: 'light' | 'dark' | 'system') => {
    setUiMode(mode)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setSessionToken(null)
    setUserId(null)
    setProfileOpen(false)
  }

  // Determine effective theme mode
  const effectiveMode = uiMode === 'system'
    ? (prefersDarkMode ? 'dark' : 'light')
    : uiMode

  // Create theme based on effective mode
  const theme = createTheme({
    palette: {
      mode: effectiveMode,
      primary: {
        main: '#667eea',
      },
      secondary: {
        main: '#764ba2',
      },
      background: effectiveMode === 'dark' ? {
        default: 'transparent',
        paper: 'rgba(18, 18, 18, 0.9)',
      } : {
        default: '#f5f5f5',
        paper: '#ffffff',
      },
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backdropFilter: 'blur(10px)',
          },
        },
      },
    },
  })

  // Show promo code input if not authenticated
  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <PromoCodeInput onSuccess={handleAuthSuccess} />
      </ThemeProvider>
    )
  }

  // Show full-screen VoiceChat for tab 0 (Apple Siri-style)
  if (tabValue === 0) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <WebSocketProvider sessionToken={sessionToken || undefined}>
          <VoiceChat
            uiMode={uiMode}
            onProfileClick={() => setProfileOpen(true)}
          />
          <Profile
            open={profileOpen}
            onClose={() => setProfileOpen(false)}
            uiMode={uiMode}
            onUiModeChange={handleUiModeChange}
            onLogout={handleLogout}
          />
        </WebSocketProvider>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider sessionToken={sessionToken || undefined}>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Paper elevation={3} sx={{ mb: 4, p: 3 }}>
            <Typography variant="h3" component="h1" gutterBottom align="center">
              MavuAI
            </Typography>
            <Typography variant="subtitle1" align="center" color="text.secondary">
              Real-time Voice AI with Contextual Understanding
            </Typography>
          </Paper>

          <Paper elevation={3}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="fullWidth"
            >
              <Tab label="Voice Chat" />
              <Tab label="Upload Context" />
              <Tab label="View Context" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              <VoiceChat
                uiMode={uiMode}
                onProfileClick={() => setProfileOpen(true)}
              />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <ContextUpload userId={userId?.toString() || ''} />
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <ContextViewer />
            </TabPanel>
          </Paper>

          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              User ID: {userId}
            </Typography>
          </Box>
        </Container>
        <Profile
          open={profileOpen}
          onClose={() => setProfileOpen(false)}
          uiMode={uiMode}
          onUiModeChange={handleUiModeChange}
          onLogout={handleLogout}
        />
      </WebSocketProvider>
    </ThemeProvider>
  )
}

export default App