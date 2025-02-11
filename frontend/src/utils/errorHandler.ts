import { toast } from 'react-toastify';

export class AppError extends Error {
    constructor(
        public statusCode: number,
        message: string,
        public details?: any
    ) {
        super(message);
    }
}

export const handleApiError = (error: unknown) => {
    if (error instanceof AppError) {
        toast.error(error.message);
    } else {
        toast.error('An unexpected error occurred');
        console.error(error);
    }
}; 