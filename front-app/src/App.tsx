import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import QuestionForm from './components/QuestionForm';
import AnswerDisplay from './components/AnswerDisplay';
import Header from './components/Header';
import Footer from './components/Footer';
import styles from './App.module.css';
import { QuestionResponse } from './api';

const App: React.FC = () => {
    const [response, setResponse] = useState<QuestionResponse | null>(null);

    return (
        <div className={styles.app}>
            <Header />
            <div className={styles.content}>
                <FileUpload />
                <QuestionForm onAnswerReceived={setResponse} />
                {response && (
                    <AnswerDisplay 
                        answer={response.answer} 
                        context={response.context}
                    />
                )}
            </div>
            <Footer />
        </div>
    );
};

export default App;