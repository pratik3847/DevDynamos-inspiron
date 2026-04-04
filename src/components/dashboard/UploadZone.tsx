import React, { useCallback, useState } from 'react';
import { UploadCloud, FileType, CheckCircle } from 'lucide-react';

interface UploadZoneProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export default function UploadZone({ onUpload, isUploading }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    setSelectedFile(file);
    // Auto upload for demo
    onUpload(file);
  };

  return (
    <div 
      className="dash-card" 
      style={{ 
        border: `2px dashed ${dragActive ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.1)'}`,
        background: dragActive ? 'rgba(0,214,255,0.05)' : 'rgba(0,0,0,0.2)',
        transition: 'all 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        textAlign: 'center',
        position: 'relative'
      }}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input 
        type="file" 
        accept=".txt,.edi,.x12" 
        onChange={handleChange}
        style={{ position: 'absolute', width: '100%', height: '100%', top: 0, left: 0, opacity: 0, cursor: 'pointer' }}
        disabled={isUploading}
      />
      
      {isUploading ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.1)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
          <div style={{ color: '#fff', fontWeight: 500 }}>Processing EDI File...</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Running Parser & Validator agents</div>
        </div>
      ) : selectedFile ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <CheckCircle size={48} color="var(--accent-cyan)" />
          <div>
            <div style={{ color: '#fff', fontWeight: 600, fontSize: '1.125rem' }}>{selectedFile.name}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{(selectedFile.size / 1024).toFixed(2)} KB</div>
          </div>
        </div>
      ) : (
        <>
          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '50%', marginBottom: '24px' }}>
            <UploadCloud size={48} color="var(--text-secondary)" />
          </div>
          <h3 style={{ color: '#fff', fontSize: '1.25rem', marginBottom: '8px' }}>Select an EDI file or drag and drop</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>Supported formats: 837P, 837I, 835, 834 (.txt, .edi, .x12)</p>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span className="btn" style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', pointerEvents: 'none' }}>
              <FileType size={18} /> Browse Files
            </span>
          </div>
        </>
      )}
    </div>
  );
}
