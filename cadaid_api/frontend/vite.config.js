import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueDevTools from 'vite-plugin-vue-devtools';
import dotenv from 'dotenv';

// Load the correct environment file
const mode = process.env.NODE_ENV || 'development';
const envFile = `.env.${mode}`;
dotenv.config({ path: envFile });

// Debug logs to verify environment variables
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('VITE_API_URL:', process.env.VITE_API_URL);
console.log('VITE_API_KEY:', process.env.VITE_API_KEY);

// Vite configuration
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});
