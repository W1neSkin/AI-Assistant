import React, { useState, useEffect, useRef } from 'react';
import styles from './DocumentsModal.module.css';
import { API_BASE_URL, ACCEPT_TYPES } from '../config';
import { formatFileSize, formatDate } from '../utils/formatters';

interface Document {
    id: string;
    filename: string;
    active: boolean;
    size?: number;  // in bytes
    uploadedAt?: string;
}

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
            const response = await fetch(`${API_BASE_URL}/documents`);
            if (!response.ok) throw new Error('Failed to fetch documents');
            const data = await response.json();
            setDocuments(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch documents');
        }
    };

    const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        setUploading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Upload failed');
            }

            await fetchDocuments();
            onUploadComplete();
            event.target.value = ''; // Reset file input
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const handleToggleActive = async (docId: string, currentActive: boolean) => {
        try {
            // Update local state immediately for better UX
            setDocuments(docs => docs.map(doc => 
                doc.id === docId ? { ...doc, active: !currentActive } : doc
            ));

            const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ active: !currentActive }),
            });

            if (!response.ok) {
                // Revert local state if server request fails
                setDocuments(docs => docs.map(doc => 
                    doc.id === docId ? { ...doc, active: currentActive } : doc
                ));
                throw new Error('Failed to update document status');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update document status');
        }
    };

    const handleDelete = async (docId: string) => {
        if (!window.confirm('Are you sure you want to delete this document?')) {
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
                method: 'DELETE',
            });

            if (!response.ok) throw new Error('Failed to delete document');
            await fetchDocuments();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete document');
        }
    };

    // Sort documents by filename
    const sortedAndFilteredDocuments = documents
        .slice() // Create a copy to avoid mutating original array
        .sort((a, b) => a.filename.localeCompare(b.filename))
        .filter(doc => doc.filename.toLowerCase().includes(searchTerm.toLowerCase()));

    if (!isOpen) return null;

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modal}>
                <div className={styles.modalHeader}>
                    <h2>Manage Documents</h2>
                    <button onClick={onClose} className={styles.closeButton}>&times;</button>
                </div>
                <div className={styles.modalContent}>
                    <div className={styles.documentStats}>
                        <span>{documents.length} document{documents.length !== 1 ? 's' : ''}</span>
                        <span>{documents.filter(d => d.active).length} active</span>
                    </div>
                    <div className={styles.searchBox}>
                        <span className="material-icons">search</span>
                        <input
                            type="text"
                            placeholder="Search documents..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className={styles.uploadSection}>
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                            className={`${styles.uploadButton} ${uploading ? styles.loading : ''}`}
                        >
                            <span className="material-icons">upload_file</span>
                            {uploading ? 'Uploading...' : 'Upload Document'}
                        </button>
                        <input
                            ref={fileInputRef}
                            type="file"
                            onChange={handleUpload}
                            accept={ACCEPT_TYPES}
                            style={{ display: 'none' }}
                        />
                    </div>
                    {error && <div className={styles.error}>{error}</div>}
                    <div className={styles.documentList}>
                        {sortedAndFilteredDocuments.length === 0 ? (
                            <div className={styles.noDocuments}>
                                {searchTerm ? 'No matching documents found' : 'No documents uploaded yet'}
                            </div>
                        ) : (
                            sortedAndFilteredDocuments.map(doc => (
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
                                                    {doc.size && (
                                                        <span>
                                                            <span className="material-icons">description</span>
                                                            {formatFileSize(doc.size)}
                                                        </span>
                                                    )}
                                                    {doc.uploadedAt && (
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
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DocumentsModal; 