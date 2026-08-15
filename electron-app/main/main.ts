import { app, BrowserWindow } from 'electron';
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

    // Wait for electron app readiness
    await app.whenReady();

    // 1. Setup backup kill switch (Ctrl+Shift+Q)
    registerKillSwitch(this.ipcBridge);

    // 2. Setup Tray
    setupTray(this.ipcBridge);

    // 3. Register IPC event handlers
    this.setupIPCEvents();

    // 4. Start or connect to Python backend
    await this.spawnPythonBackend();
  }

  private setupIPCEvents(): void {
    this.ipcBridge.on('ready', (payload) => {
      console.log('[MAIN] Python backend ready. Opening overlay window...', payload);
      this.windowManager.createOverlayWindow();

      // Echo test message for Phase 1 validation
      this.ipcBridge.send('user_input', {
        text: 'Electron connected successfully (Phase 1 Foundation)',
        source: 'electron_main',
      });
    });

    this.ipcBridge.on('ai_response', (payload) => {
      console.log('[MAIN] Received AI Response from Python:', payload);
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
      // Check if external python engine port passed via environment variable
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

        // Scan line for WS_PORT:{port} announcement
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

      // Fallback timeout if WS_PORT is not received in 15 seconds
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
  // Prevent quitting automatically on overlay close unless shutdown initiated
});
