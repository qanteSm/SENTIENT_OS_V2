import { globalShortcut, app } from 'electron';
import { IPCBridge } from './ipc-bridge';

export function registerKillSwitch(ipcBridge: IPCBridge): void {
  const registered = globalShortcut.register('Ctrl+Shift+Q', () => {
    console.warn('[KILL SWITCH] Emergency shutdown hotkey detected in Electron process!');
    try {
      ipcBridge.send('kill_switch');
    } catch (e) {
      console.error('[KILL SWITCH] Failed to signal backend:', e);
    }
    // Hard exit after short grace period for backend signal
    setTimeout(() => {
      app.exit(0);
    }, 1500);
  });

  if (!registered) {
    console.error('[KILL SWITCH] Registration of Ctrl+Shift+Q in Electron failed.');
  } else {
    console.log('[KILL SWITCH] Electron backup kill switch registered (Ctrl+Shift+Q)');
  }
}

export function unregisterKillSwitch(): void {
  globalShortcut.unregister('Ctrl+Shift+Q');
}
