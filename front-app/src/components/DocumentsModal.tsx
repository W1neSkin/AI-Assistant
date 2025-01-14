import React, { useState, useEffect, useRef } from 'react';
import { uploadFile, clearAllData, getDocuments, deleteDocument, updateDocumentStatus } from '../api';
import styles from './DocumentsModal.module.css';
import { ACCEPT_TYPES } from '../constants';

interface Document {
    id: string;
    filename: string;
    active: boolean;
    created_at?: string;
}

interface DocumentsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const DocumentsModal: React.FC<DocumentsModalProps> = ({ isOpen, onClose }) => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            loadDocuments();
        }
    }, [isOpen]);

    const loadDocuments = async () => {
        try {
            const docs = await getDocuments();
            setDocuments(docs);
        } catch (error) {
            setError('Failed to load documents');
            console.error('Load documents error:', error);
        }
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            setSelectedFile(file);
            setError(null);
            
            // Upload immediately after file selection
            setLoading(true);
            try {
                await uploadFile(file);
                await loadDocuments();
                setSelectedFile(null);
                event.target.value = ''; // Reset file input
            } catch (error) {
                setError(error instanceof Error ? error.message : 'Upload failed');
            } finally {
                setLoading(false);
            }
        }
    };

    const handleClearAll = async () => {
        if (window.confirm('Are you sure you want to clear all documents? This action cannot be undone.')) {
            try {
                await clearAllData();
                setDocuments([]);
            } catch (error) {
                setError('Failed to clear documents');
            }
        }
    };

    const handleDeleteDocument = async (docId: string, filename: string) => {
        if (window.confirm(`Are you sure you want to delete "${filename}"?`)) {
            try {
                setLoading(true);
                setError(null);
                await deleteDocument(docId);
                await loadDocuments();  // Refresh the list after deletion
            } catch (error) {
                console.error('Delete error:', error);
                setError(error instanceof Error ? error.message : 'Failed to delete document');
            } finally {
                setLoading(false);
            }
        }
    };

    const handleToggleDocument = async (docId: string, active: boolean) => {
        try {
            await updateDocumentStatus(docId, active);
            setDocuments(docs => 
                docs.map(doc => 
                    doc.id === docId ? { ...doc, active } : doc
                )
            );
        } catch (error) {
            setError('Failed to update document status');
        }
    };

    if (!isOpen) return null;

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modal}>
                <div className={styles.modalHeader}>
                    <h2>Document Management</h2>
                    <button onClick={onClose} className={styles.closeButton}>&times;</button>
                </div>

                <div className={styles.uploadSection}>
                    <input 
                        type="file" 
                        onChange={handleFileChange}
                        accept={ACCEPT_TYPES}
                        style={{ display: 'none' }}
                        ref={fileInputRef}
                    />
                    <button 
                        onClick={() => fileInputRef.current?.click()}
                        className={styles.uploadButton}
                        disabled={loading}
                    >
                        {loading ? 'Uploading...' : 'Upload Document'}
                    </button>
                </div>

                <div className={styles.documentList}>
                    {documents.length === 0 ? (
                        <div className={styles.noDocuments}>
                            No documents uploaded yet
                        </div>
                    ) : (
                        documents.map(doc => (
                            <div key={doc.id} className={styles.documentItem}>
                                <div className={styles.documentInfo}>
                                    <label className={styles.checkbox}>
                                        <input
                                            type="checkbox"
                                            checked={doc.active}
                                            onChange={(e) => handleToggleDocument(doc.id, e.target.checked)}
                                        />
                                        <span className={styles.checkmark}></span>
                                    </label>
                                    <span className={styles.filename}>{doc.filename}</span>
                                </div>
                                <button
                                    onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                                    className={styles.deleteButton}
                                >
                                    Delete
                                </button>
                            </div>
                        ))
                    )}
                </div>

                <div className={styles.modalFooter}>
                    <button 
                        onClick={handleClearAll}
                        className={styles.clearAllButton}
                        disabled={documents.length === 0}
                    >
                        Clear All Documents
                    </button>
                </div>

                {error && <div className={styles.error}>{error}</div>}
            </div>
        </div>
    );
};

export default DocumentsModal; 