/* ═══════════════════════════════════════════════════════════
   Winneba Technical Institute — Main JavaScript
   ═══════════════════════════════════════════════════════════ */

'use strict';

// ── Sidebar Toggle ──────────────────────────────────────────
(function () {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('appSidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('show');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      if (sidebar) sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }
})();

// ── Notification Panel ──────────────────────────────────────
(function () {
  const btn = document.getElementById('notifBtn');
  const panel = document.getElementById('notifPanel');
  if (!btn || !panel) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.toggle('show');
  });

  document.addEventListener('click', (e) => {
    if (!panel.contains(e.target) && e.target !== btn) {
      panel.classList.remove('show');
    }
  });
})();

// ── Auto-dismiss Django messages ────────────────────────────
(function () {
  const alerts = document.querySelectorAll('.alert.auto-dismiss');
  alerts.forEach(a => {
    setTimeout(() => {
      a.style.transition = 'opacity 0.5s';
      a.style.opacity = '0';
      setTimeout(() => a.remove(), 500);
    }, 4000);
  });
})();

// ── Notification Sound ──────────────────────────────────────
function playNotifSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.4);
  } catch (e) { /* silent fail */ }
}

// ── Reminder Sound (more urgent) ───────────────────────────
function playReminderSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523, 659, 784, 1047];
    notes.forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.3, ctx.currentTime + i * 0.15);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.15 + 0.3);
      osc.start(ctx.currentTime + i * 0.15);
      osc.stop(ctx.currentTime + i * 0.15 + 0.3);
    });
  } catch (e) { /* silent fail */ }
}

// ── Show Reminder Toast ─────────────────────────────────────
function showReminderToast(subject, startTime, minutesUntil) {
  const toast = document.getElementById('reminderToast');
  if (!toast) return;
  const title = toast.querySelector('.reminder-title');
  const body = toast.querySelector('.reminder-body');
  if (title) title.textContent = `⏰ Class Reminder: ${subject}`;
  if (body) {
    if (minutesUntil <= 0) {
      body.textContent = `Your class starts NOW at ${startTime}. Please proceed to your classroom.`;
    } else {
      body.textContent = `Your class starts in ${minutesUntil} minute(s) at ${startTime}. Get ready!`;
    }
  }
  toast.classList.add('show');
  playReminderSound();
  setTimeout(() => toast.classList.remove('show'), 10000);
}

// ── Class Reminder System ───────────────────────────────────
(function () {
  const reminderApiUrl = window.REMINDER_API_URL;
  if (!reminderApiUrl) return;

  const notifiedSchedules = new Set();

  function checkReminders() {
    fetch(reminderApiUrl)
      .then(r => r.json())
      .then(data => {
        data.schedules.forEach(s => {
          const key10 = `10_${s.id}`;
          const key2 = `2_${s.id}`;
          const key0 = `0_${s.id}`;

          if (s.minutes_until <= 0 && s.minutes_until > -5 && !notifiedSchedules.has(key0)) {
            notifiedSchedules.add(key0);
            showReminderToast(s.subject, s.start_time, 0);
          } else if (s.minutes_until <= 2 && s.minutes_until > 0 && !notifiedSchedules.has(key2)) {
            notifiedSchedules.add(key2);
            showReminderToast(s.subject, s.start_time, s.minutes_until);
          } else if (s.minutes_until <= 10 && s.minutes_until > 2 && !notifiedSchedules.has(key10)) {
            notifiedSchedules.add(key10);
            showReminderToast(s.subject, s.start_time, s.minutes_until);
          }
        });
      })
      .catch(() => {});
  }

  checkReminders();
  setInterval(checkReminders, 60000); // check every minute
})();

// ── Live Notification Polling ───────────────────────────────
(function () {
  const apiUrl = window.NOTIF_API_URL;
  if (!apiUrl) return;

  let lastCount = 0;

  function pollNotifications() {
    fetch(apiUrl)
      .then(r => r.json())
      .then(data => {
        const dot = document.querySelector('.notif-dot');
        const badge = document.getElementById('notifBadge');
        const count = data.count;

        if (count > 0) {
          if (dot) dot.style.display = 'block';
          if (badge) { badge.textContent = count; badge.style.display = 'inline'; }
          if (count > lastCount) playNotifSound();
        } else {
          if (dot) dot.style.display = 'none';
          if (badge) badge.style.display = 'none';
        }
        lastCount = count;

        // Update panel
        const list = document.getElementById('notifList');
        if (list && data.notifications) {
          if (data.notifications.length === 0) {
            list.innerHTML = '<div class="p-3 text-center text-muted" style="font-size:0.85rem">No new notifications</div>';
          } else {
            list.innerHTML = data.notifications.map(n => `
              <div class="notif-item unread" onclick="markRead(${n.id})">
                <div class="notif-icon ${n.type}"><i class="fas ${getNotifIcon(n.type)}"></i></div>
                <div class="notif-content">
                  <h6>${escHtml(n.title)}</h6>
                  <p>${escHtml(n.message)}</p>
                  <small>${n.time}</small>
                </div>
              </div>
            `).join('');
          }
        }
      })
      .catch(() => {});
  }

  pollNotifications();
  setInterval(pollNotifications, 15000);
})();

function getNotifIcon(type) {
  const icons = {
    attendance: 'fa-check-circle',
    schedule: 'fa-calendar',
    reminder: 'fa-bell',
    general: 'fa-info-circle',
    admin: 'fa-shield-alt',
    chat: 'fa-comment',
  };
  return icons[type] || 'fa-bell';
}

function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function markRead(id) {
  const url = window.MARK_READ_BASE_URL;
  if (!url) return;
  fetch(url.replace('0', id), { method: 'GET' }).catch(() => {});
}

// ── WebSocket Chat ──────────────────────────────────────────
window.initChat = function (roomName, currentUserId, recipientId, wsBase) {
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSendBtn');
  const messagesDiv = document.getElementById('chatMessages');
  if (!input || !messagesDiv) return;

  const wsUrl = `${wsBase}ws/chat/${roomName}/`;
  let socket;

  function connect() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('Chat connected');
    };

    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'chat_message') {
        appendMessage(data.message, data.sender_id, data.sender_name, data.timestamp, data.is_admin);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        if (data.sender_id !== currentUserId) playNotifSound();
      }
    };

    socket.onclose = () => {
      setTimeout(connect, 3000);
    };
  }

  connect();

  function sendMessage() {
    const msg = input.value.trim();
    if (!msg || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ message: msg, recipient_id: recipientId }));
    input.value = '';
  }

  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // Scroll to bottom on load
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
};

function appendMessage(message, senderId, senderName, timestamp, isAdmin) {
  const messagesDiv = document.getElementById('chatMessages');
  const currentUserId = window.CURRENT_USER_ID;
  const isSent = senderId === currentUserId;
  const div = document.createElement('div');
  div.style.display = 'flex';
  div.style.flexDirection = 'column';
  div.style.alignItems = isSent ? 'flex-end' : 'flex-start';

  div.innerHTML = `
    ${!isSent ? `<small style="font-size:0.72rem;color:#888;margin-bottom:2px;padding-left:4px">${escHtml(senderName)}</small>` : ''}
    <div class="message-bubble ${isSent ? 'sent' : 'received'}">
      ${escHtml(message)}
      <span class="message-time">${timestamp}</span>
    </div>
  `;
  messagesDiv.appendChild(div);
}

// ── QR Scanner (html5-qrcode) ───────────────────────────────
window.initQRScanner = function (onScanSuccess) {
  if (typeof Html5QrcodeScanner === 'undefined') return;
  const scanner = new Html5QrcodeScanner('qr-reader', {
    fps: 10,
    qrbox: { width: 250, height: 250 },
    rememberLastUsedCamera: true,
  }, false);
  scanner.render(onScanSuccess, (err) => {});
};
