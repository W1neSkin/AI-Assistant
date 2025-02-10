import { API_BASE_URL } from '../config';

export class ApiClient {
    private getHeaders(): HeadersInit {
        const token = localStorage.getItem('access_token');
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };
        if (token) {
            headers['Authorization'] = token.startsWith('Bearer ') ? token : `Bearer ${token}`;
        }
        return headers;
    }

    async get<T>(path: string): Promise<T> {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            headers: this.getHeaders(),
        });
        if (!response.ok) {
            throw new Error('API request failed');
        }
        return response.json();
    }

    async post<T>(path: string, data?: any): Promise<T> {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }
        return response.json();
    }

    async patch(path: string, data?: any) {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            method: 'PATCH',
            headers: this.getHeaders(),
            body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }

    async delete(path: string): Promise<void> {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            method: 'DELETE',
            headers: this.getHeaders(),
        });
        if (!response.ok) {
            throw new Error('API request failed');
        }
    }

    async upload(path: string, formData: FormData): Promise<void> {
        const token = localStorage.getItem('access_token');
        const headers: Record<string, string> = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${path}`, {
            method: 'POST',
            headers,
            body: formData,
        });
        if (!response.ok) {
            throw new Error('Upload failed');
        }
    }

    // Add other methods as needed (PUT, DELETE, etc.)
}

export const apiClient = new ApiClient(); 