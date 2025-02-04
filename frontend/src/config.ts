declare global {
    namespace NodeJS {
        interface ProcessEnv {
            REACT_APP_API_URL?: string;
        }
    }
}

export const API_BASE_URL = process.env.REACT_APP_API_URL || 
    'http://localhost:8000';

export const ALLOWED_EXTENSIONS = ['txt', 'pdf', 'html', 'docx'];
export const ACCEPT_TYPES = '.txt,.pdf,.html,.htm,.docx';
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB 