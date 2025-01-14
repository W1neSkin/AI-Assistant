import React, { useState, useRef } from 'react';
import { API_BASE_URL } from '../config';
import { ALLOWED_EXTENSIONS, ACCEPT_TYPES, MAX_FILE_SIZE } from '../constants';

interface FileUploadProps {
    onUpload?: (file: File) => void;
}

const FileUpload: React.FC<FileUploadProps> = () => {
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [status, setStatus] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const validateFile = (file: File): string | null => {
        const extension = file.name.split('.').pop()?.toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(extension || '')) {
            return `File type not supported. Please upload ${ALLOWED_EXTENSIONS.join(', ')} files only.`;
        }
        if (file.size > MAX_FILE_SIZE) {
            return 'File size too large. Maximum size is 10MB.';
        }
        return null;
    };

    const handleFileUpload = async (file: File) => {
        const validationError = validateFile(file);
        if (validationError) {
            setError(validationError);
            setStatus(null);
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            setStatus('Uploading...');
            setError(null);

            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Upload failed');
            }

            setStatus('Upload successful!');
            setTimeout(() => setStatus(null), 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
            setStatus(null);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    };

    return (
        <div className="upload-container">
            <div 
                className={`dropzone ${isDragging ? 'dragging' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                    accept={ACCEPT_TYPES}
                    style={{ display: 'none' }}
                />
                <p>Drag and drop a file here, or click to select</p>
                <p className="supported-formats">Supported formats: {ALLOWED_EXTENSIONS.join(', ')}</p>
            </div>
            {status && <p className="status">{status}</p>}
            {error && <p className="error">{error}</p>}
        </div>
    );
};

export default FileUpload; 