import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface UploadResponse {
    status: 'success' | 'error';
    message: string;
    filename: string;
    error: string | null;
}

export interface QuestionResponse {
    query: string;
    answer: string;
    context: {
        source_nodes: Array<{
            text: string;
            score: number;
            document_id?: string;
        }>;
    };
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
        console.log('Uploading to:', `${API_URL}/upload`);
        const response = await axios.post<UploadResponse>(
            `${API_URL}/upload`, 
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 30000,
                onUploadProgress: (progressEvent) => {
                    console.log('Upload progress:', progressEvent);
                },
            }
        );
        console.log('Upload response:', response);
        return response;
    } catch (error) {
        console.error('Upload error:', error);
        if (axios.isAxiosError(error) && error.response?.data) {
            throw new Error(error.response.data.message || error.response.data.error || 'Upload failed');
        }
        throw error;
    }
};

export const askQuestion = async (question: string) => {
    const response = await axios.get<QuestionResponse>(`${API_URL}/question/${question}`);
    return response.data;
};

export const clearAllData = async () => {
    try {
        const response = await axios.delete<{ status: string; message: string; }>(`${API_URL}/clear-data`);
        return response.data;
    } catch (error) {
        console.error('Clear data error:', error);
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
        console.error('Get documents error:', error);
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
        console.error('Update document status error:', error);
        if (axios.isAxiosError(error) && error.response?.data) {
            throw new Error(error.response.data.detail || 'Failed to update document status');
        }
        throw error;
    }
};