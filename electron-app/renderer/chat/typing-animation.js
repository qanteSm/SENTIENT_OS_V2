/**
 * SENTIENT_OS v2 — Chat Typewriter Animation
 */

class TypewriterAnimator {
  constructor() {
    this.speedMap = {
      excited: 20,
      angry: 15,
      curious: 30,
      sinister: 35,
      calm: 40,
      hurt: 45,
      sad: 50,
    };
  }

  animate(element, text, emotion = 'curious', onComplete) {
    let index = 0;
    const baseSpeed = this.speedMap[emotion] || 35;
    element.textContent = '';

    const typeNext = () => {
      if (index < text.length) {
        const char = text[index];
        element.textContent += char;
        index++;

        // Add pause after punctuation for horror pacing
        let delay = baseSpeed;
        if (['.', '!', '?'].includes(char)) {
          delay += 250;
        } else if ([',', ';', ':', '—'].includes(char)) {
          delay += 120;
        }

        setTimeout(typeNext, delay);
      } else {
        if (onComplete) onComplete();
      }
    };

    typeNext();
  }
}

window.TypewriterAnimator = TypewriterAnimator;
