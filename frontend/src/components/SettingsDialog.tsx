import React, { useState, useEffect } from 'react';
import { getSettings, saveSettings, UserSettings } from '../services/settingsService';
import styles from './SettingsDialog.module.css';

interface SettingsDialogProps {
    open: boolean;
    onClose: () => void;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
    const [settings, setSettings] = useState<UserSettings>({
        use_openai: false,
        doc_search: true,
        handle_urls: true,
        check_db: true
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (open) {
            loadSettings();
        }
    }, [open]);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const currentSettings = await getSettings();
            setSettings(currentSettings);
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setLoading(true);
            await saveSettings(settings);
            onClose();
            window.alert('Settings saved successfully');
        } catch (error) {
            console.error('Failed to save settings:', error);
            window.alert('Failed to save settings');
        } finally {
            setLoading(false);
        }
    };

    if (!open) return null;

    return (
        <div className={styles.overlay}>
            <div className={styles.dialog}>
                <h2>Settings</h2>
                <div className={styles.settingItem}>
                    <label>
                        <input
                            type="checkbox"
                            checked={settings.use_openai}
                            onChange={(e) => setSettings(s => ({...s, use_openai: e.target.checked}))}
                            disabled={loading}
                        />
                        Use OpenAI Model
                    </label>
                </div>
                <div className={styles.settingItem}>
                    <label>
                        <input
                            type="checkbox"
                            checked={settings.doc_search}
                            onChange={(e) => setSettings(s => ({...s, doc_search: e.target.checked}))}
                            disabled={loading}
                        />
                        Enable Document Search
                    </label>
                </div>
                <div className={styles.settingItem}>
                    <label>
                        <input
                            type="checkbox"
                            checked={settings.handle_urls}
                            onChange={(e) => setSettings(s => ({...s, handle_urls: e.target.checked}))}
                            disabled={loading}
                        />
                        Handle URLs in Questions
                    </label>
                </div>
                <div className={styles.settingItem}>
                    <label>
                        <input
                            type="checkbox"
                            checked={settings.check_db}
                            onChange={(e) => setSettings(s => ({...s, check_db: e.target.checked}))}
                            disabled={loading}
                        />
                        Check Database Needs
                    </label>
                </div>
                <div className={styles.buttons}>
                    <button onClick={onClose} disabled={loading}>Cancel</button>
                    <button onClick={handleSave} disabled={loading}>
                        {loading ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsDialog; 