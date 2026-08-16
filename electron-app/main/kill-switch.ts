import { globalShortcut, app } from 'electron';
import { IPCBridge } from './ipc-bridge';

export function registerKillSwitch(ipcBridge: IPCBridge): void {
  const registered = globalShortcut.register('Ctrl+Shift+Q', () => {
    if (ipcBridge && ipcBridge.isReady()) {
      try {
        ipcBridge.send('kill_switch');
      } catch (e) {
        console.error('[KILL SWITCH] Failed to signal backend:', e);
      }
    }
    // Hard exit after short grace period for backend signal
    setTimeout(() => {
      app.exit(0);
    }, (ipcBridge && ipcBridge.isReady()) ? 800 : 100);
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
