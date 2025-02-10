import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Header.module.css';

const Header: React.FC = () => {
    const navigate = useNavigate();
    const isAuthenticated = !!localStorage.getItem('access_token');

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/login');
    };

    return (
        <header className={styles.header}>
            <div className={styles.logo}>
                Document Q&A Bot
            </div>
            <nav className={styles.nav}>
                {isAuthenticated ? (
                    <button onClick={handleLogout} className={styles.logoutButton}>
                        Logout
                    </button>
                ) : (
                    <div className={styles.authButtons}>
                        <button onClick={() => navigate('/login')}>Login</button>
                        <button onClick={() => navigate('/register')}>Register</button>
                    </div>
                )}
            </nav>
        </header>
    );
};

export default Header;