import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/auth/ProtectedRoute';
import LoginForm from './components/auth/LoginForm';
import Chat from './components/Chat';
import Footer from './components/Footer';
import DocumentsModal from './components/DocumentsModal';
import styles from './App.module.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import RegisterForm from './components/auth/RegisterForm';
import Header from './components/Header';

function App() {
    const [isDocModalOpen, setIsDocModalOpen] = useState(false);

    return (
        <div className={styles.app}>
            <Header />
            <Routes>
                <Route path="/login" element={<LoginForm />} />
                <Route path="/register" element={<RegisterForm />} />
                <Route 
                    path="/" 
                    element={
                        <ProtectedRoute>
                            <main className={styles.main}>
                                <Chat onManageDocuments={() => setIsDocModalOpen(true)} />
                            </main>
                            <DocumentsModal
                                isOpen={isDocModalOpen}
                                onClose={() => setIsDocModalOpen(false)}
                                onUploadComplete={() => setIsDocModalOpen(false)}
                            />
                        </ProtectedRoute>
                    } 
                />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <Footer />
            <ToastContainer />
        </div>
    );
}

export default App;