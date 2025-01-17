import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { API_BASE_URL } from '../config';

interface Document {
    id: string;
    filename: string;
    active: boolean;
}

const DocumentManager: React.FC = () => {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchDocuments = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/documents`);
            if (response.ok) {
                const data = await response.json();
                setDocuments(data);
            } else {
                const error = await response.json();
                toast.error(error.detail || 'Failed to fetch documents');
            }
        } catch (error) {
            console.error('Error fetching documents:', error);
            toast.error('Failed to fetch documents');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAll = async () => {
        if (window.confirm('Are you sure you want to delete all documents? This action cannot be undone.')) {
            try {
                const response = await fetch(`${API_BASE_URL}/documents/all`, {
                    method: 'DELETE',
                });
                
                if (response.ok) {
                    await fetchDocuments();
                    toast.success('All documents deleted successfully');
                } else {
                    const error = await response.json();
                    toast.error(error.detail || 'Failed to delete documents');
                }
            } catch (error) {
                console.error('Error deleting documents:', error);
                toast.error('Failed to delete documents');
            }
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Manage Documents</h2>
                <button
                    onClick={handleDeleteAll}
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
                    disabled={loading}
                >
                    Delete All Documents
                </button>
            </div>
            
            {loading ? (
                <div>Loading...</div>
            ) : documents.length === 0 ? (
                <div>No documents found</div>
            ) : (
                <div className="grid gap-4">
                    {documents.map((doc) => (
                        <div key={doc.id} className="border p-4 rounded">
                            <span>{doc.filename}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default DocumentManager; 