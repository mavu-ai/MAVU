/**
 * Language Selection Component for Telegram Web App
 *
 * Shows a clean, simple language selection screen for first-time users.
 * After selection, creates a guest user automatically.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardActionArea,
  CardContent,
  CircularProgress,
  Alert,
  Stack,
} from '@mui/material';
import {
  Language as LanguageIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import axios from 'axios';
import {
  getTelegramInitData,
  getTelegramLanguageCode,
  showTelegramAlert,
  isDarkMode,
} from '../utils/telegram';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
];

interface LanguageSelectionProps {
  onComplete: (userData: {
    userId: string;
    accessToken: string;
    language: string;
  }) => void;
}

const LanguageSelection: React.FC<LanguageSelectionProps> = ({ onComplete }) => {
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const darkMode = isDarkMode();

  // Pre-select language based on Telegram user's language
  useEffect(() => {
    const telegramLang = getTelegramLanguageCode();
    const matchedLang = SUPPORTED_LANGUAGES.find(lang => lang.code === telegramLang);
    if (matchedLang) {
      setSelectedLanguage(matchedLang.code);
    }
  }, []);

  const handleLanguageSelect = async (languageCode: string) => {
    setSelectedLanguage(languageCode);
    setError(null);
    setLoading(true);

    try {
      // Get Telegram initData for authentication
      const initData = getTelegramInitData();

      if (!initData) {
        throw new Error('Telegram authentication data not available');
      }

      // Authenticate Telegram user
      const response = await axios.post(`${API_URL}/api/v1/telegram/auth`, {
        init_data: initData,
        language: languageCode,
      });

      const { user_id, telegram_id, language } = response.data;

      // Store initData and user info in localStorage (NO access token needed)
      localStorage.setItem('telegram_init_data', initData);
      localStorage.setItem('user_id', user_id);
      localStorage.setItem('telegram_id', telegram_id.toString());
      localStorage.setItem('language', language);

      // Call completion callback (no access token for Telegram users)
      onComplete({
        userId: user_id,
        accessToken: '', // Empty for Telegram users - they use initData
        language: language,
      });

    } catch (err: any) {
      console.error('Error authenticating Telegram user:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to authenticate. Please try again.';
      setError(errorMessage);
      showTelegramAlert(errorMessage);
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 4,
        }}
      >
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <LanguageIcon
            sx={{
              fontSize: 64,
              color: darkMode ? '#8774E1' : '#6c5ce7',
              mb: 2,
            }}
          />
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
            Welcome to MavuAI
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Choose your preferred language
          </Typography>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3, width: '100%' }}>
            {error}
          </Alert>
        )}

        {/* Language Grid */}
        <Stack spacing={2} sx={{ width: '100%' }}>
          {SUPPORTED_LANGUAGES.map((language) => (
            <Card
              key={language.code}
              elevation={selectedLanguage === language.code ? 4 : 1}
              sx={{
                transition: 'all 0.2s',
                border: selectedLanguage === language.code ? 2 : 0,
                borderColor: darkMode ? '#8774E1' : '#6c5ce7',
                opacity: loading && selectedLanguage !== language.code ? 0.5 : 1,
              }}
            >
              <CardActionArea
                onClick={() => !loading && handleLanguageSelect(language.code)}
                disabled={loading}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography variant="h4">{language.flag}</Typography>
                      <Box>
                        <Typography variant="h6" component="div">
                          {language.nativeName}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {language.name}
                        </Typography>
                      </Box>
                    </Box>

                    {loading && selectedLanguage === language.code ? (
                      <CircularProgress size={24} />
                    ) : selectedLanguage === language.code ? (
                      <CheckIcon
                        sx={{
                          color: darkMode ? '#8774E1' : '#6c5ce7',
                          fontSize: 32,
                        }}
                      />
                    ) : null}
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Stack>

        {/* Loading State */}
        {loading && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Setting up your account...
            </Typography>
          </Box>
        )}
      </Box>
    </Container>
  );
};

export default LanguageSelection;
