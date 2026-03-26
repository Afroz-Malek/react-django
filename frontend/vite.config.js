import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8050,
    strictPort: false, // Allow Vite to use next available port if 8050 is in use
  },
})
