import { BrowserWindow, screen } from 'electron';
import * as path from 'path';

export class WindowManager {
  private overlayWindow: BrowserWindow | null = null;
  private chatWindow: BrowserWindow | null = null;
  private onboardingWindow: BrowserWindow | null = null;
  private minigameWindow: BrowserWindow | null = null;

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

    this.overlayWindow.setIgnoreMouseEvents(true, { forward: true });
    this.overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    this.overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

    const overlayHtmlPath = path.join(__dirname, '../../renderer/overlay/index.html');
    this.overlayWindow.loadFile(overlayHtmlPath);

    this.overlayWindow.on('closed', () => {
      this.overlayWindow = null;
    });

    console.log(`[WindowManager] Overlay window created (${width}x${height})`);
    return this.overlayWindow;
  }

  public createChatWindow(): BrowserWindow {
    if (this.chatWindow && !this.chatWindow.isDestroyed()) {
      this.chatWindow.show();
      this.chatWindow.focus();
      return this.chatWindow;
    }

    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.bounds;

    this.chatWindow = new BrowserWindow({
      width: 440,
      height: 580,
      x: width - 480,
      y: height - 640,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: true,
      minWidth: 360,
      minHeight: 450,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        sandbox: false,
      },
    });

    const chatHtmlPath = path.join(__dirname, '../../renderer/chat/index.html');
    this.chatWindow.loadFile(chatHtmlPath);

    this.chatWindow.on('closed', () => {
      this.chatWindow = null;
    });

    console.log('[WindowManager] Chat window created.');
    return this.chatWindow;
  }

  public createOnboardingWindow(): BrowserWindow {
    if (this.onboardingWindow && !this.onboardingWindow.isDestroyed()) {
      this.onboardingWindow.show();
      this.onboardingWindow.focus();
      return this.onboardingWindow;
    }

    this.onboardingWindow = new BrowserWindow({
      width: 600,
      height: 650,
      frame: false,
      center: true,
      resizable: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        sandbox: false,
      },
    });

    const onboardingHtmlPath = path.join(__dirname, '../../renderer/onboarding/index.html');
    this.onboardingWindow.loadFile(onboardingHtmlPath);

    this.onboardingWindow.on('closed', () => {
      this.onboardingWindow = null;
    });

    console.log('[WindowManager] Onboarding window created.');
    return this.onboardingWindow;
  }

  private blackoutWindows: BrowserWindow[] = [];

  public createMinigameWindow(pageName: string = 'hub.html'): BrowserWindow {
    if (this.minigameWindow && !this.minigameWindow.isDestroyed()) {
      const minigameHtmlPath = path.join(__dirname, `../../renderer/minigame/${pageName}`);
      this.minigameWindow.loadFile(minigameHtmlPath);
      this.minigameWindow.show();
      return this.minigameWindow;
    }

    const primaryDisplay = screen.getPrimaryDisplay();

    this.minigameWindow = new BrowserWindow({
      x: primaryDisplay.bounds.x,
      y: primaryDisplay.bounds.y,
      width: primaryDisplay.bounds.width,
      height: primaryDisplay.bounds.height,
      fullscreen: true,
      kiosk: true,
      frame: false,
      transparent: false,
      backgroundColor: '#000000',
      alwaysOnTop: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        sandbox: false,
      },
    });

    this.minigameWindow.setAlwaysOnTop(true, 'screen-saver');

    const minigameHtmlPath = path.join(__dirname, `../../renderer/minigame/${pageName}`);
    this.minigameWindow.loadFile(minigameHtmlPath);

    // Escape Key Safeguard: Closes minigame window safely and returns to desktop/chat
    this.minigameWindow.webContents.on('before-input-event', (_event, input) => {
      if (input.key === 'Escape' && input.type === 'keyDown') {
        this.closeMinigame();
      }
    });

    this.minigameWindow.on('closed', () => {
      this.minigameWindow = null;
      this.closeMultiMonitorBlackout();
    });

    console.log(`[WindowManager] Minigame window created (${pageName}).`);
    return this.minigameWindow;
  }

  public spawnMultiMonitorBlackout(): void {
    this.closeMultiMonitorBlackout();
    const displays = screen.getAllDisplays();
    const primary = screen.getPrimaryDisplay();

    for (const display of displays) {
      if (display.id !== primary.id) {
        const blackoutWin = new BrowserWindow({
          x: display.bounds.x,
          y: display.bounds.y,
          width: display.bounds.width,
          height: display.bounds.height,
          fullscreen: true,
          kiosk: true,
          frame: false,
          backgroundColor: '#000000',
          alwaysOnTop: true,
          focusable: false,
          skipTaskbar: true,
        });
        blackoutWin.setAlwaysOnTop(true, 'screen-saver');
        this.blackoutWindows.push(blackoutWin);
      }
    }
  }

  public closeMultiMonitorBlackout(): void {
    for (const win of this.blackoutWindows) {
      if (win && !win.isDestroyed()) {
        win.close();
      }
    }
    this.blackoutWindows = [];
  }

  public getOverlayWindow(): BrowserWindow | null {
    return this.overlayWindow;
  }

  public getChatWindow(): BrowserWindow | null {
    return this.chatWindow;
  }

  public closeOnboarding(): void {
    if (this.onboardingWindow && !this.onboardingWindow.isDestroyed()) {
      this.onboardingWindow.close();
      this.onboardingWindow = null;
    }
  }

  public closeMinigame(): void {
    if (this.minigameWindow && !this.minigameWindow.isDestroyed()) {
      this.minigameWindow.close();
      this.minigameWindow = null;
    }
    this.closeMultiMonitorBlackout();
  }

  public closeAll(): void {
    [this.overlayWindow, this.chatWindow, this.onboardingWindow, this.minigameWindow, ...this.blackoutWindows].forEach((win) => {
      if (win && !win.isDestroyed()) {
        win.close();
      }
    });
    this.overlayWindow = null;
    this.chatWindow = null;
    this.onboardingWindow = null;
    this.minigameWindow = null;
    this.blackoutWindows = [];
  }
}
