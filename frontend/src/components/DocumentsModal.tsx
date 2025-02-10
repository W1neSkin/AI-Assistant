import React, { useState, useEffect, useRef } from 'react';
import styles from './DocumentsModal.module.css';
import { apiClient } from '../services/api';
import { formatFileSize, formatDate } from '../utils/formatters';
import { Document } from '../types/api';

interface DocumentsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUploadComplete: () => void;
}

const DocumentsModal: React.FC<DocumentsModalProps> = ({ isOpen, onClose, onUploadComplete }) => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const data = await apiClient.get<Document[]>('/api/documents');
            setDocuments(data);
        } catch (error) {
            console.error('Failed to fetch documents:', error);
        }
    };

    const handleUpload = async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            setUploading(true);
            await apiClient.upload('/api/documents/upload', formData);
            await fetchDocuments();
            onUploadComplete();
        } catch (error) {
            console.error('Upload failed:', error);
            setError('Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const handleToggleActive = async (docId: string, currentActive: boolean) => {
        try {
            await apiClient.patch(`/api/documents/${docId}`, { 
                active: !currentActive 
            });
            await fetchDocuments();
        } catch (error) {
            console.error('Failed to toggle document status:', error);
            setError('Failed to update document status');
        }
    };

    const handleDelete = async (docId: string) => {
        if (!window.confirm('Are you sure you want to delete this document?')) {
            return;
        }
        try {
            await apiClient.delete(`/api/documents/${docId}`);
            await fetchDocuments();
        } catch (error) {
            console.error('Failed to delete document:', error);
            setError('Failed to delete document');
        }
    };

    const handleClearAll = async () => {
        if (!window.confirm('Are you sure you want to delete all documents?')) {
            return;
        }
        try {
            await apiClient.delete('/api/documents/clear');
            await fetchDocuments();
        } catch (error) {
            console.error('Failed to clear documents:', error);
            setError('Failed to clear documents');
        }
    };

    // Sort documents by filename
    const sortedAndFilteredDocuments = documents
        .slice() // Create a copy to avoid mutating original array
        .sort((a, b) => a.filename.localeCompare(b.filename))
        .filter(doc => doc.filename.toLowerCase().includes(searchTerm.toLowerCase()));

    const activeCount = documents.filter(d => d.active).length;

    if (!isOpen) return null;

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modalContent}>
                <div className={styles.header}>
                    <div className={styles.documentStats}>
                        {documents.length} documents • {activeCount} active
                    </div>
                    <button className={styles.closeButton} onClick={onClose}>
                        ×
                    </button>
                </div>
                {error && <div className={styles.error}>{error}</div>}

                <div className={styles.searchBox}>
                    <input
                        type="text"
                        className={styles.searchInput}
                        placeholder="Search documents..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <button className={styles.uploadButton} onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                        <span className="material-icons">upload</span>
                    </button>
                    <button 
                        className={styles.clearAllButton} 
                        onClick={handleClearAll}
                        disabled={documents.length === 0}
                    >
                        <span className="material-icons">delete_sweep</span>
                    </button>
                </div>

                {documents.length > 0 ? (
                    <div className={styles.documentList}>
                        {sortedAndFilteredDocuments.map(doc => (
                            <div key={doc.id} className={styles.documentItem}>
                                <div className={styles.documentInfo}>
                                    <label className={styles.checkbox}>
                                        <input
                                            type="checkbox"
                                            checked={doc.active}
                                            onChange={() => handleToggleActive(doc.id, doc.active)}
                                        />
                                        <div className={styles.fileDetails}>
                                            <span className={styles.filename}>{doc.filename}</span>
                                            <div className={styles.fileMetadata}>
                                                {typeof doc.size !== 'undefined' && (
                                                    <span>
                                                        <span className="material-icons">description</span>
                                                        {formatFileSize(doc.size)}
                                                    </span>
                                                )}
                                                {typeof doc.uploadedAt !== 'undefined' && (
                                                    <span>
                                                        <span className="material-icons">schedule</span>
                                                        {formatDate(doc.uploadedAt)}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </label>
                                </div>
                                <button
                                    onClick={() => handleDelete(doc.id)}
                                    className={styles.deleteButton}
                                    title="Delete document"
                                >
                                    <span className="material-icons">delete</span>
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className={styles.noDocuments}>
                        No documents uploaded yet
                    </div>
                )}

                <input
                    ref={fileInputRef}
                    type="file"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                            handleUpload(file);
                        }
                    }}
                    accept="application/pdf"
                    style={{ display: 'none' }}
                />
            </div>
        </div>
    );
};

export default DocumentsModal; 