import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // 相对路径，使构建产物可在 Electron 的 file:// 下正常加载
})
