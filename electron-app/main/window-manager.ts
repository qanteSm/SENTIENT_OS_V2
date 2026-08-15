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

  public createMinigameWindow(): BrowserWindow {
    if (this.minigameWindow && !this.minigameWindow.isDestroyed()) {
      this.minigameWindow.show();
      return this.minigameWindow;
    }

    this.minigameWindow = new BrowserWindow({
      fullscreen: true,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        sandbox: false,
      },
    });

    const minigameHtmlPath = path.join(__dirname, '../../renderer/minigame/index.html');
    this.minigameWindow.loadFile(minigameHtmlPath);

    this.minigameWindow.on('closed', () => {
      this.minigameWindow = null;
    });

    console.log('[WindowManager] Minigame window created.');
    return this.minigameWindow;
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
  }

  public closeAll(): void {
    [this.overlayWindow, this.chatWindow, this.onboardingWindow, this.minigameWindow].forEach((win) => {
      if (win && !win.isDestroyed()) {
        win.close();
      }
    });
    this.overlayWindow = null;
    this.chatWindow = null;
    this.onboardingWindow = null;
    this.minigameWindow = null;
  }
}
