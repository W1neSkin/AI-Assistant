import { apiClient } from './api';
import { UserSettings } from '../types';

export const getSettings = async (): Promise<UserSettings> => {
    return apiClient.get('/api/settings');
};

export const saveSettings = async (settings: UserSettings): Promise<void> => {
    await apiClient.post('/api/settings', settings);
}; 