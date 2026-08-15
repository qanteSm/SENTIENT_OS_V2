/**
 * SENTIENT_OS v2 — Master Effect Engine
 * Coordinates all Visual Effects, Audio Layers, and Priority Queues.
 */

class MasterEffectEngine {
  constructor() {
    this.canvas = document.getElementById('glitch-canvas');
    this.setupCanvas();

    // Effect Modules
    this.glitch = new GlitchEffect(this.canvas);
    this.textOverlay = new TextOverlayEffect(document.getElementById('text-overlay-layer'));
    this.fade = new FadeEffect(document.getElementById('screen-fade-layer'));
    this.shake = new ShakeEffect(document.getElementById('overlay-container'));
    this.bsod = new FakeBSODEffect();
    this.notification = new FakeNotificationEffect();

    // Audio Modules
    this.ambient = new AmbientEngine();
    this.spatialAudio = new SpatialAudioPlayer(this.ambient);
    this.tts = new TTSPlayer(this.ambient);

    // Queue & State
    this.queue = [];
    this.isProcessingQueue = false;
    this.intensityReductionFactor = 1.0;

    this.initListeners();
  }

  setupCanvas() {
    if (!this.canvas) return;
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
  }

  resizeCanvas() {
    if (this.canvas) {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
    }
  }

  initListeners() {
    // Listen to IPC bridge messages if available
    if (window.sentientAPI && window.sentientAPI.onMessage) {
      window.sentientAPI.onMessage((msg) => {
        this.handleIncomingMessage(msg);
      });
    }

    // User interaction unlock for Web Audio API autoplay policy
    const unlockAudio = () => {
      this.ambient.ensureContext();
      window.removeEventListener('click', unlockAudio);
      window.removeEventListener('keydown', unlockAudio);
    };
    window.addEventListener('click', unlockAudio);
    window.addEventListener('keydown', unlockAudio);
  }

  handleIncomingMessage(msg) {
    if (!msg || !msg.type) return;

    if (msg.type === 'effect') {
      const payload = msg.payload || msg;
      this.enqueue(payload, payload.priority || 'normal');
    } else if (msg.type === 'ambient_change') {
      const p = msg.payload || {};
      this.ambient.setMood(p.mood || 'calm', (p.fade_ms || 3000) / 1000.0);
    } else if (msg.type === 'effect_chain') {
      this.executeChain(msg.payload || msg);
    }
  }

  enqueue(command, priority = 'normal') {
    const priorityWeights = { critical: 4, high: 3, normal: 2, low: 1 };
    const weight = priorityWeights[priority] || 2;

    this.queue.push({ command, weight });
    this.queue.sort((a, b) => b.weight - a.weight);

    if (!this.isProcessingQueue) {
      this.processQueue();
    }
  }

  async processQueue() {
    if (this.queue.length === 0) {
      this.isProcessingQueue = false;
      return;
    }

    this.isProcessingQueue = true;
    const item = this.queue.shift();
    if (item && item.command) {
      await this.executeCommand(item.command);
    }

    setTimeout(() => this.processQueue(), 50);
  }

  async executeCommand(cmd) {
    const name = cmd.name || cmd.type;
    const params = { ...(cmd.params || {}) };
    const delayMs = cmd.delay_ms || 0;

    if (delayMs > 0) {
      await new Promise((r) => setTimeout(r, delayMs));
    }

    console.log(`[EffectEngine] Executing effect: ${name}`, params);

    switch (name) {
      // Visual Effects
      case 'screen_glitch':
        this.glitch.trigger(params);
        break;
      case 'overlay_text':
        this.textOverlay.trigger(params);
        break;
      case 'screen_fade':
        this.fade.trigger(params);
        break;
      case 'blackout':
        this.fade.blackout(params.duration_ms || 2500);
        break;
      case 'flash':
        this.fade.flash(params.color || '#ffffff', params.duration_ms || 500);
        break;
      case 'screen_shake':
        this.shake.trigger(params);
        break;
      case 'fake_bsod':
        this.bsod.trigger(params);
        break;

      // System / UI Effects
      case 'fake_notification':
        this.notification.trigger(params);
        break;

      // Audio Effects
      case 'ambient_shift':
      case 'ambient_change':
        this.ambient.setMood(params.mood || 'calm', (params.fade_ms || 3000) / 1000.0);
        break;
      case 'play_sfx':
        this.spatialAudio.playSFX(params.name || 'click_soft', params);
        break;
      case 'play_stinger':
        this.spatialAudio.playStinger(params.name || 'stinger_scare', params);
        break;
      case 'tts_play':
        this.tts.playAudioFile(params.file_path);
        break;

      default:
        console.warn(`[EffectEngine] Unknown effect type: ${name}`);
    }
  }

  executeChain(chainPayload) {
    const effects = chainPayload.effects || [];
    effects.forEach((eff) => {
      this.enqueue(eff, eff.priority || 'normal');
    });
  }

  stopAll() {
    this.queue = [];
    this.isProcessingQueue = false;
    this.fade.trigger({ target_opacity: 0.0, duration_ms: 300 });
    this.bsod.hide();
    this.tts.stop();
    this.ambient.setMood('silence', 1.0);
  }
}

// Instantiate on load
document.addEventListener('DOMContentLoaded', () => {
  window.effectEngine = new MasterEffectEngine();
  console.log('[SENTIENT_OS v2] Master Effect Engine initialized.');
});
