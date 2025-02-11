import React from 'react';
import styles from './DocumentItem.module.css';
import Button from '../../../common/Button/Button';
import { Document } from '../../../../types/documents';
import { formatFileSize, formatDate } from '../../../../utils/formatters';

interface DocumentItemProps {
    document: Document;
    onToggleActive: (id: string, active: boolean) => void;
    onDelete: (id: string) => void;
}

const DocumentItem: React.FC<DocumentItemProps> = ({
    document,
    onToggleActive,
    onDelete
}) => (
    <div className={styles.documentItem}>
        <div className={styles.documentInfo}>
            <label className={styles.checkbox}>
                <input
                    type="checkbox"
                    checked={document.active}
                    onChange={() => onToggleActive(document.id, document.active)}
                />
                <div className={styles.fileDetails}>
                    <span className={styles.filename}>{document.filename}</span>
                    <div className={styles.fileMetadata}>
                        {document.size && (
                            <span>
                                <span className="material-icons">description</span>
                                {formatFileSize(document.size)}
                            </span>
                        )}
                        {document.uploadedAt && (
                            <span>
                                <span className="material-icons">schedule</span>
                                {formatDate(document.uploadedAt)}
                            </span>
                        )}
                    </div>
                </div>
            </label>
        </div>
        <Button
            onClick={() => onDelete(document.id)}
            variant="danger"
            icon="delete"
            title="Delete document"
            children=""
        />
    </div>
);

export default DocumentItem; 