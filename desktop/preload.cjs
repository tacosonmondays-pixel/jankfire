// The only things the game page can ask the desktop app to do. No file or system access is exposed.
// main.cjs checks who is asking as well: these are only the calls a page of that kind can use.
const { contextBridge, ipcRenderer } = require('electron');
const jf = {
  desktop: true,
  info: () => ipcRenderer.invoke('jf:info'),
  launcher: () => ipcRenderer.invoke('jf:launcher'),
  fullscreen: () => ipcRenderer.invoke('jf:fullscreen'),
  display: (mode) => ipcRenderer.invoke('jf:display', String(mode)),
  displayGet: () => ipcRenderer.invoke('jf:displayGet'),
  quit: () => ipcRenderer.invoke('jf:quit'),
};
// starting a server or picking one is for the launcher (a file inside the app), never for a page from a server
if (location.protocol === 'file:') {
  jf.host = () => ipcRenderer.invoke('jf:host');
  jf.join = (url) => ipcRenderer.invoke('jf:join', String(url));
}
contextBridge.exposeInMainWorld('jf', jf);
