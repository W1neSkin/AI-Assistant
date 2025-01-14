import React, { useState, useRef, KeyboardEvent, useEffect } from 'react';
import styles from './Chat.module.css';
import { API_BASE_URL } from '../config';

interface Message {
    type: 'question' | 'answer';
    text: string;
    sources?: string[];
}

const Chat: React.FC = () => {
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
            const data = await response.json();

            setMessages(prev => [...prev, {
                type: 'answer',
                text: data.answer || 'No answer available',
                sources: data.context?.source_nodes?.map((node: any) => node.filename) || []
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
            <div className={styles.messagesContainer}>
                {messages.map((msg, index) => (
                    <div key={index} className={`${styles.message} ${styles[msg.type]}`}>
                        <div className={styles.messageText}>{msg.text}</div>
                        {msg.type === 'answer' && msg.sources && msg.sources.length > 0 && (
                            <div className={styles.sources}>
                                Sources: {msg.sources.join(', ')}
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
                    <button 
                        onClick={handleClear}
                        className={styles.clearButton}
                        disabled={messages.length === 0}
                    >
                        Clear Chat
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Chat; 