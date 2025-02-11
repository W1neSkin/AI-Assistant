import React from 'react';
import styles from './Logo.module.css';

interface LogoProps {
    size?: number;
    color?: string;
}

const Logo: React.FC<LogoProps> = ({ 
    size = 32, 
    color = '#2c5282' 
}) => (
    <svg 
        width={size} 
        height={size} 
        viewBox="0 0 32 32" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className={styles.logo}
    >
        <path
            d="M16 2C8.268 2 2 8.268 2 16s6.268 14 14 14 14-6.268 14-14S23.732 2 16 2z"
            fill={color}
        />
        <path
            d="M23 12a3 3 0 00-3-3h-8a3 3 0 00-3 3v8a3 3 0 003 3h8a3 3 0 003-3v-8z"
            fill="#fff"
        />
        <path
            d="M16 13a1 1 0 100 2 1 1 0 000-2zm-4 3a1 1 0 100 2 1 1 0 000-2zm8 0a1 1 0 100 2 1 1 0 000-2zm-4 3a1 1 0 100 2 1 1 0 000-2z"
            fill={color}
        />
    </svg>
);

export default Logo; 