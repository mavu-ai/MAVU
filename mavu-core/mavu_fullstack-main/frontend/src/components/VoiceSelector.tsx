import React, { useState } from 'react'
import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Chip,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Avatar
} from '@mui/material'
import { useWebSocket } from '../hooks/useWebSocket'

// Voice configurations
const VOICES = [
  { value: 'shimmer', label: 'Shimmer', description: 'Warm & Expressive', gender: 'female', emoji: '✨' },
  { value: 'echo', label: 'Echo', description: 'Clear & Articulate', gender: 'male', emoji: '🔊' },
  { value: 'alloy', label: 'Alloy', description: 'Balanced & Robotic', gender: 'neutral', emoji: '🤖' },
  { value: 'coral', label: 'Coral', description: 'Bright & Cheerful', gender: 'female', emoji: '🪸' },
  { value: 'ash', label: 'Ash', description: 'Strong & Confident', gender: 'male', emoji: '🔥' },
  { value: 'ballad', label: 'Ballad', description: 'Lyrical & Musical', gender: 'female', emoji: '🎵' },
  { value: 'sage', label: 'Sage', description: 'Wise & Calm', gender: 'male', emoji: '🧙' },
  { value: 'verse', label: 'Verse', description: 'Poetic & Artistic', gender: 'female', emoji: '📝' },
  { value: 'marin', label: 'Marin', description: 'Calm & Flowing', gender: 'female', emoji: '🌊' },
  { value: 'cedar', label: 'Cedar', description: 'Deep & Grounded', gender: 'male', emoji: '🌲' }
]

// Character skins with preset voices
const CHARACTERS = [
  { id: 1, name: 'Alex', voice: 'echo', avatar: '👨‍💼', color: '#4CAF50' },
  { id: 2, name: 'Maya', voice: 'shimmer', avatar: '👩‍🎨', color: '#E91E63' },
  { id: 3, name: 'Robo', voice: 'alloy', avatar: '🤖', color: '#9C27B0' },
  { id: 4, name: 'Ash', voice: 'ash', avatar: '👨‍🚀', color: '#FF5722' },
  { id: 5, name: 'Melody', voice: 'ballad', avatar: '👩‍🎤', color: '#2196F3' },
  { id: 6, name: 'Coral', voice: 'coral', avatar: '🧜‍♀️', color: '#00BCD4' },
  { id: 7, name: 'Sage', voice: 'sage', avatar: '🧙‍♂️', color: '#607D8B' },
  { id: 8, name: 'Aria', voice: 'verse', avatar: '👩‍🎭', color: '#9E9E9E' },
  { id: 9, name: 'Marina', voice: 'marin', avatar: '🧜‍♀️', color: '#009688' },
  { id: 10, name: 'Cedar', voice: 'cedar', avatar: '🧔', color: '#795548' }
]

interface VoiceSelectorProps {
  currentVoice?: string
  mode?: 'dropdown' | 'cards' | 'characters'
}

const VoiceSelector: React.FC<VoiceSelectorProps> = ({
  currentVoice = 'shimmer',
  mode = 'dropdown'
}) => {
  const { sendMessage, lastMessage } = useWebSocket()
  const [selectedVoice, setSelectedVoice] = useState(currentVoice)
  const [changing, setChanging] = useState(false)

  // Handle voice change confirmation
  React.useEffect(() => {
    if (lastMessage?.type === 'voice.changed') {
      setSelectedVoice(lastMessage.new_voice)
      setChanging(false)
      console.log('Voice changed to:', lastMessage.new_voice)
    } else if (lastMessage?.type === 'error' && changing) {
      setChanging(false)
      console.error('Voice change error:', lastMessage.message)
    }
  }, [lastMessage, changing])

  const handleVoiceChange = (voice: string) => {
    if (voice === selectedVoice) return

    setChanging(true)
    sendMessage({
      type: 'voice.change',
      voice: voice
    })
  }

  const handleCharacterSelect = (skinId: number) => {
    setChanging(true)
    sendMessage({
      type: 'voice.change',
      skin_id: skinId
    })
  }

  // Dropdown mode
  if (mode === 'dropdown') {
    return (
      <FormControl fullWidth>
        <InputLabel>Assistant Voice</InputLabel>
        <Select
          value={selectedVoice}
          onChange={(e) => handleVoiceChange(e.target.value)}
          disabled={changing}
          label="Assistant Voice"
        >
          {VOICES.map(voice => (
            <MenuItem key={voice.value} value={voice.value}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography>{voice.emoji}</Typography>
                <Box>
                  <Typography>{voice.label}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {voice.description}
                  </Typography>
                </Box>
                <Chip
                  label={voice.gender}
                  size="small"
                  color={voice.gender === 'male' ? 'primary' : voice.gender === 'female' ? 'secondary' : 'default'}
                />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    )
  }

  // Cards mode
  if (mode === 'cards') {
    return (
      <Grid container spacing={2}>
        {VOICES.map(voice => (
          <Grid item xs={6} sm={4} md={3} key={voice.value}>
            <Card
              sx={{
                border: selectedVoice === voice.value ? '2px solid' : '1px solid',
                borderColor: selectedVoice === voice.value ? 'primary.main' : 'divider',
                opacity: changing ? 0.6 : 1
              }}
            >
              <CardActionArea
                onClick={() => handleVoiceChange(voice.value)}
                disabled={changing}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h2">{voice.emoji}</Typography>
                  <Typography variant="h6">{voice.label}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {voice.description}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={voice.gender}
                      size="small"
                      color={voice.gender === 'male' ? 'primary' : voice.gender === 'female' ? 'secondary' : 'default'}
                    />
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    )
  }

  // Characters mode
  return (
    <Grid container spacing={2}>
      {CHARACTERS.map(character => {
        const isSelected = selectedVoice === character.voice
        return (
          <Grid item xs={6} sm={4} md={3} key={character.id}>
            <Card
              sx={{
                border: isSelected ? '3px solid' : '1px solid',
                borderColor: isSelected ? character.color : 'divider',
                opacity: changing ? 0.6 : 1,
                transition: 'all 0.3s'
              }}
            >
              <CardActionArea
                onClick={() => handleCharacterSelect(character.id)}
                disabled={changing}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Avatar
                    sx={{
                      width: 80,
                      height: 80,
                      margin: '0 auto',
                      fontSize: '3rem',
                      bgcolor: character.color,
                      mb: 1
                    }}
                  >
                    {character.avatar}
                  </Avatar>
                  <Typography variant="h6">{character.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Voice: {character.voice}
                  </Typography>
                  {isSelected && (
                    <Box sx={{ mt: 1 }}>
                      <Chip label="Active" size="small" color="success" />
                    </Box>
                  )}
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        )
      }
    </Grid>
  )
}

export default VoiceSelector