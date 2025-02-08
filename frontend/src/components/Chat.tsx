import React, { useState, useRef, KeyboardEvent, useEffect, Component } from 'react';
import styles from './Chat.module.css';
import { API_BASE_URL } from '../config';
import { useSearchParams } from 'react-router-dom';
import SettingsDialog from './SettingsDialog';

interface Message {
    type: 'question' | 'answer';
    text: string;
    sources?: string[];
    time_taken?: number;
}

interface ChatProps {
    onManageDocuments: () => void;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    context?: {
        source_nodes: Array<{
            filename: string;
            text: string;
        }>;
        time_taken?: number;
    };
}

interface ApiResponse {
    answer: string;
    context: {
        source_nodes: Array<{
            filename: string;
            text: string;
        }>;
        time_taken: number;
    };
}

interface ModelInfo {
    models: string[];
    current: string;
}

const formatSources = (context: ChatMessage['context']) => {
    if (!context?.source_nodes?.length) return '';
    
    // Get unique filenames
    const uniqueSources = [...new Set(
        context.source_nodes.map(node => node.filename)
    )];
    
    let result = '\n\nSources:\n' + uniqueSources.join('\n');
    
    // Add time taken if available
    if (context.time_taken !== undefined) {
        result += `\n\nTime: ${context.time_taken} seconds`;
    }
    
    return result;
};

// Error boundary component
class ErrorBoundary extends Component<{children: React.ReactNode}, {hasError: boolean}> {
    constructor(props: {children: React.ReactNode}) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(_: Error) {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Chat component error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className={styles.errorContainer}>
                    <h2>Something went wrong.</h2>
                    <button onClick={() => window.location.reload()}>Refresh Page</button>
                </div>
            );
        }

        return this.props.children;
    }
}

const Chat: React.FC<ChatProps> = ({ onManageDocuments }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [settingsOpen, setSettingsOpen] = useState(false);

    useEffect(() => {
        // Test backend connectivity
        const testBackend = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/health`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                console.log("Backend health check:", data);
                return data.status === "healthy";
            } catch (error) {
                console.error("Backend connection error:", {
                    error: error instanceof Error ? error : "Unknown error",
                    API_BASE_URL,
                    message: error instanceof Error ? error.message : String(error),
                    stack: error instanceof Error ? error.stack : undefined
                });
                return false;
            }
        };
        testBackend();
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    const handleClear = () => {
        setMessages([]);
        setInput('');
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleSubmit = async () => {
        if (!input.trim() || loading) return;

        const question = input.trim();
        setInput('');
        setMessages(prev => [...prev, { type: 'question', text: question }]);
        setLoading(true);

        try {
            const encodedQuery = encodeURIComponent(encodeURIComponent(question));
            const response = await fetch(`${API_BASE_URL}/api/question/${encodedQuery}`, {
                headers: {
                }
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get answer');
            }
            const data: ApiResponse = await response.json();

            // Add type checking and default values
            const answer = data?.answer || 'No answer available';
            const sources = data?.context?.source_nodes?.map(node => node.filename) || [];
            const timeTaken = data?.context?.time_taken || 0;

            setMessages(prev => [...prev, {
                type: 'answer',
                text: answer,
                sources: [...new Set(sources)],
                time_taken: timeTaken
            }]);
        } catch (error) {
            console.error('Error in handleSubmit:', error);
            const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
            setMessages(prev => [...prev, {
                type: 'answer',
                text: `Error: ${errorMessage}`,
                sources: []
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.chatContainer}>
            <div className={styles.header}>
                <h1>Document Q&A Bot</h1>
            </div>
            <div className={styles.messagesContainer}>
                {messages.map((msg, index) => (
                    <div key={index} className={`${styles.message} ${styles[msg.type]}`}>
                        <div className={styles.messageText}>{msg.text}</div>
                        {msg.type === 'answer' && msg.sources && msg.sources.length > 0 && (
                            <div className={styles.sources}>
                                Sources: {msg.sources.join('\n')}
                                {msg.time_taken !== undefined && (
                                    <div>Time: {msg.time_taken} seconds</div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className={`${styles.message} ${styles.answer}`}>
                        <div className={styles.loadingIndicator}>Thinking...</div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className={styles.inputContainer}>
                <div className={styles.inputWrapper}>
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your question and press Enter to send (Shift+Enter for new line)"
                        className={styles.input}
                    />
                    <div className={styles.buttonGroup}>
                        <button 
                            onClick={onManageDocuments}
                            className={styles.iconButton}
                            title="Manage Documents"
                        >
                            <span className="material-icons">folder</span>
                        </button>
                        <button 
                            onClick={() => setSettingsOpen(true)}
                            className={styles.iconButton}
                            title="Settings"
                        >
                            <span className="material-icons">settings</span>
                        </button>
                        <button 
                            onClick={handleClear}
                            className={`${styles.iconButton} ${styles.clearButton}`}
                            disabled={messages.length === 0}
                            title="Clear Chat"
                        >
                            <span className="material-icons">delete_sweep</span>
                        </button>
                    </div>
                </div>
            </div>
            <SettingsDialog 
                open={settingsOpen} 
                onClose={() => setSettingsOpen(false)} 
            />
        </div>
    );
};

export default function ChatWithErrorBoundary(props: ChatProps) {
    return (
        <ErrorBoundary>
            <Chat {...props} />
        </ErrorBoundary>
    );
} 