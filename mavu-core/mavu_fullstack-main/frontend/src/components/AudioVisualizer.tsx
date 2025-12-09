import React from 'react'
import { Box } from '@mui/material'

interface AudioVisualizerProps {
  level: number // 0 to 1
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ level }) => {
  const bars = 20
  const barHeight = level * 100

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 0.5,
        height: 100,
        mb: 2,
      }}
    >
      {Array.from({ length: bars }).map((_, index) => {
        const offset = Math.abs(index - bars / 2)
        const heightMultiplier = 1 - offset / (bars / 2)
        const animationDelay = index * 0.05

        return (
          <Box
            key={index}
            sx={{
              width: 4,
              height: `${barHeight * heightMultiplier}%`,
              minHeight: 4,
              bgcolor: 'primary.main',
              borderRadius: 2,
              transition: 'height 0.1s ease',
              animation: level > 0.1 ? 'pulse 1s infinite' : 'none',
              animationDelay: `${animationDelay}s`,
              '@keyframes pulse': {
                '0%, 100%': {
                  opacity: 0.5,
                  transform: 'scaleY(0.8)',
                },
                '50%': {
                  opacity: 1,
                  transform: 'scaleY(1)',
                },
              },
            }}
          />
        )
      })}
    </Box>
  )
}

export default AudioVisualizer