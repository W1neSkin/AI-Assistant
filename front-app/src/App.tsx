import React, { useState } from 'react';
import QuestionForm from './components/QuestionForm';
import AnswerDisplay from './components/AnswerDisplay';
import DocumentsModal from './components/DocumentsModal';
import Header from './components/Header';
import Footer from './components/Footer';
import styles from './App.module.css';
import { QuestionResponse } from './api';

const App: React.FC = () => {
    const [response, setResponse] = useState<QuestionResponse | null>(null);
    const [isDocumentsModalOpen, setIsDocumentsModalOpen] = useState(false);

    return (
        <div className={styles.app}>
            <Header />
            <div className={styles.content}>
                <div className={styles.toolbar}>
                    <button 
                        onClick={() => setIsDocumentsModalOpen(true)}
                        className={styles.documentsButton}
                    >
                        <svg 
                            width="16" 
                            height="16" 
                            viewBox="0 0 16 16" 
                            fill="none" 
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path 
                                d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2z" 
                                fill="currentColor"
                            />
                            <path 
                                d="M4 4h8v1H4V4zm0 3h8v1H4V7zm0 3h8v1H4v-1z" 
                                fill="white"
                            />
                        </svg>
                        Documents
                    </button>
                </div>
                <div className={styles.chatSection}>
                    <QuestionForm onAnswerReceived={setResponse} />
                    {response && (
                        <AnswerDisplay 
                            answer={response.answer} 
                            context={response.context}
                        />
                    )}
                </div>
            </div>
            <DocumentsModal 
                isOpen={isDocumentsModalOpen}
                onClose={() => setIsDocumentsModalOpen(false)}
            />
            <Footer />
        </div>
    );
};

export default App;