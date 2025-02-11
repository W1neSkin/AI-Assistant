export {}; // Make it a module

const createFavicon = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    if (ctx) {
        // Draw the logo at 64x64
        // Background circle
        ctx.fillStyle = '#2c5282';
        ctx.beginPath();
        ctx.arc(32, 32, 30, 0, Math.PI * 2);
        ctx.fill();
        
        // Chat bubble
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(16, 16, 32, 32);
        
        // Dots
        ctx.fillStyle = '#2c5282';
        ctx.beginPath();
        ctx.arc(32, 26, 3, 0, Math.PI * 2);
        ctx.arc(24, 32, 3, 0, Math.PI * 2);
        ctx.arc(40, 32, 3, 0, Math.PI * 2);
        ctx.arc(32, 38, 3, 0, Math.PI * 2);
        ctx.fill();
        
        // Convert to favicon
        const link = document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = 'shortcut icon';
        link.href = canvas.toDataURL("image/x-icon");
        document.getElementsByTagName('head')[0].appendChild(link);
    }
};

export { createFavicon }; 