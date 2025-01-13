// front-app/src/components/FileUpload.tsx
import React, { useState } from 'react';
import { uploadFile, clearAllData } from '../api';
import styles from './FileUpload.module.css';

// Define the response type
interface UploadResponse {
    status: 'success' | 'error';
    message: string;
    filename: string;
    error: string | null;
}

const FileUpload: React.FC = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [clearing, setClearing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setSelectedFile(event.target.files[0]);
            setError(null); // Clear any previous errors
        }
    };

    const handleUpload = async () => {
        if (selectedFile) {
            setLoading(true);
            setError(null);
            try {
                const response = await uploadFile(selectedFile);
                const data = response.data as UploadResponse;
                
                if (data.status === 'success') {
                    alert('File uploaded successfully!');
                    setSelectedFile(null); // Reset file selection
                    // Reset the file input
                    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
                    if (fileInput) fileInput.value = '';
                } else {
                    throw new Error(data.message || 'Upload failed');
                }
            } catch (error) {
                console.error('Error uploading file:', error);
                setError(error instanceof Error ? error.message : 'File upload failed');
                alert(error instanceof Error ? error.message : 'File upload failed');
            } finally {
                setLoading(false);
            }
        }
    };

    const handleClearData = async () => {
        if (window.confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
            setClearing(true);
            setError(null);
            try {
                await clearAllData();
                alert('All data cleared successfully');
            } catch (error) {
                console.error('Error clearing data:', error);
                setError(error instanceof Error ? error.message : 'Failed to clear data');
                alert('Failed to clear data');
            } finally {
                setClearing(false);
            }
        }
    };

    return (
        <div className={styles.fileUpload}>
            <div className={styles.uploadSection}>
                <input 
                    type="file" 
                    onChange={handleFileChange}
                    accept=".txt,.pdf,.doc,.docx"
                />
                <button 
                    onClick={handleUpload} 
                    disabled={loading || !selectedFile}
                >
                    {loading ? 'Uploading...' : 'Upload'}
                </button>
            </div>
            <div className={styles.clearSection}>
                <button 
                    onClick={handleClearData}
                    disabled={clearing}
                    className={styles.clearButton}
                >
                    {clearing ? 'Clearing...' : 'Clear All Data'}
                </button>
            </div>
            {error && <div className={styles.error}>{error}</div>}
        </div>
    );
};

export default FileUpload;