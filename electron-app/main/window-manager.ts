import { BrowserWindow, screen } from 'electron';
import * as path from 'path';

export class WindowManager {
  private overlayWindow: BrowserWindow | null = null;

  public createOverlayWindow(): BrowserWindow {
    if (this.overlayWindow && !this.overlayWindow.isDestroyed()) {
      return this.overlayWindow;
    }

    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.bounds;

    this.overlayWindow = new BrowserWindow({
      x: primaryDisplay.bounds.x,
      y: primaryDisplay.bounds.y,
      width: width,
      height: height,
      transparent: true,
      frame: false,
      alwaysOnTop: true,
      skipTaskbar: true,
      hasShadow: false,
      resizable: false,
      movable: false,
      fullscreenable: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        sandbox: false,
      },
    });

    // Mandatory click-through configuration for transparent overlay
    this.overlayWindow.setIgnoreMouseEvents(true, { forward: true });
    this.overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    this.overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

    // Load overlay index.html
    const overlayHtmlPath = path.join(__dirname, '../../renderer/overlay/index.html');
    this.overlayWindow.loadFile(overlayHtmlPath);

    this.overlayWindow.on('closed', () => {
      this.overlayWindow = null;
    });

    console.log(`[WindowManager] Overlay window created (${width}x${height}, DPI scale: ${primaryDisplay.scaleFactor})`);
    return this.overlayWindow;
  }

  public getOverlayWindow(): BrowserWindow | null {
    return this.overlayWindow;
  }

  public closeAll(): void {
    if (this.overlayWindow && !this.overlayWindow.isDestroyed()) {
      this.overlayWindow.close();
      this.overlayWindow = null;
    }
  }
}
