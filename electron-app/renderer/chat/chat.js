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
      this.addAIMessage(p.speech || '', p.emotion || 'curious');
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

  addAIMessage(text, emotion = 'curious') {
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
      this.scrollToBottom();
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
