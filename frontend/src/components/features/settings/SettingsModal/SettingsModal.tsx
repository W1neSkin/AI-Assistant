import React, { useState, useEffect } from 'react';
import styles from './SettingsModal.module.css';
import Modal from '../../../common/Modal/Modal';
import Button from '../../../common/Button/Button';
import { handleApiError } from '../../../../utils/errorHandler';
import { apiClient } from '../../../../services/api';

interface ApiError {
    detail: string;
}

interface UserSettings {
    use_cloud: boolean;
    enable_document_search: boolean;
    handle_urls: boolean;
    check_db: boolean;
}

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
    const [settings, setSettings] = useState<UserSettings>({
        use_cloud: false,
        enable_document_search: true,
        handle_urls: true,
        check_db: true
    });

    useEffect(() => {
        if (isOpen) {
            const fetchSettings = async () => {
                try {
                    console.log('Fetching settings...');
                    const response = await apiClient.get<UserSettings>('/api/settings');
                    console.log('Received settings:', response);
                    setSettings(response);
                } catch (error) {
                    console.error('Error fetching settings:', error);
                    handleApiError(error);
                }
            };

            fetchSettings();
        }
    }, [isOpen]);

    const handleSave = async () => {
        try {
            console.log('Saving settings:', settings);
            await apiClient.post('/api/settings', settings);
            console.log('Settings saved successfully');
            onClose();
        } catch (error) {
            console.error('Error saving settings:', error);
            handleApiError(error);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Settings"
        >
            <div className={styles.settingsForm}>
                <div className={styles.settingGroup}>
                    <label className={styles.settingItem}>
                        <div className={styles.settingLabel}>
                            <span>Use Cloud Model</span>
                            <span className={styles.settingDescription}>
                                Use Cloud's model for responses
                            </span>
                        </div>
                        <input
                            type="checkbox"
                            checked={settings.use_cloud}
                            onChange={() => setSettings(prev => ({
                                ...prev,
                                use_cloud: !prev.use_cloud
                            }))}
                        />
                    </label>

                    <label className={styles.settingItem}>
                        <div className={styles.settingLabel}>
                            <span>Enable Document Search</span>
                            <span className={styles.settingDescription}>
                                Search through uploaded documents for answers
                            </span>
                        </div>
                        <input
                            type="checkbox"
                            checked={settings.enable_document_search}
                            onChange={() => setSettings(prev => ({
                                ...prev,
                                enable_document_search: !prev.enable_document_search
                            }))}
                        />
                    </label>

                    <label className={styles.settingItem}>
                        <div className={styles.settingLabel}>
                            <span>Handle URLs in Questions</span>
                            <span className={styles.settingDescription}>
                                Process URLs mentioned in questions
                            </span>
                        </div>
                        <input
                            type="checkbox"
                            checked={settings.handle_urls}
                            onChange={() => setSettings(prev => ({
                                ...prev,
                                handle_urls: !prev.handle_urls
                            }))}
                        />
                    </label>

                    <label className={styles.settingItem}>
                        <div className={styles.settingLabel}>
                            <span>Check Database</span>
                            <span className={styles.settingDescription}>
                                Include database information in responses
                            </span>
                        </div>
                        <input
                            type="checkbox"
                            checked={settings.check_db}
                            onChange={() => setSettings(prev => ({
                                ...prev,
                                check_db: !prev.check_db
                            }))}
                        />
                    </label>
                </div>

                <div className={styles.actions}>
                    <Button onClick={onClose} variant="secondary">Cancel</Button>
                    <Button onClick={handleSave} variant="primary">
                        Save
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default SettingsModal; 