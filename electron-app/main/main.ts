import { app, ipcMain, shell } from 'electron';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import { IPCBridge } from './ipc-bridge';
import { registerKillSwitch, unregisterKillSwitch } from './kill-switch';
import { setupTray, destroyTray } from './tray';
import { WindowManager } from './window-manager';

class Application {
  private pythonProcess: ChildProcess | null = null;
  private ipcBridge: IPCBridge;
  private windowManager: WindowManager;
  private isShuttingDown = false;

  constructor() {
    this.ipcBridge = new IPCBridge();
    this.windowManager = new WindowManager();
  }

  public async start(): Promise<void> {
    console.log('[MAIN] Starting SENTIENT_OS v2 Electron Application...');

    await app.whenReady();

    // 1. Setup backup kill switch (Ctrl+Shift+Q)
    registerKillSwitch(this.ipcBridge);

    // 2. Setup Tray
    setupTray(this.ipcBridge);

    // 3. Register IPC event handlers
    this.setupRendererIPCEvents();
    this.setupPythonWSEvents();

    // Check for direct test flags
    const gameMap: { [flag: string]: string } = {
      '--hub': 'hub.html',
      '--minigame': 'index.html',
      '--popups': 'popup_game.html',
      '--game1': 'games/game1_memory.html',
      '--game2': 'games/game2_slicer.html',
      '--game3': 'games/game3_wires.html',
      '--game4': 'games/game4_radar.html',
      '--game5': 'games/game5_cipher.html',
      '--game6': 'games/game6_cctv.html',
      '--game7': 'games/game7_hex.html',
      '--game8': 'games/game8_maze.html',
      '--game9': 'games/game9_reactor.html',
      '--game10': 'games/game10_trial.html',
    };

    for (const [flag, page] of Object.entries(gameMap)) {
      if (process.argv.includes(flag)) {
        console.log(`[MAIN] Running test flag ${flag} -> ${page}`);
        const win = this.windowManager.createMinigameWindow(page);
        win.show();
        win.focus();
        return;
      }
    }

    if (process.env.TEST_MINIGAME === '1') {
      const win = this.windowManager.createMinigameWindow('index.html');
      win.show();
      win.focus();
      return;
    }

    // 4. Start Python backend
    await this.spawnPythonBackend();
  }

  private setupRendererIPCEvents(): void {
    // Dynamic Minigame Switcher from Arcade Hub
    ipcMain.on('launch-minigame', (_event, pageName) => {
      console.log(`[MAIN] Launching minigame from Hub: ${pageName}`);
      this.windowManager.createMinigameWindow(pageName);
    });

    ipcMain.on('spawn-blackout', () => {
      this.windowManager.spawnMultiMonitorBlackout();
    });

    ipcMain.on('close-blackout', () => {
      this.windowManager.closeMultiMonitorBlackout();
    });

    // Renderer -> Main -> Python
    ipcMain.on('user-chat', (_event, data) => {
      this.ipcBridge.send('user_input', {
        text: data.text,
        source: 'electron_chat',
      });
    });

    ipcMain.on('system-event', (_event, data) => {
      this.ipcBridge.send('system_event', data);
    });

    ipcMain.on('onboarding-complete', (_event, data) => {
      console.log('[MAIN] Onboarding completed:', data);
      this.windowManager.closeOnboarding();
      this.windowManager.createOverlayWindow();

      this.ipcBridge.send('onboarding_complete', {
        intensity: data.intensity,
        language: data.language,
      });
    });

    ipcMain.on('minigame-result', (_event, data) => {
      console.log('[MAIN] Minigame finished with result:', data);
      this.windowManager.closeMinigame();
      this.ipcBridge.send('minigame_completed', data);
    });

    ipcMain.on('close-minigame', () => {
      console.log('[MAIN] Closing minigame window via renderer request');
      this.windowManager.closeMinigame();
    });

    ipcMain.on('app-exit', () => {
      this.shutdown();
    });
  }

  private setupPythonWSEvents(): void {
    this.ipcBridge.on('ready', (payload) => {
      console.log('[MAIN] Python backend ready. Launching Onboarding Wizard...', payload);
      this.windowManager.createOnboardingWindow();
    });

    const forwardToAll = (type: string, payload: any) => {
      const overlayWin = this.windowManager.getOverlayWindow();
      if (overlayWin && !overlayWin.isDestroyed()) {
        overlayWin.webContents.send('ws-message', { type, payload });
      }

      const chatWin = this.windowManager.getChatWindow();
      if (chatWin && !chatWin.isDestroyed()) {
        chatWin.webContents.send('ws-message', { type, payload });
      }

      const minigameWin = this.windowManager.getMinigameWindow();
      if (minigameWin && !minigameWin.isDestroyed()) {
        minigameWin.webContents.send('ws-message', { type, payload });
      }
    };

    this.ipcBridge.on('effect', (payload) => {
      forwardToAll('effect', payload);
    });

    this.ipcBridge.on('ambient_change', (payload) => {
      forwardToAll('ambient_change', payload);
    });

    this.ipcBridge.on('cctv_anomaly_update', (payload) => {
      forwardToAll('cctv_anomaly_update', payload);
    });

    this.ipcBridge.on('ui_command', (payload) => {
      console.log('[MAIN] Received ui_command:', payload);
      const cmd = payload?.command;
      if (cmd === 'open_chat') {
        const chatWin = this.windowManager.createChatWindow();
        setTimeout(() => {
          chatWin.webContents.send('ws-message', { type: 'ui_command', payload });
        }, 500);
      } else if (cmd === 'trigger_minigame' || cmd === 'open_minigame') {
        const page = payload?.params?.page || 'hub.html';
        const minigameWin = this.windowManager.createMinigameWindow(page);
        minigameWin.show();
        minigameWin.focus();
      } else if (cmd === 'open_arg_site' || cmd === 'open_arg_portal') {
        const url = payload?.params?.url || 'http://127.0.0.1:6660';
        console.log(`[MAIN] Opening ARG Portal: ${url}`);
        shell.openExternal(url);
      } else {
        forwardToAll('ui_command', payload);
      }
    });

    this.ipcBridge.on('ai_response', (payload) => {
      console.log('[MAIN] Received AI Response from Python:', payload?.speech?.slice(0, 30));
      forwardToAll('ai_response', payload);
    });

    this.ipcBridge.on('narrative_event', (payload) => {
      forwardToAll('narrative_event', payload);
    });

    this.ipcBridge.on('shutdown', () => {
      console.log('[MAIN] Received shutdown signal from Python');
      this.shutdown();
    });

    this.ipcBridge.on('fatal_connection_loss', () => {
      console.error('[MAIN] Fatal loss of Python backend connection. Exiting.');
      this.shutdown();
    });
  }

  private spawnPythonBackend(): Promise<void> {
    return new Promise((resolve) => {
      if (process.env.SENTIENT_PORT) {
        const port = parseInt(process.env.SENTIENT_PORT, 10);
        console.log(`[MAIN] Using predefined Python WS port: ${port}`);
        this.ipcBridge.connect(port);
        resolve();
        return;
      }

      const pythonEngineDir = path.resolve(__dirname, '../../../python-engine');
      console.log(`[MAIN] Spawning Python engine from: ${pythonEngineDir}`);

      this.pythonProcess = spawn('python', ['-m', 'src.main'], {
        cwd: pythonEngineDir,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
        },
      });

      let portDiscovered = false;

      this.pythonProcess.stdout?.on('data', (data: Buffer) => {
        const text = data.toString('utf-8');
        process.stdout.write(`[PYTHON] ${text}`);

        const match = text.match(/WS_PORT:(\d+)/);
        if (match && !portDiscovered) {
          portDiscovered = true;
          const port = parseInt(match[1], 10);
          console.log(`[MAIN] Python backend announced WebSocket port: ${port}`);
          this.ipcBridge.connect(port);
          resolve();
        }
      });

      this.pythonProcess.stderr?.on('data', (data: Buffer) => {
        process.stderr.write(`[PYTHON ERR] ${data.toString('utf-8')}`);
      });

      this.pythonProcess.on('exit', (code, signal) => {
        console.warn(`[MAIN] Python backend process exited with code ${code}, signal ${signal}`);
        if (!this.isShuttingDown) {
          this.shutdown();
        }
      });

      setTimeout(() => {
        if (!portDiscovered) {
          console.error('[MAIN] Timeout waiting for Python WS_PORT. Trying fallback port 5000...');
          this.ipcBridge.connect(5000);
          resolve();
        }
      }, 15000);
    });
  }

  public shutdown(): void {
    if (this.isShuttingDown) return;
    this.isShuttingDown = true;
    console.log('[MAIN] Initiating clean shutdown...');

    unregisterKillSwitch();
    destroyTray();
    this.windowManager.closeAll();
    this.ipcBridge.close();

    if (this.pythonProcess && !this.pythonProcess.killed) {
      console.log('[MAIN] Terminating child Python process...');
      this.pythonProcess.kill('SIGTERM');
    }

    setTimeout(() => {
      app.quit();
    }, 500);
  }
}

const sentientApp = new Application();
sentientApp.start().catch((err) => {
  console.error('[MAIN] Fatal application startup error:', err);
  app.exit(1);
});

app.on('window-all-closed', () => {
  // Keep app active in background
});
