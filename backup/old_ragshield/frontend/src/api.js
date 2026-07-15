// API client for RAGShield backend
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export const uploadDocument = (formData, onProgress) =>
  api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => onProgress && onProgress(Math.round((e.loaded * 100) / e.total)),
  })

export const queryRAGShield = (payload) => api.post('/query', payload)

export const listDocuments = () => api.get('/documents')

export const deleteDocument = (filename) => api.delete(`/documents/${encodeURIComponent(filename)}`)

export const getStats = () => api.get('/stats')

export const getHealth = () => api.get('/health')

export const runPoisonTest = (payload) => api.post('/poison-test', payload)

export default api
