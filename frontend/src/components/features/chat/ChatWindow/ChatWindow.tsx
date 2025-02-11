import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import styles from './ChatWindow.module.css';
import { Message, ApiResponse } from '../../../../types/chat';
import MessageList from '../MessageList/MessageList';
import Button from '../../../common/Button/Button';
import { handleApiError } from '../../../../utils/errorHandler';
import { apiClient } from '../../../../services/api';

interface ChatWindowProps {
    onManageDocuments: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ onManageDocuments }) => {
    const [searchParams] = useSearchParams();
    const [messages, setMessages] = useState<Message[]>([]);
    const [question, setQuestion] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const initialQuestion = searchParams.get('q');
        if (initialQuestion) {
            handleSubmit(initialQuestion);
        }
    }, [searchParams]);

    const handleSubmit = async (text: string) => {
        if (!text.trim()) return;

        setMessages(prev => [...prev, { type: 'question', text }]);
        setQuestion('');
        setLoading(true);

        try {
            const response = await apiClient.get<ApiResponse>(`/api/question/${encodeURIComponent(text)}`);
            setMessages(prev => [...prev, {
                type: 'answer',
                text: response.answer,
                sources: response.context?.source_nodes?.map(node => node.filename) || [],
                time_taken: response.context?.time_taken
            }]);
        } catch (err) {
            handleApiError(err);
        } finally {
            setLoading(false);
        }
    };

    const handleClearChat = () => setMessages([]);

    return (
        <div className={styles.chatContainer}>
            <MessageList 
                messages={messages} 
                loading={loading}
            />
            <div className={styles.inputContainer}>
                <div className={styles.inputWrapper}>
                    <textarea
                        className={styles.input}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Ask a question..."
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(question);
                            }
                        }}
                    />
                    <div className={styles.buttonGroup}>
                        <Button
                            onClick={() => handleSubmit(question)}
                            disabled={!question.trim() || loading}
                            icon="send"
                        >
                            Send
                        </Button>
                        <Button
                            onClick={onManageDocuments}
                            icon="folder"
                            variant="secondary"
                        >
                            Documents
                        </Button>
                        <Button
                            onClick={handleClearChat}
                            disabled={messages.length === 0}
                            icon="delete"
                            variant="danger"
                        >
                            Clear
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatWindow; 