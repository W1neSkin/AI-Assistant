import React from 'react';
import styles from './Button.module.css';

interface ButtonProps {
    children: React.ReactNode;
    onClick?: () => void;
    type?: 'button' | 'submit';
    variant?: 'primary' | 'secondary' | 'danger';
    disabled?: boolean;
    icon?: string;
    title?: string;
}

const Button: React.FC<ButtonProps> = ({
    children,
    onClick,
    type = 'button',
    variant = 'primary',
    disabled = false,
    icon,
    title
}) => (
    <button 
        className={`${styles.button} ${styles[variant]}`}
        onClick={onClick}
        type={type}
        disabled={disabled}
        title={title}
    >
        {icon && <span className="material-icons">{icon}</span>}
        {children}
    </button>
);

export default Button; 