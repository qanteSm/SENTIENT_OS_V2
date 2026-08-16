/**
 * SENTIENT_OS v2 — Chat Controller & IPC Communication
 */

class ChatManager {
  constructor() {
    this.messagesContainer = document.getElementById('chat-messages');
    this.input = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('chat-send-btn');
    this.closeBtn = document.getElementById('btn-close');
    this.typingIndicator = document.getElementById('typing-indicator');
    this.typewriter = new TypewriterAnimator();

    this.initEvents();
  }

  initEvents() {
    this.sendBtn.addEventListener('click', () => this.handleSend());
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.handleSend();
      }
    });

    // Quick Command Chips
    document.querySelectorAll('.cmd-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        const cmd = chip.dataset.cmd;
        if (cmd) {
          this.input.value = cmd;
          this.handleSend();
        }
      });
    });

    // Close button intercept — does not close, reports to AI
    this.closeBtn.addEventListener('click', () => {
      if (window.sentientAPI && window.sentientAPI.sendEvent) {
        window.sentientAPI.sendEvent('system-event', {
          event: 'chat_close_attempt',
          data: { timestamp: Date.now() },
        });
      }
    });

    // IPC message listener
    if (window.sentientAPI && window.sentientAPI.onMessage) {
      window.sentientAPI.onMessage((msg) => {
        this.handleIncomingMessage(msg);
      });
    }
  }

  handleSend() {
    const text = this.input.value.trim();
    if (!text) return;

    this.addUserMessage(text);
    this.input.value = '';
    this.showTypingIndicator();

    if (window.sentientAPI && window.sentientAPI.sendEvent) {
      window.sentientAPI.sendEvent('user-chat', { text });
    }
  }

  handleIncomingMessage(msg) {
    if (!msg || !msg.type) return;

    if (msg.type === 'ai_response') {
      const p = msg.payload || {};
      this.hideTypingIndicator();
      this.addAIMessage(p.speech || '', p.emotion || 'curious', p.actions || []);
    } else if (msg.type === 'ui_command') {
      const p = msg.payload || {};
      if (p.command === 'change_chat_theme') {
        this.changeTheme(p.params?.theme || 'normal');
      } else if (p.command === 'open_chat' && p.params?.initial_messages) {
        p.params.initial_messages.forEach((m, idx) => {
          setTimeout(() => {
            this.addAIMessage(m.content, 'curious');
          }, m.delay_ms || idx * 1500);
        });
      }
    }
  }

  addUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user';
    row.innerHTML = `
      <span class="msg-sender">SEN</span>
      <div class="msg-bubble">${this.escapeHtml(text)}</div>
    `;
    this.messagesContainer.appendChild(row);
    this.scrollToBottom();
  }

  addAIMessage(text, emotion = 'curious', actions = []) {
    const row = document.createElement('div');
    row.className = 'msg-row ai';
    const sender = document.createElement('span');
    sender.className = 'msg-sender';
    sender.textContent = `SENTIENT [${emotion.toUpperCase()}]`;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    row.appendChild(sender);
    row.appendChild(bubble);
    this.messagesContainer.appendChild(row);
    this.scrollToBottom();

    if (text.includes('başardın') || text.includes('Başarısız') || text.includes('sınavını') || text.includes('İnanılmaz')) {
      this.markPreviousActionCardsCompleted();
    }

    // Dynamically react with theme shifts and window tension
    if (emotion === 'angry') {
      this.changeTheme('bloody');
      document.body.classList.add('chat-rage-shake');
      setTimeout(() => document.body.classList.remove('chat-rage-shake'), 600);
    } else if (emotion === 'sinister') {
      this.changeTheme('terminal');
    } else if (emotion === 'hurt') {
      this.changeTheme('glitched');
    }

    this.typewriter.animate(bubble, text, emotion, () => {
      // Check if message contains trial invitation or action cards
      this.attachActionCardsIfNeeded(bubble, text, actions);
      this.scrollToBottom();
    });
  }

  attachActionCardsIfNeeded(bubble, text, actions) {
    // Never attach cards to victory or failure outcome reports
    if (text.includes('başardın') || text.includes('Başarısız') || text.includes('Şifreli Log')) {
      return;
    }

    let targetGame = null;
    let trialTitle = 'SİSTEM SINAVINI BAŞLAT';

    // Only check explicit actions from director
    if (Array.isArray(actions)) {
      for (const act of actions) {
        if (act.type === 'trigger_trial' && act.params?.game) {
          targetGame = act.params.game;
          trialTitle = act.params.title || '🚨 ACİL DURUM SINAVI';
          break;
        }
      }
    }

    if (targetGame) {
      const card = document.createElement('div');
      card.className = 'action-card';
      card.innerHTML = `
        <div class="action-card-header">SİSTEM TEHLİKE PROTOKOLÜ</div>
        <button class="action-card-btn">▶ ${trialTitle}</button>
      `;
      const btn = card.querySelector('.action-card-btn');
      btn.addEventListener('click', () => {
        btn.disabled = true;
        btn.textContent = '⌛ BAĞLANTI KURULUYOR...';
        btn.style.animation = 'none';
        btn.style.background = '#2a3a4a';
        btn.style.boxShadow = 'none';
        btn.style.cursor = 'default';
        if (window.sentientAPI && window.sentientAPI.sendEvent) {
          window.sentientAPI.sendEvent('launch-minigame', targetGame);
        }
      });
      bubble.appendChild(card);
    }
  }

  markPreviousActionCardsCompleted() {
    document.querySelectorAll('.action-card-btn:not([disabled])').forEach((btn) => {
      btn.disabled = true;
      btn.textContent = '✅ PROTOKOL TAMAMLANDI';
      btn.style.animation = 'none';
      btn.style.background = 'rgba(0, 255, 128, 0.2)';
      btn.style.borderColor = '#00ff88';
      btn.style.color = '#00ff88';
      btn.style.boxShadow = 'none';
      btn.style.cursor = 'default';
    });
  }

  showTypingIndicator() {
    if (this.typingIndicator) {
      this.typingIndicator.style.display = 'flex';
      this.scrollToBottom();
    }
  }

  hideTypingIndicator() {
    if (this.typingIndicator) {
      this.typingIndicator.style.display = 'none';
    }
  }

  changeTheme(themeName) {
    document.body.className = `theme-${themeName}`;
    console.log(`[ChatManager] Chat theme switched to: ${themeName}`);
  }

  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.chatManager = new ChatManager();
});
