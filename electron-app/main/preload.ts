import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('sentientAPI', {
  sendEvent: (channel: string, data: any) => ipcRenderer.send(channel, data),
  onEvent: (channel: string, callback: (event: any, ...args: any[]) => void) =>
    ipcRenderer.on(channel, callback),
});
