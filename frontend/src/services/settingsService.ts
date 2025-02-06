import axios from 'axios';
import { API_BASE_URL } from '../config';

export interface UserSettings {
  use_openai: boolean;
  doc_search: boolean;
  handle_urls: boolean;
  check_db: boolean;
}

const DEFAULT_SETTINGS: UserSettings = {
  use_openai: false,
  doc_search: true,
  handle_urls: true,
  check_db: true
};

export const getSettings = async (): Promise<UserSettings> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/settings`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch settings:', error);
    return DEFAULT_SETTINGS;
  }
};

export const saveSettings = async (settings: UserSettings): Promise<void> => {
  try {
    await axios.post(`${API_BASE_URL}/api/settings`, settings);
  } catch (error) {
    console.error('Failed to save settings:', error);
    throw error;
  }
}; 