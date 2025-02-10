import { API_BASE_URL } from '../config';

interface LoginData {
    username: string;
    password: string;
    remember_me: boolean;
}

interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export const login = async (data: LoginData): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    const authData = await response.json();
    localStorage.setItem('access_token', authData.access_token);
    localStorage.setItem('refresh_token', authData.refresh_token);
    return authData;
};

export const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
};

export const isAuthenticated = (): boolean => {
    return !!localStorage.getItem('access_token');
};

export const getAuthHeader = (): HeadersInit => {
    const token = localStorage.getItem('access_token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
}; 