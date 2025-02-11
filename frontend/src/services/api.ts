const BASE_URL = process.env.REACT_APP_API_URL || (
    process.env.NODE_ENV === 'production' 
        ? 'https://api.yourdomain.com' 
        : 'http://localhost:8000'
);

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

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

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
            ...options.headers,
        };

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
                throw new Error('Session expired');
            }
            throw await response.json();
        }

        return response.json();
    }

    async get<T>(path: string): Promise<T> {
        return this.request<T>(path);
    }

    async post<T>(path: string, data?: any): Promise<T> {
        return this.request<T>(path, {
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined
        });
    }

    async patch(path: string, data?: any) {
        const response = await fetch(`${this.baseUrl}${path}`, {
            method: 'PATCH',
            headers: this.getHeaders(),
            body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }

    async delete(path: string): Promise<void> {
        const response = await fetch(`${this.baseUrl}${path}`, {
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
        
        const response = await fetch(`${this.baseUrl}${path}`, {
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

export const apiClient = new ApiClient(BASE_URL); 