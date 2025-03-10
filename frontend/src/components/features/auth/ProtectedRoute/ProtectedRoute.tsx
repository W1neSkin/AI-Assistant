import React from 'react';
import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const isAuthenticated = !!localStorage.getItem('access_token');
    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

export default ProtectedRoute; 