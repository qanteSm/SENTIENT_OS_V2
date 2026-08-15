import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('sentientAPI', {
  sendEvent: (channel: string, data: any) => ipcRenderer.send(channel, data),
  onEvent: (channel: string, callback: (event: any, ...args: any[]) => void) =>
    ipcRenderer.on(channel, callback),
  onMessage: (callback: (data: any) => void) =>
    ipcRenderer.on('ws-message', (_event, data) => callback(data)),
});
