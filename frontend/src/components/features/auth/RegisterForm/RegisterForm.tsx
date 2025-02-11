import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/auth.module.css';
import Input from '../../../common/Input/Input';
import Button from '../../../common/Button/Button';
import { handleApiError } from '../../../../utils/errorHandler';
import { apiClient } from '../../../../services/api';

const RegisterForm: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        confirmPassword: '',
        error: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            setFormData(prev => ({ ...prev, error: 'Passwords do not match' }));
            return;
        }

        try {
            await apiClient.post('/api/auth/register', {
                username: formData.username,
                password: formData.password,
                confirm_password: formData.confirmPassword
            });
            navigate('/login');
        } catch (err) {
            handleApiError(err);
            setFormData(prev => ({ ...prev, error: 'Registration failed' }));
        }
    };

    return (
        <div className={styles.authContainer}>
            <form className={styles.authForm} onSubmit={handleSubmit}>
                <h2>Register</h2>
                <Input
                    label="Username"
                    value={formData.username}
                    onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                    error={formData.error}
                />
                <Input
                    label="Password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                />
                <Input
                    label="Confirm Password"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                />
                <Button type="submit" variant="primary">
                    Register
                </Button>
                <div className={styles.switchMode}>
                    Already have an account?
                    <a href="/login">Login</a>
                </div>
            </form>
        </div>
    );
};

export default RegisterForm; 