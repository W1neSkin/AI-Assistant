import React from 'react';
import styles from './ModelToggle.module.css';

interface ModelToggleProps {
    isLocal: boolean;
    onToggle: (isLocal: boolean) => void;
    disabled?: boolean;
    models?: string[];
}

const ModelToggle: React.FC<ModelToggleProps> = ({ 
    isLocal, 
    onToggle, 
    disabled,
    models = ['local', 'openai']  // Default values if not provided
}) => {
    return (
        <div className={styles.toggleContainer}>
            <label className={styles.switch}>
                <input
                    type="checkbox"
                    checked={isLocal}
                    onChange={(e) => onToggle(e.target.checked)}
                    disabled={disabled}
                />
                <span className={styles.slider}></span>
            </label>
            <span className={styles.label}>
                {isLocal ? 'Local' : 'OpenAI'}
                {disabled && ' (Loading...)'}
            </span>
        </div>
    );
};

export default ModelToggle; 