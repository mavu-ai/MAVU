import React, { useState } from 'react'
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Card,
  CardContent,
} from '@mui/material'
import { LockOpen, CheckCircle } from '@mui/icons-material'
import { authService } from '../services/authService'

interface PromoCodeInputProps {
  onSuccess: () => void
}

const PromoCodeInput: React.FC<PromoCodeInputProps> = ({ onSuccess }) => {
  const [promoCode, setPromoCode] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!promoCode.trim()) {
      setError('Please enter a promo code')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await authService.register(promoCode)
      console.log('Registration successful:', response)

      setSuccess(true)

      // Wait a moment to show success message, then proceed
      setTimeout(() => {
        onSuccess()
      }, 1500)
    } catch (err) {
      console.error('Registration error:', err)
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.')
      setIsSubmitting(false)
    }
  }

  if (success) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          p: 2,
        }}
      >
        <Card sx={{ maxWidth: 500, width: '100%' }}>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle color="success" sx={{ fontSize: 80, mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Welcome to MavuAI!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Your account has been created successfully.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        p: 2,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card sx={{ maxWidth: 500, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <LockOpen sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom fontWeight="bold">
              Welcome to MavuAI
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Enter your promo code to get started with your AI companion
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Promo Code"
              variant="outlined"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
              disabled={isSubmitting}
              placeholder="Enter your promo code"
              autoFocus
              sx={{ mb: 3 }}
              inputProps={{
                style: { textTransform: 'uppercase' }
              }}
            />

            <Button
              fullWidth
              variant="contained"
              size="large"
              type="submit"
              disabled={isSubmitting || !promoCode.trim()}
              sx={{
                py: 1.5,
                fontSize: '1.1rem',
                fontWeight: 'bold',
              }}
            >
              {isSubmitting ? (
                <>
                  <CircularProgress size={24} sx={{ mr: 1 }} color="inherit" />
                  Activating...
                </>
              ) : (
                'Start My Journey'
              )}
            </Button>
          </form>

          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Don't have a promo code? Contact us to get one!
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

export default PromoCodeInput
