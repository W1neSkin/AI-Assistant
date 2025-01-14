import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface UploadResponse {
    status: 'success' | 'error';
    message: string;
    filename: string;
    error: string | null;
}

export interface Document {
    id: string;
    filename: string;
    active: boolean;
}

export const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await axios.post<UploadResponse>(
            `${API_URL}/upload`, 
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw new Error(error.response.data.message || error.response.data.error || 'Upload failed');
        }
        throw error;
    }
};

export const clearAllData = async () => {
    try {
        const response = await axios.delete<{ status: string; message: string; }>(`${API_URL}/clear-data`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw new Error(error.response.data.detail || error.response.data.message || 'Failed to clear data');
        }
        throw error;
    }
};

export const getDocuments = async (): Promise<Document[]> => {
    try {
        const response = await axios.get<Document[]>(`${API_URL}/documents`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw new Error(error.response.data.detail || 'Failed to get documents');
        }
        throw error;
    }
};

export const deleteDocument = async (docId: string): Promise<void> => {
    const response = await fetch(`${API_URL}/documents/${docId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete document');
    }
};

export const updateDocumentStatus = async (docId: string, active: boolean): Promise<void> => {
    try {
        await axios.patch(`${API_URL}/documents/${docId}`, { active });
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw new Error(error.response.data.detail || 'Failed to update document status');
        }
        throw error;
    }
};