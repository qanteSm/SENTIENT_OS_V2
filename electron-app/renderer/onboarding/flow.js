/**
 * SENTIENT_OS v2 — Onboarding Wizard Controller
 */

class OnboardingFlow {
  constructor() {
    this.currentStep = 1;
    this.selectedIntensity = 'medium';
    this.selectedLanguage = 'tr';

    this.initElements();
    this.bindEvents();
  }

  initElements() {
    this.step1 = document.getElementById('step-1');
    this.step2 = document.getElementById('step-2');
    this.step3 = document.getElementById('step-3');

    this.btnStart = document.getElementById('btn-start');
    this.btnConsentNext = document.getElementById('btn-consent-next');
    this.btnExit = document.getElementById('btn-exit');
    this.chkConsent = document.getElementById('chk-consent');

    this.intensityCards = document.querySelectorAll('.intensity-card');
    this.btnLangTr = document.getElementById('lang-tr');
    this.btnLangEn = document.getElementById('lang-en');
    this.btnLaunch = document.getElementById('btn-launch');
  }

  bindEvents() {
    // Step 1 -> Step 2
    this.btnStart.addEventListener('click', () => this.goToStep(2));

    // Step 2: Checkbox enables Next
    this.chkConsent.addEventListener('change', () => {
      this.btnConsentNext.disabled = !this.chkConsent.checked;
    });

    this.btnConsentNext.addEventListener('click', () => this.goToStep(3));

    this.btnExit.addEventListener('click', () => {
      if (window.sentientAPI && window.sentientAPI.sendEvent) {
        window.sentientAPI.sendEvent('app-exit', {});
      }
    });

    // Step 3: Intensity Selection
    this.intensityCards.forEach((card) => {
      card.addEventListener('click', () => {
        this.intensityCards.forEach((c) => c.classList.remove('selected'));
        card.classList.add('selected');
        this.selectedIntensity = card.getAttribute('data-val');
      });
    });

    // Language Selection
    this.btnLangTr.addEventListener('click', () => {
      this.btnLangTr.classList.add('active');
      this.btnLangEn.classList.remove('active');
      this.selectedLanguage = 'tr';
    });

    this.btnLangEn.addEventListener('click', () => {
      this.btnLangEn.classList.add('active');
      this.btnLangTr.classList.remove('active');
      this.selectedLanguage = 'en';
    });

    // Launch Final Game
    this.btnLaunch.addEventListener('click', () => {
      if (window.sentientAPI && window.sentientAPI.sendEvent) {
        window.sentientAPI.sendEvent('onboarding-complete', {
          intensity: this.selectedIntensity,
          language: this.selectedLanguage,
        });
      }
    });
  }

  goToStep(stepNumber) {
    this.step1.classList.remove('active');
    this.step2.classList.remove('active');
    this.step3.classList.remove('active');

    if (stepNumber === 1) this.step1.classList.add('active');
    if (stepNumber === 2) this.step2.classList.add('active');
    if (stepNumber === 3) this.step3.classList.add('active');

    this.currentStep = stepNumber;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.onboardingFlow = new OnboardingFlow();
});
