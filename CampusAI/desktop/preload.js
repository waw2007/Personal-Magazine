// 预加载脚本：向渲染进程暴露受限的 IPC 能力
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  openMain: () => ipcRenderer.send('open-main'),
  hideWidget: () => ipcRenderer.send('hide-widget'),
})
