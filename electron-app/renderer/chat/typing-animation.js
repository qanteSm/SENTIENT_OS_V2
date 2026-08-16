/**
 * SENTIENT_OS v2 — Ultra-Fast Responsive Typewriter Animation
 */

class TypewriterAnimator {
  constructor() {
    // High-speed responsiveness (5-10ms range instead of sluggish 40-50ms)
    this.speedMap = {
      excited: 4,
      angry: 5,
      curious: 6,
      sinister: 8,
      calm: 7,
      hurt: 8,
      sad: 9,
    };
  }

  animate(element, text, emotion = 'curious', onComplete) {
    if (!text) {
      element.textContent = '';
      if (onComplete) onComplete();
      return;
    }

    // If text is a system/status report or command output, render with chunk streaming
    const isSystemReport = (
      text.startsWith('🔍') ||
      text.startsWith('📊') ||
      text.startsWith('💡') ||
      text.startsWith('ℹ️') ||
      text.startsWith('===') ||
      text.startsWith('🚨') ||
      text.startsWith('🟢') ||
      text.startsWith('[')
    );

    if (isSystemReport) {
      let index = 0;
      element.textContent = '';
      const chunkSize = 8;

      const typeFast = () => {
        if (index < text.length) {
          element.textContent += text.slice(index, index + chunkSize);
          index += chunkSize;
          setTimeout(typeFast, 4);
        } else {
          element.textContent = text;
          if (onComplete) onComplete();
        }
      };
      typeFast();
      return;
    }

    let index = 0;
    const baseSpeed = this.speedMap[emotion] || 6;
    element.textContent = '';
    let isCancelled = false;

    // Click anywhere on the bubble to instantly finish writing without waiting
    const skipHandler = () => {
      if (!isCancelled) {
        isCancelled = true;
        element.textContent = text;
        element.removeEventListener('click', skipHandler);
        if (onComplete) onComplete();
      }
    };
    element.addEventListener('click', skipHandler);

    const typeNext = () => {
      if (isCancelled) return;

      if (index < text.length) {
        // Stream 2 characters per frame for longer messages to eliminate sluggishness
        const step = text.length > 80 ? 2 : 1;
        const slice = text.slice(index, index + step);
        element.textContent += slice;
        index += step;

        const lastChar = slice[slice.length - 1];
        let delay = baseSpeed;
        if (['.', '!', '?'].includes(lastChar)) {
          delay += 35; // Crisp, subtle pause
        } else if ([',', ';', ':'].includes(lastChar)) {
          delay += 15;
        }

        setTimeout(typeNext, delay);
      } else {
        element.removeEventListener('click', skipHandler);
        if (onComplete) onComplete();
      }
    };

    typeNext();
  }
}

window.TypewriterAnimator = TypewriterAnimator;
