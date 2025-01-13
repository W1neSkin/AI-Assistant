import React, { useState } from 'react';
import { askQuestion, QuestionResponse } from '../api';
import styles from './QuestionForm.module.css';

interface QuestionFormProps {
    onAnswerReceived: (response: QuestionResponse | null) => void;
}

const QuestionForm: React.FC<QuestionFormProps> = ({ onAnswerReceived }) => {
    const [question, setQuestion] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setLoading(true);
        try {
            const response = await askQuestion(question);
            onAnswerReceived(response);
            console.log('Question response:', response);
        } catch (error) {
            console.error('Error asking question:', error);
            alert('Failed to get an answer.');
            onAnswerReceived(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className={styles.questionForm}>
            <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Enter your question"
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Asking...' : 'Ask'}
            </button>
        </form>
    );
};

export default QuestionForm;