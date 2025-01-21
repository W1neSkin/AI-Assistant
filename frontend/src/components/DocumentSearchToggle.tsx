import React from 'react';
import styles from './ModelToggle.module.css'; // We can reuse the same styles

interface DocumentSearchToggleProps {
    enableDocSearch: boolean;
    onToggle: (enabled: boolean) => void;
    disabled?: boolean;
}

const DocumentSearchToggle: React.FC<DocumentSearchToggleProps> = ({ 
    enableDocSearch, 
    onToggle, 
    disabled = false
}) => {
    return (
        <div className={styles.toggleContainer}>
            <label className={styles.switch}>
                <input
                    type="checkbox"
                    checked={enableDocSearch}
                    onChange={(e) => onToggle(e.target.checked)}
                    disabled={disabled}
                />
                <span className={styles.slider}></span>
            </label>
            <span className={styles.label}>
                {enableDocSearch ? 'Doc Search On' : 'Doc Search Off'}
                {disabled && ' (Loading...)'}
            </span>
        </div>
    );
};

export default DocumentSearchToggle; 