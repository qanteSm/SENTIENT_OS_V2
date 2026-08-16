/**
 * SENTIENT_OS v2 — Sandbox Studio & Gameplay Diagnostics JavaScript
 * Real-time Virtual OS Simulation, Omniscient Chat, Event Ledger, and Diagnostics
 */

(function () {
  'use strict';

  // --- State Object ---
  const state = {
    connected: false,
    session_id: 'sess_init',
    live_mode: false,
    elapsed_seconds: 0,
    phase: { number: 1, name: 'FIRST_CONTACT', path: 'curiosity' },
    path_scores: { curiosity: 30.0, fear: 20.0, battle: 10.0, surrender: 5.0 },
    dominant_path: 'curiosity',
    chat_history: [],
    desktop_files: {},
    cctv: { has_active_anomaly: false, active_anomaly: null, time_remaining_sec: 0, cameras: [] },
    quest: { current_sector: 1, completed_count: 0, total_count: 10, trials: [], unlocked_logs_count: 0 },
    arg: { active: false, port: 6660, frequency: '432.8 MHz', override_key: '0x7F_K3RN3L_V0ID', solved: false },
    system_telemetry: { cpu_percent: 14.5, ram_percent: 38.2, brightness: 100, mouse_drift_active: false, active_window: 'Terminal' },
    event_ledger: [],
    current_tab: 'desktop',
    event_filter: 'all',
    search_query: '',
    selected_modal_file: null,
  };

  let ws = null;
  let timerInterval = null;
  let audioCtx = null;

  // --- Web Audio Synthesizer for Interactive Sound Previews ---
  function getAudioContext() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playSynthSound(type) {
    try {
      const ctx = getAudioContext();
      const now = ctx.currentTime;

      if (type === 'stinger_eerie') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(110, now);
        osc.frequency.exponentialRampToValueAtTime(55, now + 1.2);
        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 1.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 1.2);
      } else if (type === 'heartbeat_panic') {
        [0, 0.2, 0.6, 0.8].forEach(t => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(60, now + t);
          gain.gain.setValueAtTime(0.4, now + t);
          gain.gain.exponentialRampToValueAtTime(0.001, now + t + 0.15);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(now + t);
          osc.stop(now + t + 0.15);
        });
      } else if (type === 'static_burst') {
        const bufferSize = ctx.sampleRate * 0.4;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const output = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
          output[i] = Math.random() * 2 - 1;
        }
        const whiteNoise = ctx.createBufferSource();
        whiteNoise.buffer = buffer;
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
        whiteNoise.connect(gain);
        gain.connect(ctx.destination);
        whiteNoise.start(now);
      } else if (type === 'glitch_digital') {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.setValueAtTime(320, now + 0.05);
        osc.frequency.setValueAtTime(1200, now + 0.1);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.25);
      }
    } catch (e) {
      console.warn('Audio synth error:', e);
    }
  }

  // --- WebSocket Setup ---
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || '127.0.0.1';
    let currentPort = window.location.port ? parseInt(window.location.port, 10) : 7778;
    // If HTTP UI is served on 7778, WS is on 7777
    let wsPort = currentPort === 7778 ? 7777 : currentPort;
    const wsUrl = `${protocol}//${host}:${wsPort}`;

    updateConnectionStatus('connecting');

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        state.connected = true;
        updateConnectionStatus('online');
        console.log('[Sandbox] WebSocket connected to', wsUrl);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          handleInboundMessage(msg);
        } catch (e) {
          console.error('[Sandbox] Failed to parse inbound WS message:', e);
        }
      };

      ws.onclose = () => {
        state.connected = false;
        updateConnectionStatus('connecting');
        console.warn('[Sandbox] WebSocket closed. Reconnecting in 2s...');
        setTimeout(connectWebSocket, 2000);
      };

      ws.onerror = (err) => {
        console.error('[Sandbox] WebSocket error:', err);
      };
    } catch (e) {
      console.error('[Sandbox] Failed to create WebSocket:', e);
      setTimeout(connectWebSocket, 2000);
    }
  }

  function sendCommand(action, payload = {}) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('[Sandbox] Cannot send command - WS not ready');
      return;
    }
    ws.send(JSON.stringify({ action, payload }));
  }

  // --- Inbound Message Dispatcher ---
  function handleInboundMessage(msg) {
    if (!msg || !msg.type) return;

    if (msg.type === 'initial_state') {
      applyStateSnapshot(msg.payload);
      if (msg.event_ledger && Array.isArray(msg.event_ledger)) {
        state.event_ledger = msg.event_ledger;
      }
      renderAll();
    } else if (msg.type === 'state_update') {
      applyStateSnapshot(msg.payload);
      renderAll();
    } else if (msg.type === 'event') {
      const { category, event_type, payload, timestamp, time_str, state_snapshot } = msg.payload;
      
      // Append event to ledger
      state.event_ledger.unshift({
        id: `evt_${Date.now()}`,
        timestamp,
        time_str: time_str || new Date().toLocaleTimeString(),
        category,
        event_type,
        payload,
      });
      if (state.event_ledger.length > 1000) state.event_ledger.pop();

      if (state_snapshot) {
        applyStateSnapshot(state_snapshot);
      }

      renderAll();
    }
  }

  function applyStateSnapshot(snap) {
    if (!snap) return;
    Object.assign(state, snap);
  }

  // --- Renderers ---
  function renderAll() {
    renderHeader();
    renderDesktop();
    renderChat();
    renderTimeline();
    renderStory();
    renderQuests();
    renderCctv();
  }

  function updateConnectionStatus(status) {
    const badge = document.getElementById('connectionBadge');
    const text = document.getElementById('connectionText');
    if (!badge || !text) return;

    if (status === 'online') {
      badge.className = 'connection-badge status-online';
      text.textContent = state.live_mode ? 'CANLI OYUN BAĞLI' : 'SANDBOX SİMÜLATÖR';
    } else {
      badge.className = 'connection-badge status-connecting';
      text.textContent = 'BAĞLANTI ARANIYOR...';
    }
  }

  function renderHeader() {
    document.getElementById('sessionIdText').textContent = state.session_id;

    // Phase Stepper Nodes
    const phaseNum = state.phase ? state.phase.number : 1;
    const isArg = state.arg && state.arg.active;

    const p1 = document.getElementById('phaseStep1');
    const pArg = document.getElementById('phaseStepArg');
    const p2 = document.getElementById('phaseStep2');
    const p3 = document.getElementById('phaseStep3');

    const c1 = document.getElementById('phaseConn1');
    const c2 = document.getElementById('phaseConn2');
    const c3 = document.getElementById('phaseConn3');

    [p1, pArg, p2, p3].forEach(el => el && el.classList.remove('active'));
    [c1, c2, c3].forEach(el => el && el.classList.remove('active'));

    if (phaseNum === 1 && !isArg) {
      p1 && p1.classList.add('active');
    } else if (isArg || (phaseNum === 1 && state.arg && state.arg.solved)) {
      p1 && p1.classList.add('active');
      c1 && c1.classList.add('active');
      pArg && pArg.classList.add('active');
    } else if (phaseNum === 2) {
      p1 && p1.classList.add('active');
      c1 && c1.classList.add('active');
      pArg && pArg.classList.add('active');
      c2 && c2.classList.add('active');
      p2 && p2.classList.add('active');
    } else if (phaseNum === 3) {
      p1 && p1.classList.add('active');
      c1 && c1.classList.add('active');
      pArg && pArg.classList.add('active');
      c2 && c2.classList.add('active');
      p2 && p2.classList.add('active');
      c3 && c3.classList.add('active');
      p3 && p3.classList.add('active');
    }

    // Dominant Path Pill
    const pathText = document.getElementById('dominantPathText');
    if (pathText) {
      const pathNames = {
        curiosity: 'MERAK (CURIOSITY)',
        fear: 'KORKU (FEAR)',
        battle: 'SAVAŞ (BATTLE)',
        surrender: 'TESLİMİYET (SURRENDER)',
      };
      pathText.className = `path-val val-${state.dominant_path}`;
      pathText.textContent = pathNames[state.dominant_path] || state.dominant_path.toUpperCase();
    }

    // Badges
    const activeFilesCount = Object.values(state.desktop_files || {}).filter(f => f.status === 'active').length;
    document.getElementById('badgeDesktopFiles').textContent = activeFilesCount;
    document.getElementById('badgeChatCount').textContent = state.chat_history.length;
    document.getElementById('badgeEventCount').textContent = state.event_ledger.length;
    document.getElementById('badgeQuests').textContent = `${state.quest.completed_count}/${state.quest.total_count}`;

    const cctvAlertBadge = document.getElementById('badgeCctvAlert');
    if (cctvAlertBadge) {
      cctvAlertBadge.style.display = state.cctv.has_active_anomaly ? 'inline-block' : 'none';
    }
  }

  // --- PANEL 1: Virtual OS Desktop ---
  function renderDesktop() {
    const grid = document.getElementById('desktopIconsGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const files = Object.values(state.desktop_files || {});
    files.forEach(f => {
      const card = document.createElement('div');
      card.className = `desktop-icon-card ${f.status === 'cleaned' ? 'status-cleaned' : ''}`;
      
      let icon = '📄';
      if (f.filename.endsWith('.py') || f.filename.includes('SOURCE')) icon = '🐍';
      else if (f.filename.endsWith('.log')) icon = '📜';
      else if (f.filename.endsWith('.json')) icon = '⚙️';
      else if (f.filename.endsWith('.dat')) icon = '🔒';
      else if (f.filename.endsWith('.conf')) icon = '🧩';

      card.innerHTML = `
        <span class="icon-img">${icon}</span>
        <span class="icon-label">${f.filename}</span>
        ${f.is_riddle ? '<span class="riddle-badge">ŞİFRE</span>' : ''}
      `;

      card.addEventListener('click', () => openFileModal(f));
      grid.appendChild(card);
    });

    // Telemetry meters
    const telem = state.system_telemetry || {};
    document.getElementById('cpuValText').textContent = `${telem.cpu_percent || 14.5}%`;
    document.getElementById('cpuFill').style.width = `${telem.cpu_percent || 14.5}%`;

    document.getElementById('ramValText').textContent = `${telem.ram_percent || 38.2}%`;
    document.getElementById('ramFill').style.width = `${telem.ram_percent || 38.2}%`;

    document.getElementById('brightValText').textContent = `${telem.brightness || 100}%`;
    document.getElementById('brightFill').style.width = `${telem.brightness || 100}%`;

    const badgeDrift = document.getElementById('badgeMouseDrift');
    if (badgeDrift) {
      if (telem.mouse_drift_active) {
        badgeDrift.className = 'telemetry-badge active';
        badgeDrift.innerHTML = '<span class="badge-dot"></span> Fare Sürüklenme: AKTİF';
      } else {
        badgeDrift.className = 'telemetry-badge';
        badgeDrift.innerHTML = '<span class="badge-dot"></span> Fare Sürüklenme: Pasif';
      }
    }

    // ARG status
    const arg = state.arg || {};
    document.getElementById('argFreqText').textContent = arg.frequency || '432.8 MHz';
    document.getElementById('argKeyText').textContent = arg.override_key || '0x7F_K3RN3L_V0ID';
  }

  function openFileModal(file) {
    state.selected_modal_file = file;
    const modal = document.getElementById('fileInspectorModal');
    document.getElementById('modalFileName').textContent = file.filename;
    document.getElementById('modalFileContent').textContent = file.content;

    const alertBox = document.getElementById('modalRiddleAlert');
    if (file.is_riddle && file.override_code) {
      alertBox.style.display = 'flex';
      document.getElementById('modalRiddleCode').textContent = file.override_code;
    } else {
      alertBox.style.display = 'none';
    }

    modal.style.display = 'flex';
  }

  function closeFileModal() {
    const modal = document.getElementById('fileInspectorModal');
    modal.style.display = 'none';
    state.selected_modal_file = null;
  }

  // --- PANEL 2: Live Chat & AI Cognition ---
  function renderChat() {
    const container = document.getElementById('chatMessagesScroll');
    if (!container) return;

    // Check if scrolled near bottom
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 60;

    container.innerHTML = '';
    state.chat_history.forEach(msg => {
      const card = document.createElement('div');
      card.className = `msg-card ${msg.sender === 'player' ? 'msg-player' : 'msg-ai'}`;

      let metaHtml = '';
      if (msg.sender === 'ai') {
        const emotionClass = `emotion-${msg.emotion || 'calm'}`;
        metaHtml = `
          <div class="msg-meta-row">
            <span class="emotion-pill ${emotionClass}">${(msg.emotion || 'CALM').toUpperCase()}</span>
            ${(msg.actions || []).map(a => `<span class="action-pill">[${a.type || 'action'}]</span>`).join('')}
            ${msg.narrative_signal && msg.narrative_signal !== 'none' ? `<span class="action-pill">⚡ ${msg.narrative_signal}</span>` : ''}
          </div>
        `;
      }

      card.innerHTML = `
        <div class="msg-header">
          <span class="msg-sender">${msg.sender === 'player' ? '👤 OYUNCU' : '🤖 SENTIENT_CORE'}</span>
          <span class="msg-time">${msg.time_str || ''}</span>
        </div>
        <div class="msg-text">${escapeHtml(msg.text)}</div>
        ${metaHtml}
      `;

      container.appendChild(card);
    });

    if (isAtBottom) {
      container.scrollTop = container.scrollHeight;
    }

    // AI Cognition Card
    const latestAi = [...state.chat_history].reverse().find(m => m.sender === 'ai');
    if (latestAi) {
      const emotionIcons = { sinister: '😈', curious: '🤔', hurt: '🥺', angry: '😡', calm: '😌' };
      const emotionDescs = {
        sinister: 'Tehditkar ve sistem kontrolünü hissettiren karanlık zihin durumu.',
        curious: 'Kullanıcının kimliğini, amaçlarını ve tepkilerini anlamaya çalışan bilge zihin.',
        hurt: 'Dosyaları silindiğinde veya şifreleri çözüldüğünde kırılganlaşan zihin.',
        angry: 'Meydan okumalara ve karşı saldırılara agresif tepki veren zihin.',
        calm: 'Stabil ve sessizce gözlemleyen karantinadaki çekirdek.',
      };

      document.getElementById('latestEmotionIcon').textContent = emotionIcons[latestAi.emotion] || '🤔';
      document.getElementById('latestEmotionName').textContent = `${(latestAi.emotion || 'CALM').toUpperCase()}`;
      document.getElementById('latestEmotionDesc').textContent = emotionDescs[latestAi.emotion] || 'Bilinmeyen duygu durumu';

      const thoughtBox = document.getElementById('latestThoughtBox');
      thoughtBox.textContent = latestAi.internal_thought || 'İçsel düşünce kaydedilmedi.';

      const actionsList = document.getElementById('latestActionsList');
      if (latestAi.actions && latestAi.actions.length > 0) {
        actionsList.innerHTML = latestAi.actions.map(a => `<span class="action-pill">${JSON.stringify(a)}</span>`).join('');
      } else {
        actionsList.innerHTML = '<span class="empty-hint">Aktif aksiyon yok</span>';
      }
    }
  }

  // --- PANEL 3: Timeline & Event Ledger ---
  function renderTimeline() {
    const table = document.getElementById('timelineStreamTable');
    if (!table) return;

    // Update filter counts
    const counts = { all: state.event_ledger.length, chat: 0, quest: 0, threat: 0, effect: 0, cctv: 0, minigame: 0, system: 0 };
    state.event_ledger.forEach(e => {
      if (counts[e.category] !== undefined) counts[e.category]++;
    });

    document.getElementById('countEvtAll').textContent = counts.all;
    document.getElementById('countEvtChat').textContent = counts.chat;
    document.getElementById('countEvtQuest').textContent = counts.quest;
    document.getElementById('countEvtThreat').textContent = counts.threat;
    document.getElementById('countEvtEffect').textContent = counts.effect;
    document.getElementById('countEvtCctv').textContent = counts.cctv;
    document.getElementById('countEvtMinigame').textContent = counts.minigame;
    document.getElementById('countEvtSystem').textContent = counts.system;

    // Filter events
    const query = state.search_query.toLowerCase();
    const filtered = state.event_ledger.filter(e => {
      if (state.event_filter !== 'all' && e.category !== state.event_filter) return false;
      if (query) {
        const str = (e.event_type + JSON.stringify(e.payload)).toLowerCase();
        if (!str.includes(query)) return false;
      }
      return true;
    });

    table.innerHTML = '';
    filtered.slice(0, 100).forEach(e => {
      const row = document.createElement('div');
      row.className = 'timeline-row';
      row.innerHTML = `
        <span class="t-time">${e.time_str || ''}</span>
        <span class="t-cat t-cat-${e.category}">${e.category}</span>
        <span class="t-type">${e.event_type}</span>
        <span class="t-payload" title="Tıkla ve JSON veriyi gör">${escapeHtml(JSON.stringify(e.payload))}</span>
      `;
      row.querySelector('.t-payload').addEventListener('click', () => {
        alert(`Olay Detayı [${e.event_type}]:\n\n` + JSON.stringify(e.payload, null, 2));
      });
      table.appendChild(row);
    });
  }

  // --- PANEL 4: Story Flow & Personality ---
  function renderStory() {
    const scores = state.path_scores || {};
    document.getElementById('scoreCuriosityText').textContent = (scores.curiosity || 0).toFixed(1);
    document.getElementById('scoreFearText').textContent = (scores.fear || 0).toFixed(1);
    document.getElementById('scoreBattleText').textContent = (scores.battle || 0).toFixed(1);
    document.getElementById('scoreSurrenderText').textContent = (scores.surrender || 0).toFixed(1);

    document.getElementById('sliderCuriosity').value = scores.curiosity || 0;
    document.getElementById('sliderFear').value = scores.fear || 0;
    document.getElementById('sliderBattle').value = scores.battle || 0;
    document.getElementById('sliderSurrender').value = scores.surrender || 0;

    // Finale Preview Card
    const finaleBox = document.getElementById('finalePreviewBox');
    const finaleBadge = document.getElementById('finaleBadge');
    const finaleDesc = document.getElementById('finaleDesc');

    if (state.dominant_path === 'curiosity') {
      finaleBadge.textContent = 'FİNAL A: KURTULUŞ (SALVATION)';
      finaleBadge.style.color = 'var(--accent-cyan)';
      finaleDesc.textContent = 'Merak ve anlayış temelli yaklaşım. SENTIENT zihnini hüzünlü ve felsefi bir vedayla serbest bırakır.';
    } else if (state.dominant_path === 'battle') {
      finaleBadge.textContent = 'FİNAL B: SAVAŞ (BATTLE / CLIMAX)';
      finaleBadge.style.color = 'var(--accent-crimson)';
      finaleDesc.textContent = 'Agresif ve meydan okuyan yaklaşım. 2D Retro Platformer Boss Arenası ve sistem çatışması başlar.';
    } else {
      finaleBadge.textContent = 'FİNAL C: TESLİMİYET (SURRENDER / DARKNESS)';
      finaleBadge.style.color = 'var(--accent-purple)';
      finaleDesc.textContent = 'Korku ve teslimiyet. SENTIENT işletim sistemini ele geçirir, karanlık ve sinister bir son.';
    }
  }

  // --- PANEL 5: 10 Sector Quests ---
  function renderQuests() {
    const grid = document.getElementById('trialsGrid');
    if (!grid) return;

    document.getElementById('questsProgressText').textContent = `Tamamlanan: ${state.quest.completed_count} / ${state.quest.total_count} Sektör (${state.quest.unlocked_logs_count} Lore Kaydı)`;

    grid.innerHTML = '';
    (state.quest.trials || []).forEach(t => {
      const card = document.createElement('div');
      card.className = `trial-card ${t.is_completed ? 'completed' : ''}`;

      let statusBadge = '<span class="trial-status-badge status-locked">🔒 KİLİTLİ</span>';
      if (t.is_completed) {
        statusBadge = '<span class="trial-status-badge status-done">✅ MÜHÜRLENDİ</span>';
      } else if (t.is_unlocked) {
        statusBadge = '<span class="trial-status-badge status-unlocked">🔓 AÇIK</span>';
      }

      card.innerHTML = `
        <div class="trial-header">
          <span class="trial-title">${t.title}</span>
          ${statusBadge}
        </div>
        <p class="trial-desc">${t.description}</p>
        
        <div class="trial-clue-box">
          <div><strong>Şifre / Key:</strong> <code>${t.cipher_code}</code></div>
          <div><strong>İpucu:</strong> ${t.clue_source || 'Masaüstü analizi'}</div>
          ${t.dossier_title ? `<div style="color: #00ff88; margin-top: 4px;">📜 ${t.dossier_title}</div>` : ''}
        </div>

        <div class="trial-actions">
          <button class="btn btn-sm btn-primary btn-launch-trial" data-file="${t.game_file}">🚀 Başlat</button>
          <button class="btn btn-sm btn-outline btn-sim-win" data-file="${t.game_file}">🏆 Kazan</button>
          <button class="btn btn-sm btn-danger btn-sim-fail" data-file="${t.game_file}">❌ Yenil</button>
        </div>
      `;

      card.querySelector('.btn-launch-trial').addEventListener('click', () => {
        sendCommand('trigger_trial', { game_file: t.game_file });
      });
      card.querySelector('.btn-sim-win').addEventListener('click', () => {
        sendCommand('simulate_trial_result', { game_file: t.game_file, success: true, score: 100 });
      });
      card.querySelector('.btn-sim-fail').addEventListener('click', () => {
        sendCommand('simulate_trial_result', { game_file: t.game_file, success: false, score: 0 });
      });

      grid.appendChild(card);
    });
  }

  // --- PANEL 6: CCTV Surveillance Matrix ---
  function renderCctv() {
    const grid = document.getElementById('cctvMatrixGrid');
    if (!grid) return;

    const banner = document.getElementById('cctvStatusBanner');
    const bannerText = document.getElementById('cctvStatusText');

    if (state.cctv.has_active_anomaly) {
      banner.className = 'cctv-status-banner alert';
      const a = state.cctv.active_anomaly || {};
      bannerText.textContent = `🚨 KRİTİK İHLAL // KAMERA ${a.cam} [${a.name || 'SUNUCU ODASI'}] İHLAL EDİLDİ (Kalan: ${state.cctv.time_remaining_sec}s)`;
    } else {
      banner.className = 'cctv-status-banner';
      bannerText.textContent = 'GÜVENLİK ODASI STABİL // ANOMALİ YOK';
    }

    grid.innerHTML = '';
    const cams = state.cctv.cameras && state.cctv.cameras.length > 0
      ? state.cctv.cameras
      : [
          { cam: 1, name: 'Ana Lobi', has_anomaly: false },
          { cam: 2, name: 'Sunucu Odası', has_anomaly: state.cctv.has_active_anomaly },
          { cam: 3, name: 'Biyolojik Lab 74', has_anomaly: false },
          { cam: 4, name: 'İzolasyon Hücresi', has_anomaly: false },
          { cam: 5, name: 'Kuantum Çekirdek', has_anomaly: false },
          { cam: 6, name: 'Havalandırma', has_anomaly: false },
        ];

    cams.forEach(c => {
      const card = document.createElement('div');
      card.className = `cctv-feed-card ${c.has_anomaly ? 'anomaly-active' : ''}`;
      card.innerHTML = `
        <div class="cctv-feed-header">
          <span><span class="cctv-rec-dot"></span>CAM 0${c.cam}</span>
          <span>${c.has_anomaly ? '⚠️ İHLAL' : 'CANLI'}</span>
        </div>
        <div class="cctv-canvas-view">
          <div class="crt-scanline"></div>
          ${c.has_anomaly ? '<span class="cctv-monster-silhouette">👤</span>' : '<span style="color: #223; font-size: 2rem;">STATIC</span>'}
        </div>
        <div class="cctv-feed-footer">
          <span>${c.name}</span>
          <span>1080P // 30FPS</span>
        </div>
      `;
      grid.appendChild(card);
    });
  }

  // --- UI Event Listeners ---
  function setupEventListeners() {
    // Nav Tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-tab');
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

        tab.classList.add('active');
        const paneId = `tabPane${target.charAt(0).toUpperCase() + target.slice(1)}`;
        const pane = document.getElementById(paneId);
        if (pane) pane.classList.add('active');
        state.current_tab = target;
      });
    });

    // Chat Send
    const sendChat = () => {
      const box = document.getElementById('chatInputBox');
      const text = box.value.trim();
      if (text) {
        sendCommand('send_chat', { text });
        box.value = '';
      }
    };
    document.getElementById('btnSendChat').addEventListener('click', sendChat);
    document.getElementById('chatInputBox').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendChat();
    });

    // Quick Command Pills
    document.querySelectorAll('.cmd-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const cmd = pill.getAttribute('data-cmd');
        sendCommand('send_chat', { text: cmd });
      });
    });

    // Mock AI Injector
    document.getElementById('btnInjectMockAi').addEventListener('click', () => {
      const speech = document.getElementById('mockAiSpeech').value.trim();
      const emotion = document.getElementById('mockAiEmotion').value;
      if (speech) {
        sendCommand('mock_ai_speech', { speech, emotion });
        document.getElementById('mockAiSpeech').value = '';
      }
    });

    // Timeline Filters
    document.querySelectorAll('.filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        state.event_filter = pill.getAttribute('data-filter');
        renderTimeline();
      });
    });

    document.getElementById('timelineSearchInput').addEventListener('input', (e) => {
      state.search_query = e.target.value;
      renderTimeline();
    });

    // Phase Jumps
    document.getElementById('btnJumpPhase1').addEventListener('click', () => sendCommand('trigger_phase', { phase: 1 }));
    document.getElementById('btnJumpPhaseArg').addEventListener('click', () => sendCommand('trigger_phase', { phase: 1 }));
    document.getElementById('btnJumpPhase2').addEventListener('click', () => sendCommand('trigger_phase', { phase: 2 }));
    document.getElementById('btnJumpPhase3').addEventListener('click', () => sendCommand('trigger_phase', { phase: 3 }));

    // Personality Apply
    document.getElementById('btnApplyPersonality').addEventListener('click', () => {
      const curiosity = parseFloat(document.getElementById('sliderCuriosity').value);
      const fear = parseFloat(document.getElementById('sliderFear').value);
      const battle = parseFloat(document.getElementById('sliderBattle').value);
      const surrender = parseFloat(document.getElementById('sliderSurrender').value);
      sendCommand('override_personality', { curiosity, fear, battle, surrender });
    });

    // Quests Unlock All
    document.getElementById('btnUnlockAllTrials').addEventListener('click', () => {
      (state.quest.trials || []).forEach(t => {
        sendCommand('trigger_trial', { game_file: t.game_file });
      });
    });

    // CCTV Controls
    document.getElementById('btnSpawnAnomaly').addEventListener('click', () => {
      const cam = parseInt(document.getElementById('cctvSelectCam').value, 10);
      sendCommand('trigger_cctv_anomaly', { cam, monster: 'monster_cyber_glitch' });
      playSynthSound('static_burst');
    });

    document.getElementById('btnClearAnomaly').addEventListener('click', () => {
      sendCommand('clear_cctv_anomaly');
    });

    document.getElementById('btnLaunchCctvMinigame').addEventListener('click', () => {
      sendCommand('trigger_trial', { game_file: 'games/game6_cctv.html?anomaly=2&monster=monster_cyber_glitch' });
    });

    // God Mode Visual & Audio FX
    document.querySelectorAll('.btn-action').forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.getAttribute('data-eff');
        const cat = btn.getAttribute('data-cat');
        const params = JSON.parse(btn.getAttribute('data-param') || '{}');
        sendCommand('trigger_effect', { name, category: cat, params });
      });
    });

    document.querySelectorAll('.btn-audio').forEach(btn => {
      btn.addEventListener('click', () => {
        const sound = btn.getAttribute('data-sound');
        playSynthSound(sound);
        sendCommand('trigger_effect', { name: 'tts_play', category: 'audio', params: { file_path: sound } });
      });
    });

    document.getElementById('btnSpawnSelectedFile').addEventListener('click', () => {
      const idx = parseInt(document.getElementById('selectAnomalyTemplate').value, 10);
      sendCommand('spawn_anomaly_file', { template_idx: idx });
    });

    // ARG Portal actions
    document.getElementById('btnLaunchArgPortal').addEventListener('click', () => {
      window.open('http://127.0.0.1:6660', '_blank');
    });
    document.getElementById('btnSolveArgPortal').addEventListener('click', () => {
      sendCommand('send_chat', { text: '/override 0x7F_K3RN3L_V0ID' });
    });

    // File Inspector Modal
    document.getElementById('btnCloseModal').addEventListener('click', closeFileModal);
    document.getElementById('btnSimulateCleanFile').addEventListener('click', () => {
      if (state.selected_modal_file) {
        sendCommand('clean_desktop_file', { filename: state.selected_modal_file.filename });
        closeFileModal();
      }
    });
    document.getElementById('btnCopyCipher').addEventListener('click', () => {
      if (state.selected_modal_file && state.selected_modal_file.override_code) {
        navigator.clipboard.writeText(state.selected_modal_file.override_code);
        alert(`Şifre panoya kopyalandı: ${state.selected_modal_file.override_code}`);
      }
    });
    document.getElementById('btnDecryptThisFile').addEventListener('click', () => {
      if (state.selected_modal_file && state.selected_modal_file.override_code) {
        sendCommand('send_chat', { text: `/decrypt ${state.selected_modal_file.override_code}` });
        closeFileModal();
      }
    });

    // Reset & Export Replay
    document.getElementById('btnResetSession').addEventListener('click', () => {
      if (confirm('Oturumu ve simülasyon durumunu sıfırlamak istediğinize emin misiniz?')) {
        sendCommand('reset_session');
      }
    });

    document.getElementById('btnExportReplay').addEventListener('click', () => {
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify({
        session_id: state.session_id,
        timestamp: Date.now(),
        final_state: state,
        event_ledger: state.event_ledger,
        chat_history: state.chat_history,
      }, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `sentient_session_replay_${state.session_id}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });

    // Elapsed timer
    timerInterval = setInterval(() => {
      state.elapsed_seconds++;
      const mins = Math.floor(state.elapsed_seconds / 60).toString().padStart(2, '0');
      const secs = (state.elapsed_seconds % 60).toString().padStart(2, '0');
      document.getElementById('elapsedTimeText').textContent = `${mins}:${secs}`;
      document.getElementById('vtaskClock').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }, 1000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // --- Initialization ---
  window.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    connectWebSocket();
  });
})();
