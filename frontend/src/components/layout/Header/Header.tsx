import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../common/Button/Button';
import SettingsModal from '../../features/settings/SettingsModal/SettingsModal';
import styles from './Header.module.css';

const Header: React.FC = () => {
    const navigate = useNavigate();
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/login');
    };

    return (
        <>
            <header className={styles.header}>
                <div className={styles.container}>
                    <h1 className={styles.title}>AI Assistant</h1>
                    <div className={styles.buttons}>
                        <Button 
                            onClick={() => setIsSettingsOpen(true)} 
                            variant="secondary"
                            icon="settings"
                        >
                            Settings
                        </Button>
                        <Button onClick={handleLogout} variant="secondary">
                            Logout
                        </Button>
                    </div>
                </div>
            </header>
            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />
        </>
    );
};

export default Header; 