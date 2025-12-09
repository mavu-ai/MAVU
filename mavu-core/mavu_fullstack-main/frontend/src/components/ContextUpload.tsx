import React, { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
  Chip,
  Paper,
} from '@mui/material'
import { CloudUpload, TextFields, Description } from '@mui/icons-material'
import axios from 'axios'

interface ContextUploadProps {
  userId: string
}

const ContextUpload: React.FC<ContextUploadProps> = ({ userId }) => {
  const [uploadType, setUploadType] = useState<'user' | 'app'>('user')
  const [inputType, setInputType] = useState<'text' | 'file'>('text')
  const [textContent, setTextContent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [category, setCategory] = useState('general')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0])
      setError(null)
    }
  }

  const handleUpload = async () => {
    setIsUploading(true)
    setError(null)
    setUploadResult(null)

    try {
      const endpoint = uploadType === 'user'
        ? '/api/v1/context/user/upload'
        : '/api/v1/context/app/upload'

      if (inputType === 'text') {
        const response = await axios.post(`${endpoint}/json`, {
          text: textContent,
          metadata: {
            upload_time: new Date().toISOString(),
            category: category,
          },
          source: 'manual_input'
        }, {
          headers: {
            'X-User-Id': userId,
            'Content-Type': 'application/json'
          }
        })

        setUploadResult(response.data)
        setTextContent('')
      } else {
        if (!selectedFile) {
          setError('Please select a file')
          setIsUploading(false)
          return
        }

        const formData = new FormData()
        formData.append('file', selectedFile)
        formData.append('source', 'file_upload')
        formData.append('category', category)
        formData.append('metadata', JSON.stringify({
          upload_time: new Date().toISOString(),
          filename: selectedFile.name,
        }))

        const response = await axios.post(endpoint, formData, {
          headers: {
            'X-User-Id': userId,
            'Content-Type': 'multipart/form-data'
          }
        })

        setUploadResult(response.data)
        setSelectedFile(null)
      }
    } catch (err: any) {
      console.error('Upload error:', err)
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Upload Context Documents
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Upload documents to enhance the AI's knowledge. User context is personal to you,
        while app context is shared across all users.
      </Typography>

      {/* Upload Type Selection */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant={uploadType === 'user' ? 'contained' : 'outlined'}
          onClick={() => setUploadType('user')}
          color="primary"
        >
          Personal Context
        </Button>
        <Button
          variant={uploadType === 'app' ? 'contained' : 'outlined'}
          onClick={() => setUploadType('app')}
          color="secondary"
        >
          App Context (Admin)
        </Button>
      </Box>

      {/* Input Type Selection */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant={inputType === 'text' ? 'contained' : 'outlined'}
          onClick={() => setInputType('text')}
          startIcon={<TextFields />}
          size="small"
        >
          Text Input
        </Button>
        <Button
          variant={inputType === 'file' ? 'contained' : 'outlined'}
          onClick={() => setInputType('file')}
          startIcon={<Description />}
          size="small"
        >
          File Upload
        </Button>
      </Box>

      <Card>
        <CardContent>
          {/* Category Selection (for app context) */}
          {uploadType === 'app' && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                label="Category"
              >
                <MenuItem value="general">General</MenuItem>
                <MenuItem value="technical">Technical</MenuItem>
                <MenuItem value="business">Business</MenuItem>
                <MenuItem value="product">Product</MenuItem>
                <MenuItem value="support">Support</MenuItem>
              </Select>
            </FormControl>
          )}

          {/* Input Area */}
          {inputType === 'text' ? (
            <TextField
              fullWidth
              multiline
              rows={8}
              variant="outlined"
              placeholder="Enter your text content here..."
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              sx={{ mb: 2 }}
            />
          ) : (
            <Box sx={{ mb: 2 }}>
              <input
                accept=".txt,.md,.json,.csv"
                style={{ display: 'none' }}
                id="file-upload"
                type="file"
                onChange={handleFileSelect}
              />
              <label htmlFor="file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<CloudUpload />}
                  fullWidth
                  sx={{ py: 2 }}
                >
                  Select File
                </Button>
              </label>
              {selectedFile && (
                <Box sx={{ mt: 2 }}>
                  <Chip
                    label={selectedFile.name}
                    onDelete={() => setSelectedFile(null)}
                    color="primary"
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Size: {(selectedFile.size / 1024).toFixed(2)} KB
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Upload Button */}
          <Button
            variant="contained"
            fullWidth
            onClick={handleUpload}
            disabled={isUploading || (inputType === 'text' ? !textContent : !selectedFile)}
            startIcon={<CloudUpload />}
            sx={{ mb: 2 }}
          >
            {isUploading ? 'Uploading...' : 'Upload Context'}
          </Button>

          {/* Progress Bar */}
          {isUploading && <LinearProgress sx={{ mb: 2 }} />}

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Success Result */}
          {uploadResult && (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Upload Successful!
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2">
                  Chunks created: {uploadResult.chunks_created}
                </Typography>
                <Typography variant="body2">
                  Total words: {uploadResult.total_words}
                </Typography>
                <Typography variant="body2">
                  Total characters: {uploadResult.total_chars}
                </Typography>
              </Box>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Example Templates */}
      <Paper sx={{ mt: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Example Templates
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setTextContent('My name is [Name]. I work as a [Job Title] at [Company]. My interests include [Interests].')}
          >
            Personal Info
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setTextContent('I prefer concise responses. I am technical and understand programming concepts. Please be direct and skip basic explanations.')}
          >
            Preferences
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setTextContent('Our product is [Product Name]. It helps users [Main Value Prop]. Key features include: [Feature 1], [Feature 2], [Feature 3].')}
          >
            Product Info
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}

export default ContextUpload