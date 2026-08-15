/**
 * SENTIENT_OS v2 — Fake Windows Toast Notification Module
 */

class FakeNotificationEffect {
  constructor() {
    this.container = document.getElementById('notification-container');
  }

  trigger(params = {}) {
    const title = params.title || 'Sistem Bildirimi';
    const body = params.body || '';
    const durationMs = params.duration_ms || 4000;

    if (!this.container) return;

    const toast = document.createElement('div');
    toast.className = 'fake-toast-item';
    toast.innerHTML = `
      <div class="toast-header">
        <span class="toast-app-icon">⚠️</span>
        <span class="toast-app-name">Windows Güvenliği</span>
        <span class="toast-time">Şimdi</span>
      </div>
      <div class="toast-body">
        <div class="toast-title">${this.escapeHtml(title)}</div>
        <div class="toast-desc">${this.escapeHtml(body)}</div>
      </div>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('slide-out');
      setTimeout(() => toast.remove(), 400);
    }, durationMs);
  }

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

window.FakeNotificationEffect = FakeNotificationEffect;
