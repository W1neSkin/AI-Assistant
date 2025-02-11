export interface Message {
    type: 'question' | 'answer';
    text: string;
    sources?: string[];
    time_taken?: number;
}

export interface ApiResponse {
    answer: string;
    context?: {
        source_nodes?: Array<{
            filename: string;
        }>;
        time_taken?: number;
    };
} 