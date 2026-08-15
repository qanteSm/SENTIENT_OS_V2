import { app, Menu, nativeImage, Tray } from 'electron';
import { IPCBridge } from './ipc-bridge';

let tray: Tray | null = null;

export function setupTray(ipcBridge: IPCBridge): Tray {
  // Create a minimal 16x16 transparent/monochrome icon fallback if asset file not present
  const icon = nativeImage.createEmpty();

  tray = new Tray(icon);
  tray.setToolTip('SENTIENT_OS v2');

  const contextMenu = Menu.buildFromTemplate([
    { label: 'SENTIENT_OS v2', enabled: false },
    { type: 'separator' },
    {
      label: 'Acil Çıkış (Ctrl+Shift+Q)',
      click: () => {
        console.log('[TRAY] Emergency exit requested from tray menu');
        ipcBridge.send('kill_switch');
        setTimeout(() => {
          app.exit(0);
        }, 1000);
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  return tray;
}

export function destroyTray(): void {
  if (tray) {
    tray.destroy();
    tray = null;
  }
}
