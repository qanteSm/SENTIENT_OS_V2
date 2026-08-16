const COMMAND_SUGGESTIONS = [
  { cmd: '/dossier', desc: 'Dr. Evelyn Aris vaka dosyasını & delilleri aç', hint: '' },
  { cmd: '/decrypt', desc: 'Masaüstü dosyasındaki şifreyi çöz', hint: ' <KOD> (Örn: /decrypt 0x1A_MEM)' },
  { cmd: '/trial', desc: 'Güvenlik sektörü minigame sınavını başlat', hint: ' [1-5] (Örn: /trial 1)' },
  { cmd: '/cctv', desc: 'Güvenlik kameralarını canlı izle & anomali yakala', hint: '' },
  { cmd: '/scan', desc: 'Masaüstü ve CCTV tehditlerini tara', hint: '' },
  { cmd: '/status', desc: 'Sektör ilerlemesi ve çekirdek durumunu raporla', hint: '' },
  { cmd: '/logs', desc: 'Ele geçirilen Black-Site ses ve veri kayıtları', hint: '' },
  { cmd: '/override', desc: 'ARG güvenlik baypas anahtarını gir', hint: ' <ANAHTAR>' },
  { cmd: '/hack', desc: 'Sıradaki hedef için taktiksel ipucu al', hint: '' },
  { cmd: '/help', desc: 'Tüm komutların listesini ve kullanımını göster', hint: '' },
];

class ChatManager {
  constructor() {
    this.messagesContainer = document.getElementById('chat-messages');
    this.input = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('chat-send-btn');
    this.closeBtn = document.getElementById('btn-close');
    this.typingIndicator = document.getElementById('typing-indicator');
    this.autocompleteBox = document.getElementById('cmd-autocomplete');
    this.typewriter = new TypewriterAnimator();
    this.selectedAutoIdx = -1;

    this.initEvents();
  }

  initEvents() {
    this.sendBtn.addEventListener('click', () => this.handleSend());
    this.input.addEventListener('keydown', (e) => {
      if (this.autocompleteBox && this.autocompleteBox.style.display === 'flex') {
        const items = this.autocompleteBox.querySelectorAll('.cmd-autocomplete-item');
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.selectedAutoIdx = (this.selectedAutoIdx + 1) % items.length;
          this.updateAutoHighlight(items);
          return;
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.selectedAutoIdx = (this.selectedAutoIdx - 1 + items.length) % items.length;
          this.updateAutoHighlight(items);
          return;
        } else if (e.key === 'Enter' || e.key === 'Tab') {
          if (this.selectedAutoIdx >= 0 && items[this.selectedAutoIdx]) {
            e.preventDefault();
            items[this.selectedAutoIdx].click();
            return;
          }
        } else if (e.key === 'Escape') {
          this.hideAutocomplete();
          return;
        }
      }

      if (e.key === 'Enter') {
        this.handleSend();
      }
    });

    // Autocomplete input listener
    this.input.addEventListener('input', () => {
      this.handleAutocompleteInput();
    });

    document.addEventListener('click', (e) => {
      if (!this.input.contains(e.target) && !this.autocompleteBox.contains(e.target)) {
        this.hideAutocomplete();
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

  handleAutocompleteInput() {
    const val = this.input.value.trimStart();
    if (!val.startsWith('/')) {
      this.hideAutocomplete();
      return;
    }

    const search = val.toLowerCase();
    const matches = COMMAND_SUGGESTIONS.filter((c) => c.cmd.startsWith(search) || search === '/');

    if (matches.length === 0) {
      this.hideAutocomplete();
      return;
    }

    this.selectedAutoIdx = 0;
    this.autocompleteBox.innerHTML = '';
    matches.forEach((m, idx) => {
      const item = document.createElement('div');
      item.className = `cmd-autocomplete-item ${idx === 0 ? 'active' : ''}`;
      item.innerHTML = `
        <span class="cmd-auto-tag">${m.cmd}</span>
        <span class="cmd-auto-hint">${m.hint}</span>
        <span class="cmd-auto-desc">${m.desc}</span>
      `;
      item.addEventListener('click', () => {
        if (m.hint.includes('<')) {
          this.input.value = `${m.cmd} `;
        } else {
          this.input.value = m.cmd;
        }
        this.input.focus();
        this.hideAutocomplete();
      });
      this.autocompleteBox.appendChild(item);
    });

    this.autocompleteBox.style.display = 'flex';
  }

  updateAutoHighlight(items) {
    items.forEach((it, idx) => {
      if (idx === this.selectedAutoIdx) {
        it.classList.add('active');
        it.scrollIntoView({ block: 'nearest' });
      } else {
        it.classList.remove('active');
      }
    });
  }

  hideAutocomplete() {
    if (this.autocompleteBox) {
      this.autocompleteBox.style.display = 'none';
      this.selectedAutoIdx = -1;
    }
  }

  handleSend() {
    this.hideAutocomplete();
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

    if (text.includes('DEŞİFRE EDİLDİ') || text.includes('mühürlendi') || text.includes('BAŞARILI')) {
      bubble.classList.add('decrypt-success-pulse');
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
