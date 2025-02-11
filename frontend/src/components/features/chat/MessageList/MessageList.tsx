import React from 'react';
import styles from './MessageList.module.css';
import { Message } from '../../../../types/chat';

interface MessageListProps {
    messages: Message[];
    loading: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, loading }) => {
    return (
        <div className={styles.messagesContainer}>
            {messages.map((message, index) => (
                <div 
                    key={index}
                    className={`${styles.message} ${styles[message.type]}`}
                >
                    <div className={styles.messageContent}>
                        {message.text}
                    </div>
                    {message.type === 'answer' && message.sources && message.sources.length > 0 && (
                        <div className={styles.sources}>
                            Sources: {message.sources.join(', ')}
                            {message.time_taken && (
                                <span className={styles.timeTaken}>
                                    ({(message.time_taken / 1000).toFixed(2)}s)
                                </span>
                            )}
                        </div>
                    )}
                </div>
            ))}
            {loading && (
                <div className={styles.loadingIndicator}>
                    Thinking...
                </div>
            )}
        </div>
    );
};

export default MessageList; 