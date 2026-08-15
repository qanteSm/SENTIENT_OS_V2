/**
 * SENTIENT_OS v2 — TTS Audio Player with Ambient Ducking
 */

class TTSPlayer {
  constructor(ambientEngine) {
    this.ambientEngine = ambientEngine;
    this.currentAudio = null;
  }

  playAudioFile(filePath, onEndedCallback) {
    if (!filePath) return;

    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    const audioUrl = filePath.startsWith('http') || filePath.startsWith('file://')
      ? filePath
      : `file://${filePath.replace(/\\/g, '/')}`;

    this.currentAudio = new Audio(audioUrl);

    // Duck ambient volume
    if (this.ambientEngine) {
      this.ambientEngine.setVolumeDucking(0.3, 0.3);
    }

    this.currentAudio.onended = () => {
      this.currentAudio = null;
      if (this.ambientEngine) {
        this.ambientEngine.restoreVolume(0.5);
      }
      if (onEndedCallback) onEndedCallback();
    };

    this.currentAudio.onerror = (e) => {
      console.warn('[TTSPlayer] Failed to play TTS audio file:', e);
      if (this.ambientEngine) {
        this.ambientEngine.restoreVolume(0.2);
      }
      if (onEndedCallback) onEndedCallback();
    };

    this.currentAudio.play().catch((err) => {
      console.warn('[TTSPlayer] Playback was prevented or failed:', err);
      if (this.ambientEngine) this.ambientEngine.restoreVolume(0.1);
      if (onEndedCallback) onEndedCallback();
    });
  }

  stop() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if (this.ambientEngine) {
      this.ambientEngine.restoreVolume(0.2);
    }
  }
}

window.TTSPlayer = TTSPlayer;
