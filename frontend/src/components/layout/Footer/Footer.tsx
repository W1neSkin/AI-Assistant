import React from 'react';
import styles from './Footer.module.css';

const Footer: React.FC = () => {
    return (
        <footer className={styles.footer}>
            <div>
                <span>© {new Date().getFullYear()} AI Assistant. All rights reserved.</span>
            </div>
        </footer>
    );
};

export default Footer; 