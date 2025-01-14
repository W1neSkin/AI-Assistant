import React from 'react';

interface Document {
    id: string;
    filename: string;
    active: boolean;
}

const DocumentList: React.FC<{ documents: Document[] }> = ({ documents }) => {
    const getFileIcon = (filename: string) => {
        const extension = filename.split('.').pop()?.toLowerCase();
        switch (extension) {
            case 'pdf':
                return '📄';
            case 'txt':
                return '📝';
            case 'html':
                return '🌐';
            case 'docx':
                return '📋';
            default:
                return '📎';
        }
    };

    return (
        <div>
            {documents.map(doc => (
                <div key={doc.id}>
                    {getFileIcon(doc.filename)} {doc.filename}
                </div>
            ))}
        </div>
    );
};

export default DocumentList; 