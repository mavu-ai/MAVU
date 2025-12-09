import React from 'react'
import { Box, Paper, Typography, Divider } from '@mui/material'
import { Person, SmartToy } from '@mui/icons-material'

interface TranscriptionDisplayProps {
  userText: string
  assistantText: string
  isProcessing: boolean
}

const TranscriptionDisplay: React.FC<TranscriptionDisplayProps> = ({
  userText,
  assistantText,
  isProcessing,
}) => {
  return (
    <Paper sx={{ p: 2, minHeight: 200, maxHeight: 400, overflow: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        Conversation
      </Typography>
      <Divider sx={{ mb: 2 }} />

      {userText && (
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Person sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="subtitle2" color="primary">
              You
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ pl: 4 }}>
            {userText}
          </Typography>
        </Box>
      )}

      {assistantText && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <SmartToy sx={{ mr: 1, color: 'secondary.main' }} />
            <Typography variant="subtitle2" color="secondary">
              Assistant
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ pl: 4 }}>
            {assistantText}
            {isProcessing && !assistantText && (
              <Box
                component="span"
                sx={{
                  animation: 'blink 1s infinite',
                  '@keyframes blink': {
                    '0%, 50%': { opacity: 1 },
                    '51%, 100%': { opacity: 0 },
                  },
                }}
              >
                ▊
              </Box>
            )}
          </Typography>
        </Box>
      )}

      {!userText && !assistantText && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 8 }}>
          Start talking to begin the conversation...
        </Typography>
      )}
    </Paper>
  )
}

export default TranscriptionDisplay