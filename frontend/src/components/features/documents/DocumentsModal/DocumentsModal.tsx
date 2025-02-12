import React, { useState, useEffect, useRef } from 'react';
import styles from './DocumentsModal.module.css';
import Modal from '../../../common/Modal/Modal';
import Button from '../../../common/Button/Button';
import Input from '../../../common/Input/Input';
import DocumentItem from '../DocumentItem/DocumentItem';
import { Document } from '../../../../types/documents';
import { handleApiError } from '../../../../utils/errorHandler';
import { apiClient } from '../../../../services/api';

interface DocumentsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUploadComplete: () => void;
}

const DocumentsModal: React.FC<DocumentsModalProps> = ({ isOpen, onClose, onUploadComplete }) => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [uploading, setUploading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            fetchDocuments();
        }
    }, [isOpen]);

    const fetchDocuments = async () => {
        try {
            const data = await apiClient.getDocuments();
            if (Array.isArray(data)) {
                setDocuments(data);
            } else {
                console.error('Invalid response format:', data);
                setDocuments([]);
            }
        } catch (err) {
            handleApiError(err);
            setDocuments([]);
        }
    };

    const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            setUploading(true);
            await apiClient.uploadDocument(file);
            await fetchDocuments();
            onUploadComplete();
        } catch (err) {
            handleApiError(err);
        } finally {
            setUploading(false);
        }
    };

    const handleToggleActive = async (docId: string, currentActive: boolean) => {
        try {
            await apiClient.patch(`/api/documents/${docId}`, { active: !currentActive });
            await fetchDocuments();
        } catch (err) {
            handleApiError(err);
        }
    };

    const handleDelete = async (docId: string) => {
        if (!window.confirm('Are you sure you want to delete this document?')) return;
        
        try {
            await apiClient.delete(`/api/documents/${docId}`);
            await fetchDocuments();
        } catch (err) {
            handleApiError(err);
        }
    };

    const filteredDocuments = documents.filter(doc => 
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <Modal 
            isOpen={isOpen} 
            onClose={onClose}
            title="Manage Documents"
        >
            <div className={styles.searchBox}>
                <Input
                    value={searchTerm}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                    placeholder="Search documents..."
                    icon="search"
                />
            </div>

            <div className={styles.toolbar}>
                <Button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    icon="upload"
                >
                    Upload
                </Button>
            </div>

            <div className={styles.documentList}>
                {filteredDocuments.map(doc => (
                    <DocumentItem
                        key={doc.id}
                        document={doc}
                        onToggleActive={handleToggleActive}
                        onDelete={handleDelete}
                    />
                ))}
            </div>

            <input
                ref={fileInputRef}
                type="file"
                onChange={handleUpload}
                accept=".pdf,.txt,.doc,.docx"
                style={{ display: 'none' }}
            />
        </Modal>
    );
};

export default DocumentsModal; 