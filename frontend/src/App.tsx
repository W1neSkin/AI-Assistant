import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import styles from './App.module.css';
import { ChatWindow } from './components/features/chat';
import { LoginForm, RegisterForm, ProtectedRoute } from './components/features/auth';
import { Header, Footer } from './components/layout';
import { DocumentsModal } from './components/features/documents';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
    const [isDocModalOpen, setIsDocModalOpen] = useState(false);

    return (
        <div className={styles.app}>
            <Header />
            <Routes>
                <Route path="/login" element={<LoginForm />} />
                <Route path="/register" element={<RegisterForm />} />
                <Route path="/" element={
                    <ProtectedRoute>
                        <main className={styles.main}>
                            <ChatWindow onManageDocuments={() => setIsDocModalOpen(true)} />
                        </main>
                        <DocumentsModal
                            isOpen={isDocModalOpen}
                            onClose={() => setIsDocModalOpen(false)}
                            onUploadComplete={() => setIsDocModalOpen(false)}
                        />
                    </ProtectedRoute>
                } />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <Footer />
            <ToastContainer />
        </div>
    );
}

export default App;