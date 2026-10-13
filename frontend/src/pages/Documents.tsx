import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, type DocumentItem } from '../api/client';
import { 
  FileText, 
  Upload, 
  Trash2, 
  Plus,
  X
} from 'lucide-react';

export const Documents: React.FC = () => {
  const { user } = useAuth();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Upload modal state
  const [showModal, setShowModal] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [docTitle, setDocTitle] = useState<string>('');
  const [accessLevel, setAccessLevel] = useState<string>('internal');
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await api.getDocuments();
      setDocs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch knowledge documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError('Please select a PDF, DOCX, or TXT file to upload.');
      return;
    }

    // Client-side pre-validation
    const ext = uploadFile.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(ext || '')) {
      setUploadError('Invalid file type. Only PDF, DOCX, and TXT files are supported.');
      return;
    }

    if (uploadFile.size > 10 * 1024 * 1024) {
      setUploadError('File size exceeds the 10 MB limit.');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      await api.uploadDocument(uploadFile, docTitle || uploadFile.name, accessLevel);
      setShowModal(false);
      setUploadFile(null);
      setDocTitle('');
      loadDocuments();
    } catch (err: any) {
      setUploadError(err.message || 'Document processing and embedding failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!window.confirm('Are you sure you want to delete this document from the knowledge mesh?')) return;
    try {
      await api.deleteDocument(docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      alert(`Deletion failed: ${err.message}`);
    }
  };

  const canDelete = user?.role === 'admin' || user?.role === 'department_manager';

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1>Knowledge Documents & Semantic Index</h1>
          <p className="subtitle">
            RAG Ingestion • Automatic Chunking & Neural Embeddings with all-MiniLM-L6-v2
          </p>
        </div>

        <button 
          onClick={() => setShowModal(true)} 
          className="btn btn-primary"
          style={{ gap: '8px' }}
        >
          <Plus size={16} />
          <span>Upload Document</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: '8px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          Loading authorized knowledge documents...
        </div>
      ) : docs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          <FileText size={40} color="#94a3b8" style={{ margin: '0 auto 12px auto' }} />
          <div style={{ fontWeight: 600, fontSize: '1rem', color: '#1e293b' }}>No documents uploaded yet</div>
          <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>
            Upload corporate policies, manuals, or pricing matrices to index them in the semantic vector database.
          </div>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title & Filename</th>
                <th>Format</th>
                <th>Access Level</th>
                <th>Index Status</th>
                <th>Date Added</th>
                {canDelete && <th style={{ textAlign: 'right' }}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id}>
                  <td>#{doc.id}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{doc.title}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{doc.filename}</div>
                  </td>
                  <td>
                    <span className="badge badge-neutral">{doc.file_type.toUpperCase()}</span>
                  </td>
                  <td>
                    <span className={`badge ${doc.access_level === 'confidential' ? 'badge-danger' : 'badge-primary'}`}>
                      {doc.access_level}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${doc.status === 'indexed' ? 'badge-success' : (doc.status === 'error' ? 'badge-danger' : 'badge-warning')}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                  {canDelete && (
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        onClick={() => handleDelete(doc.id)} 
                        className="btn btn-secondary btn-sm"
                        style={{ color: '#ef4444', borderColor: '#fecaca', padding: '6px' }}
                        title="Delete Document"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '1.1rem' }}>
                <Upload size={20} color="#2563eb" />
                <span>Upload & Index Document</span>
              </div>
              <button 
                onClick={() => setShowModal(false)} 
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleUpload}>
              <div className="modal-body">
                {uploadError && (
                  <div style={{ padding: '10px 14px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: '6px', fontSize: '0.85rem', marginBottom: '16px' }}>
                    {uploadError}
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="fileUpload">Select Document (.pdf, .docx, .txt)</label>
                  <input
                    id="fileUpload"
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    required
                  />
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Maximum file size: 10 MB</span>
                </div>

                <div className="form-group">
                  <label htmlFor="docTitle">Document Title (Optional)</label>
                  <input
                    id="docTitle"
                    type="text"
                    value={docTitle}
                    onChange={(e) => setDocTitle(e.target.value)}
                    placeholder="e.g. Q4 Global Discounting Matrix"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="accessLevel">Security Classification Level</label>
                  <select
                    id="accessLevel"
                    value={accessLevel}
                    onChange={(e) => setAccessLevel(e.target.value)}
                  >
                    <option value="internal">Internal (All department members)</option>
                    <option value="public">Public (Cross-department accessible)</option>
                    {(user?.role === 'admin' || user?.role === 'department_manager') && (
                      <option value="confidential">Confidential (Managers and Admin only)</option>
                    )}
                  </select>
                </div>
              </div>

              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowModal(false)}
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={uploading || !uploadFile}
                >
                  {uploading ? 'Processing & Generating Embeddings...' : 'Upload & Ingest'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
