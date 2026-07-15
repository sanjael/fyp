import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadDocument, listDocuments, deleteDocument } from '../api'
import { useEffect } from 'react'

function Toast({ msg, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 4000); return () => clearTimeout(t) }, [onClose])
  return (
    <div className={`toast ${type}`}>
      <span>{type === 'success' ? '✅' : type === 'error' ? '❌' : '⚠️'}</span>
      <span style={{ flex: 1, fontSize: '0.9rem' }}>{msg}</span>
      <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>✕</button>
    </div>
  )
}

const SOURCE_TYPE_COLORS = {
  research_paper: 'badge-primary',
  arxiv: 'badge-primary',
  textbook: 'badge-info',
  wikipedia: 'badge-success',
  government: 'badge-warning',
  unknown: 'badge-danger',
}

export default function Upload() {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [documents, setDocuments] = useState([])
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [toast, setToast] = useState(null)
  const [deletingFile, setDeletingFile] = useState(null)

  const showToast = (msg, type = 'success') => setToast({ msg, type })

  const fetchDocs = useCallback(() => {
    setLoadingDocs(true)
    listDocuments()
      .then(r => setDocuments(r.data.documents || []))
      .catch(() => setDocuments([]))
      .finally(() => setLoadingDocs(false))
  }, [])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const onDrop = useCallback(async (acceptedFiles) => {
    const pdfFiles = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.pdf'))
    if (!pdfFiles.length) {
      showToast('Only PDF files are supported', 'error')
      return
    }

    for (const file of pdfFiles) {
      setUploading(true)
      setUploadProgress(0)
      const formData = new FormData()
      formData.append('file', file)

      try {
        const res = await uploadDocument(formData, p => setUploadProgress(p))
        const d = res.data
        showToast(`✓ ${d.filename}: ${d.new_chunks_added} chunks indexed in ${d.processing_time_seconds}s`)
        fetchDocs()
      } catch (err) {
        showToast(err?.response?.data?.detail || `Failed to upload ${file.name}`, 'error')
      } finally {
        setUploading(false)
        setUploadProgress(0)
      }
    }
  }, [fetchDocs])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    disabled: uploading,
  })

  const handleDelete = async (filename) => {
    if (!confirm(`Delete "${filename}" from the index?`)) return
    setDeletingFile(filename)
    try {
      await deleteDocument(filename)
      showToast(`Deleted ${filename}`)
      fetchDocs()
    } catch {
      showToast('Delete failed', 'error')
    } finally {
      setDeletingFile(null)
    }
  }

  return (
    <div className="fade-in">
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}

      <div className="page-header">
        <h1 className="page-title">📄 Document Library</h1>
        <p className="page-subtitle">Upload PDF documents to build your RAGShield knowledge base</p>
      </div>

      {/* Upload Zone */}
      <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'drag-over' : ''}`} style={{ marginBottom: '2rem' }}>
        <input {...getInputProps()} />
        {uploading ? (
          <div>
            <span className="upload-icon">⏳</span>
            <p className="upload-title">Processing Document...</p>
            <div style={{ maxWidth: 300, margin: '1rem auto 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span className="text-sm text-muted">Uploading & Indexing</span>
                <span className="text-sm" style={{ color: 'var(--brand-primary)', fontWeight: 700 }}>{uploadProgress}%</span>
              </div>
              <div className="progress-bar-container">
                <div className="progress-bar-fill brand" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          </div>
        ) : isDragActive ? (
          <div>
            <span className="upload-icon">📥</span>
            <p className="upload-title">Drop PDF here!</p>
          </div>
        ) : (
          <div>
            <span className="upload-icon">📤</span>
            <p className="upload-title">Drag & Drop PDF Files</p>
            <p className="upload-sub">or click to browse — supports multiple PDFs</p>
            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              {['Research Papers', 'Textbooks', 'Technical Docs', 'Legal Files', 'Medical Reports'].map(t => (
                <span key={t} className="badge badge-primary">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Indexed Documents ({documents.length})</div>
          <button className="btn btn-secondary btn-sm" onClick={fetchDocs}>↻ Refresh</button>
        </div>

        {loadingDocs ? (
          <div className="loading-overlay" style={{ padding: '2rem' }}>
            <div className="spinner" />
            <span>Loading documents...</span>
          </div>
        ) : documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
            <p style={{ fontSize: '1rem' }}>No documents indexed yet</p>
            <p style={{ fontSize: '0.85rem' }}>Upload a PDF above to get started</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {documents.map((doc, i) => (
              <div key={i} className="chunk-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 10, background: 'rgba(99,102,241,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.3rem', flexShrink: 0
                }}>📄</div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', truncate: true }}>{doc.title || doc.filename}</span>
                    <span className={`badge ${SOURCE_TYPE_COLORS[doc.source_type] || 'badge-primary'}`}>
                      {(doc.source_type || 'unknown').replace('_', ' ')}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                    <span>👤 {doc.author || 'Unknown'}</span>
                    <span>📅 {doc.year || 'Unknown'}</span>
                    <span>🗂️ {doc.chunk_count} chunks</span>
                    <span className="font-mono">{doc.filename}</span>
                  </div>
                </div>

                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(doc.filename)}
                  disabled={deletingFile === doc.filename}
                >
                  {deletingFile === doc.filename ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '🗑️'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="card" style={{ marginTop: '1.5rem', background: 'rgba(6,182,212,0.05)', borderColor: 'rgba(6,182,212,0.2)' }}>
        <div className="card-title" style={{ marginBottom: '0.75rem', color: 'var(--info)' }}>💡 Tips for Best Results</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
          {[
            ['📚', 'Use research papers or textbooks for highest reliability scores'],
            ['📅', 'Recent documents (2020+) get better freshness scores'],
            ['🔍', 'More relevant documents = lower hallucination risk'],
            ['⚠️', 'Avoid uploading contradictory documents from the same topic'],
          ].map(([icon, text], i) => (
            <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              <span>{icon}</span><span>{text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
