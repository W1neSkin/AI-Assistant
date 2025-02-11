import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/auth.module.css';
import Input from '../../../common/Input/Input';
import Button from '../../../common/Button/Button';
import { handleApiError } from '../../../../utils/errorHandler';
import { apiClient } from '../../../../services/api';

interface LoginFormProps {
    onSuccess?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [rememberMe, setRememberMe] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await apiClient.post<{access_token: string}>('/api/auth/login', {
                username,
                password,
                remember_me: rememberMe
            });
            localStorage.setItem('access_token', response.access_token);
            onSuccess?.() || navigate('/');
        } catch (err) {
            handleApiError(err);
            setError('Invalid username or password');
        }
    };

    return (
        <div className={styles.authContainer}>
            <form className={styles.authForm} onSubmit={handleSubmit}>
                <h2>Login</h2>
                <Input
                    label="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    error={error}
                />
                <Input
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                <label className={styles.checkbox}>
                    <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                    />
                    Remember me
                </label>
                <Button type="submit" variant="primary">
                    Login
                </Button>
                <div className={styles.switchMode}>
                    Don't have an account?
                    <a href="/register">Register</a>
                </div>
            </form>
        </div>
    );
};

export default LoginForm; 