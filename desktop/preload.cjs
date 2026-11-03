// The only things the game page can ask the desktop app to do. No file or system access is exposed.
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('jf', {
  desktop: true,
  info: () => ipcRenderer.invoke('jf:info'),
  host: () => ipcRenderer.invoke('jf:host'),
  join: (url) => ipcRenderer.invoke('jf:join', String(url)),
  launcher: () => ipcRenderer.invoke('jf:launcher'),
  fullscreen: () => ipcRenderer.invoke('jf:fullscreen'),
  quit: () => ipcRenderer.invoke('jf:quit'),
});
