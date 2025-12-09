import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  List,
  ListItem,
  Chip,
  TextField,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material'
import { Search, Refresh } from '@mui/icons-material'
import { useWebSocket } from '../hooks/useWebSocket'

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
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  )
}

const ContextViewer: React.FC = () => {
  const { sendMessage, lastMessage, isConnected } = useWebSocket()
  const [tabValue, setTabValue] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [userContext, setUserContext] = useState<any[]>([])
  const [appContext, setAppContext] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (lastMessage?.type === 'context.refreshed') {
      setUserContext(lastMessage.context?.user_context || [])
      setAppContext(lastMessage.context?.app_context || [])
      setIsSearching(false)
    }
  }, [lastMessage])

  const handleSearch = () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setError(null)
    sendMessage({
      type: 'context.refresh',
      query: searchQuery
    })
  }

  const handleRefresh = () => {
    handleSearch()
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Context Explorer
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Search and explore the context stored in the vector database.
      </Typography>

      {/* Search Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Enter search query to retrieve context..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            disabled={!isConnected}
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            startIcon={isSearching ? <CircularProgress size={20} /> : <Search />}
            disabled={!isConnected || isSearching || !searchQuery.trim()}
          >
            Search
          </Button>
          <Button
            variant="outlined"
            onClick={handleRefresh}
            startIcon={<Refresh />}
            disabled={!isConnected || isSearching}
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Context Tabs */}
      <Paper>
        <Tabs
          value={tabValue}
          onChange={(_e, newValue) => setTabValue(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Personal Context
                {userContext.length > 0 && (
                  <Chip label={userContext.length} size="small" />
                )}
              </Box>
            }
          />
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                App Context
                {appContext.length > 0 && (
                  <Chip label={appContext.length} size="small" />
                )}
              </Box>
            }
          />
        </Tabs>

        {/* Personal Context Tab */}
        <TabPanel value={tabValue} index={0}>
          {userContext.length > 0 ? (
            <List>
              {userContext.map((item, index) => (
                <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', mb: 2 }}>
                  <Paper elevation={1} sx={{ p: 2, width: '100%' }}>
                    <Typography variant="body2" paragraph>
                      {item.text}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {item.source && (
                        <Chip label={`Source: ${item.source}`} size="small" variant="outlined" />
                      )}
                      {item.score !== undefined && (
                        <Chip
                          label={`Score: ${item.score.toFixed(3)}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                      {item.metadata && Object.entries(item.metadata).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}: ${value}`}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Paper>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              {searchQuery
                ? 'No personal context found for this query.'
                : 'Enter a search query to retrieve personal context.'}
            </Typography>
          )}
        </TabPanel>

        {/* App Context Tab */}
        <TabPanel value={tabValue} index={1}>
          {appContext.length > 0 ? (
            <List>
              {appContext.map((item, index) => (
                <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', mb: 2 }}>
                  <Paper elevation={1} sx={{ p: 2, width: '100%' }}>
                    <Typography variant="body2" paragraph>
                      {item.text}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {item.source && (
                        <Chip label={`Source: ${item.source}`} size="small" variant="outlined" />
                      )}
                      {item.category && (
                        <Chip
                          label={`Category: ${item.category}`}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      )}
                      {item.score !== undefined && (
                        <Chip
                          label={`Score: ${item.score.toFixed(3)}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                      {item.metadata && Object.entries(item.metadata).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}: ${value}`}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Paper>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              {searchQuery
                ? 'No application context found for this query.'
                : 'Enter a search query to retrieve application context.'}
            </Typography>
          )}
        </TabPanel>
      </Paper>

      {/* Stats */}
      {(userContext.length > 0 || appContext.length > 0) && (
        <Paper sx={{ mt: 3, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Search Statistics
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Typography variant="body2">
              Total Results: {userContext.length + appContext.length}
            </Typography>
            <Typography variant="body2">
              Query: "{searchQuery}"
            </Typography>
          </Box>
        </Paper>
      )}
    </Box>
  )
}

export default ContextViewer