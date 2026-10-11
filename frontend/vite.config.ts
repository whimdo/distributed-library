import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          element: ['element-plus', '@element-plus/icons-vue'],
          map: ['ol/Map', 'ol/View', 'ol/layer/Tile', 'ol/layer/Vector', 'ol/source/OSM', 'ol/source/Vector', 'ol/format/GeoJSON'],
          editor: ['codemirror', '@codemirror/lang-sql', '@codemirror/theme-one-dark'],
        },
      },
    },
  },
})
