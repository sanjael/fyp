import React, { useState } from 'react';
import { UploadCloud, FileText, Trash2, CheckCircle, Clock } from 'lucide-react';

import axios from 'axios';

const Documents = () => {
  const [docs, setDocs] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const fetchDocs = () => {
    axios.get('/api/v1/documents/list')
      .then(res => setDocs(res.data))
      .catch(err => console.error("Error fetching docs", err));
  };

  React.useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 5000); // Poll for updates
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    setIsUploading(true);
    try {
      await axios.post('/api/v1/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchDocs();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Upload failed. Ensure backend is running.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Knowledge Base</h1>
          <p style={{ color: 'var(--text-muted)' }}>Manage your indexed documents and vector embeddings.</p>
        </div>
        <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="application/pdf" style={{ display: 'none' }} />
        <button className="btn-primary" onClick={() => fileInputRef.current?.click()} disabled={isUploading} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UploadCloud size={20} />
          {isUploading ? 'Uploading...' : 'Upload New PDF'}
        </button>
      </div>

      {/* Upload Dropzone (visual only for now) */}
      <div className="glass-panel" onClick={() => fileInputRef.current?.click()} style={{ cursor: 'pointer', padding: '60px', textAlign: 'center', marginBottom: '40px', border: '2px dashed var(--border-color)', background: 'rgba(0,0,0,0.1)' }}>
        <UploadCloud size={48} color="var(--primary)" style={{ marginBottom: '16px' }} />
        <h3 style={{ marginBottom: '8px', fontSize: '1.2rem' }}>Drag & Drop PDF files here</h3>
        <p style={{ color: 'var(--text-muted)' }}>Files will be automatically chunked and indexed into ChromaDB</p>
      </div>

      {/* Documents Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--text-muted)' }}>Document Name</th>
              <th style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--text-muted)' }}>Upload Date</th>
              <th style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--text-muted)' }}>Chunks</th>
              <th style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--text-muted)' }}>Status</th>
              <th style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--text-muted)', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {docs.map(doc => (
              <tr key={doc.id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.2s' }} onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'} onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                    <FileText size={18} color="var(--primary)" />
                  </div>
                  {doc.name}
                </td>
                <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>{doc.date}</td>
                <td style={{ padding: '16px 24px' }}>{doc.chunks > 0 ? doc.chunks : '-'}</td>
                <td style={{ padding: '16px 24px' }}>
                  {doc.status === 'processed' ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--accent-green)', fontSize: '0.85rem', background: 'rgba(0, 230, 118, 0.1)', padding: '4px 10px', borderRadius: '12px' }}>
                      <CheckCircle size={14} /> Indexed
                    </span>
                  ) : (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--accent-yellow)', fontSize: '0.85rem', background: 'rgba(255, 234, 0, 0.1)', padding: '4px 10px', borderRadius: '12px' }}>
                      <Clock size={14} /> Processing...
                    </span>
                  )}
                </td>
                <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                  <button className="btn-outline" style={{ padding: '8px', border: 'none', color: 'var(--text-muted)' }}>
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Documents;
