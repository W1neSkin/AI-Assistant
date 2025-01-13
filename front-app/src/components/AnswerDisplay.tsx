// front-app/src/components/AnswerDisplay.tsx
import React from 'react';
import styles from './AnswerDisplay.module.css';

interface SourceNode {
    text: string;
    score: number;
    document_id?: string;
}

interface AnswerDisplayProps {
    answer: string;
    context?: {
        source_nodes: SourceNode[];
    };
}

const AnswerDisplay: React.FC<AnswerDisplayProps> = ({ answer, context }) => {
    return (
        <div className={styles.answerDisplay}>
            <div className={styles.answerSection}>
                <h3>Answer:</h3>
                <div className={styles.answerText}>
                    {answer.split('\n').map((paragraph, index) => (
                        <p key={index}>{paragraph}</p>
                    ))}
                </div>
            </div>

            {context && context.source_nodes.length > 0 && (
                <div className={styles.contextSection}>
                    <h3>Source Context:</h3>
                    <div className={styles.contextList}>
                        {context.source_nodes.map((node, index) => (
                            <div key={index} className={styles.contextItem}>
                                <p className={styles.contextText}>{node.text}</p>
                                <span className={styles.contextScore}>
                                    Relevance: {(node.score * 100).toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AnswerDisplay;