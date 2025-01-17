import React, { useState, useRef, KeyboardEvent, useEffect } from 'react';
import styles from './Chat.module.css';
import { API_BASE_URL } from '../config';

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
    };
    time_taken: number;
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

const Chat: React.FC<ChatProps> = ({ onManageDocuments }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

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
            const response = await fetch(`${API_BASE_URL}/question/${encodeURIComponent(question)}`);
            const data: ApiResponse = await response.json();

            setMessages(prev => [...prev, {
                type: 'answer',
                text: data.answer || 'No answer available',
                sources: [...new Set(data.context.source_nodes.map(node => node.filename))],
                time_taken: data.time_taken
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                type: 'answer',
                text: 'Sorry, an error occurred while getting the answer.',
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
        </div>
    );
};

export default Chat; 