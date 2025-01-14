import React, { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import Chat from './components/Chat';
import DocumentsModal from './components/DocumentsModal';
import styles from './App.module.css';

const App: React.FC = () => {
    const [isDocModalOpen, setIsDocModalOpen] = useState(false);

    return (
        <div className={styles.app}>
            <Header onManageDocuments={() => setIsDocModalOpen(true)} />
            <main className={styles.main}>
                <Chat />
            </main>
            <Footer />
            <DocumentsModal 
                isOpen={isDocModalOpen} 
                onClose={() => setIsDocModalOpen(false)} 
            />
        </div>
    );
};

export default App;