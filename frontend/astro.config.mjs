// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  devToolbar: {
    enabled: false,
  },
  vite: {
    plugins: [tailwindcss()],
    server: {
      proxy: {
        '/api': {
          target: process.env.BACKEND_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/health': {
          target: process.env.BACKEND_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
  },
});
