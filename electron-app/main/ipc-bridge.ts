import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface IPCMessage {
  type: string;
  id?: string;
  timestamp?: number;
  payload?: any;
}

export class IPCBridge extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string = '';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isHandshakeComplete = false;

  constructor() {
    super();
  }

  public connect(port: number, host: string = '127.0.0.1'): void {
    this.url = `ws://${host}:${port}`;
    this.initSocket();
  }

  private initSocket(): void {
    console.log(`[IPC] Connecting to Python backend at ${this.url}...`);
    this.ws = new WebSocket(this.url);

    this.ws.on('open', () => {
      console.log('[IPC] WebSocket connection opened. Sending handshake...');
      this.reconnectAttempts = 0;
      this.sendHandshake();
    });

    this.ws.on('message', (raw: WebSocket.Data) => {
      try {
        const text = raw.toString('utf-8');
        const data: IPCMessage = JSON.parse(text);
        this.handleInboundMessage(data);
      } catch (err) {
        console.error('[IPC] Failed to parse message from Python:', err);
      }
    });

    this.ws.on('close', (code, reason) => {
      console.warn(`[IPC] Connection closed (${code}: ${reason.toString()})`);
      this.isHandshakeComplete = false;
      this.emit('disconnected');
      this.scheduleReconnect();
    });

    this.ws.on('error', (err) => {
      console.error('[IPC] WebSocket error:', err.message);
    });
  }

  private sendHandshake(): void {
    this.send('handshake', {
      version: '2.0',
      electron_pid: process.pid,
      platform: process.platform,
    });
  }

  private handleInboundMessage(msg: IPCMessage): void {
    if (!msg || !msg.type) return;

    if (msg.type === 'handshake_ack') {
      this.isHandshakeComplete = true;
      console.log('[IPC] Handshake acknowledged by Python engine:', msg.payload);
      this.emit('ready', msg.payload);
      return;
    }

    if (msg.type === 'shutdown') {
      console.log('[IPC] Python engine requested shutdown');
      this.emit('shutdown', msg.payload);
      return;
    }

    // Emit event for listeners (Window Manager, Overlay, etc.)
    this.emit(msg.type, msg.payload, msg.id);
    this.emit('message', msg);
  }

  public send(type: string, payload: any = {}): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn(`[IPC] Cannot send '${type}' - WebSocket is not open.`);
      return;
    }

    const message: IPCMessage = {
      type,
      id: `el_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      timestamp: Math.floor(Date.now() / 1000),
      payload,
    };

    this.ws.send(JSON.stringify(message));
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[IPC] Maximum reconnection attempts reached. Giving up.');
      this.emit('fatal_connection_loss');
      return;
    }

    this.reconnectAttempts++;
    console.log(`[IPC] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in 1000ms...`);
    this.reconnectTimer = setTimeout(() => {
      this.initSocket();
    }, 1000);
  }

  public close(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public isReady(): boolean {
    return this.isHandshakeComplete && this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
