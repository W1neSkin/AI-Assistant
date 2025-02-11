import React from 'react';
import styles from './Input.module.css';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    label?: string;
    error?: string;
    icon?: string;
    className?: string;
}

const Input: React.FC<InputProps> = ({ 
    label, 
    error, 
    className = '', 
    ...props 
}) => (
    <div className={styles.inputGroup}>
        {label && <label className={styles.label}>{label}</label>}
        <input 
            className={`${styles.input} ${error ? styles.error : ''} ${className}`}
            {...props}
        />
        {error && <span className={styles.errorMessage}>{error}</span>}
    </div>
);

export default Input; 