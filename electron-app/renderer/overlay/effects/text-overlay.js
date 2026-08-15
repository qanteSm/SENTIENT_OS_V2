/**
 * SENTIENT_OS v2 — Text Overlay Effect Module
 */

class TextOverlayEffect {
  constructor(container) {
    this.container = container || document.getElementById('text-overlay-layer');
  }

  trigger(params = {}) {
    const text = params.text || '';
    if (!text) return;

    const style = params.style || 'ghostly';
    const animation = params.animation || (style === 'glitched' ? 'glitch_in' : 'fade_in_out');
    const durationMs = params.duration_ms || 4000;
    const position = params.position || 'center';

    const textElem = document.createElement('div');
    textElem.className = `overlay-text-item style-${style} anim-${animation} pos-${position}`;
    textElem.style.animationDuration = `${durationMs}ms`;

    if (animation === 'typewriter') {
      this.container.appendChild(textElem);
      this.typewrite(textElem, text, durationMs);
    } else {
      textElem.textContent = text;
      this.container.appendChild(textElem);

      setTimeout(() => {
        textElem.classList.add('fade-out');
        setTimeout(() => textElem.remove(), 800);
      }, durationMs - 800);
    }
  }

  typewrite(element, text, totalDurationMs) {
    let index = 0;
    const charDelay = Math.max(20, Math.min(100, Math.floor(totalDurationMs / (text.length * 2))));

    const interval = setInterval(() => {
      if (index < text.length) {
        element.textContent += text[index];
        index++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          element.classList.add('fade-out');
          setTimeout(() => element.remove(), 800);
        }, totalDurationMs / 2);
      }
    }, charDelay);
  }
}

window.TextOverlayEffect = TextOverlayEffect;
