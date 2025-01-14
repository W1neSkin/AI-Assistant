import React from 'react';
import styles from './Header.module.css';

interface HeaderProps {
    onManageDocuments: () => void;
}

const Header: React.FC<HeaderProps> = ({ onManageDocuments }) => {
    return (
        <header className={styles.header}>
            <h1>Document Q&A</h1>
            <button 
                onClick={onManageDocuments}
                className={styles.documentsButton}
            >
                Manage Documents
            </button>
        </header>
    );
};

export default Header;