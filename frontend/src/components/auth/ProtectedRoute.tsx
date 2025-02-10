import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        // Redirect to login if there's no token
        return <Navigate to="/login" replace />;
    }
    
    return <>{children}</>;
};

export default ProtectedRoute; 