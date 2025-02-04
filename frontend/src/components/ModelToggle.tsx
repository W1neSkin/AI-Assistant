import React from 'react';
import styles from './ModelToggle.module.css';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface ModelToggleProps {
    isLocal: boolean;
    onToggle: (isLocal: boolean) => void;
    disabled?: boolean;
    models?: string[];
}

const ModelToggle: React.FC<ModelToggleProps> = ({ 
    isLocal, 
    onToggle,
    disabled,
    models = ['local', 'openai']
}) => {
    const handleToggle = async (newIsLocal: boolean) => {
        const provider = newIsLocal ? 'local' : 'openai';
        try {
            console.log('Sending switch request to:', `${API_BASE_URL}/api/switch-provider`);
            console.log('Request payload:', { provider });
            const response = await axios.post(`${API_BASE_URL}/api/switch-provider`, 
                { provider }, 
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout: 5000,
                }
            );
            console.log('Switch successful:', response.data);
            onToggle(newIsLocal);
        } catch (error) {
            console.error('Switch failed:', error);
            if (axios.isAxiosError(error)) {
                console.error('Error config:', error.config);
                console.error('Error status:', error.response?.status);
                console.error('Response:', error.response?.data);
                if (error.response) {
                    console.error('Response headers:', error.response.headers);
                }
            }
            onToggle(!newIsLocal);  // Revert the toggle
        }
    };

    return (
        <div className={styles.toggleContainer}>
            <label className={styles.switch}>
                <input
                    type="checkbox"
                    checked={isLocal}
                    onChange={(e) => handleToggle(e.target.checked)}
                    disabled={disabled}
                />
                <span className={styles.slider}></span>
            </label>
            <span className={styles.label}>
                {isLocal ? models[0] : models[1]}
            </span>
        </div>
    );
};

export default ModelToggle; 