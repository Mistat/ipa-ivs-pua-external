import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: './src',
  plugins: [
    react(),
    {
      name: 'configure-server',
      configureServer(server) {
        const path = require('path');
        const fs = require('fs');
        const fontsPath = path.resolve(process.cwd(), '../../fonts');
        
        server.middlewares.use('/fonts', (req, res, next) => {
          const filePath = path.join(fontsPath, req.url.replace('/fonts', ''));
          
          if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
            res.setHeader('Content-Type', 
              filePath.endsWith('.ttf') ? 'font/ttf' :
              filePath.endsWith('.woff2') ? 'font/woff2' :
              filePath.endsWith('.woff') ? 'font/woff' : 'application/octet-stream'
            );
            fs.createReadStream(filePath).pipe(res);
          } else {
            next();
          }
        });
      }
    }
  ],
  base: process.env.NODE_ENV === 'production' ? '/ipa-ivs-pua-external/pdf-react/' : '/',
  server: {
    port: 3000,
    host: true
  },
  build: {
    outDir: '../../docs/pdf-react',
    emptyOutDir: true
  },
  define: {
    global: 'globalThis'
  }
});