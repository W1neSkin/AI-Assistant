import React, { useState } from 'react';
import Chat from './components/Chat';
import Footer from './components/Footer';
import DocumentsModal from './components/DocumentsModal';
import styles from './App.module.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
    const [isDocModalOpen, setIsDocModalOpen] = useState(false);

    const handleUploadComplete = () => {
        // You might want to refresh the chat or clear previous responses
        setIsDocModalOpen(false);
    };

    return (
        <div className={styles.app}>
            <main className={styles.main}>
                <Chat onManageDocuments={() => setIsDocModalOpen(true)} />
            </main>
            <Footer />
            <DocumentsModal
                isOpen={isDocModalOpen}
                onClose={() => setIsDocModalOpen(false)}
                onUploadComplete={handleUploadComplete}
            />
            <ToastContainer />
        </div>
    );
}

export default App;