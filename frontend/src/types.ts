export interface UserSettings {
    use_openai: boolean;
    enable_document_search: boolean;
    handle_urls: boolean;
    check_db: boolean;
}

export interface Document {
    id: string;
    filename: string;
    active: boolean;
    size?: number;
    uploadedAt?: string;
} 