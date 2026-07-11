/* ═══════════════════════════════════════════════════════════
   INKWELL – main.js
   Dark mode · AOS init · Navbar scroll · Notifications
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. AOS Animations ──
  AOS.init({ duration: 600, once: true, offset: 60, easing: 'ease-out-cubic' });

  // ── 2. Dark Mode ──
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon   = document.getElementById('themeIcon');
  const htmlEl      = document.documentElement;

  const applyTheme = (theme) => {
    htmlEl.setAttribute('data-bs-theme', theme);
    if (themeIcon) {
      themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
    localStorage.setItem('inkwell_theme', theme);
  };

  // Load saved preference
  applyTheme(localStorage.getItem('inkwell_theme') || 'light');

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = htmlEl.getAttribute('data-bs-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // ── 3. Navbar scroll shadow ──
  const navbar = document.getElementById('mainNavbar');
  if (navbar) {
    const handleScroll = () => {
      navbar.classList.toggle('scrolled', window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  // ── 4. Auto-dismiss flash messages ──
  setTimeout(() => {
    document.querySelectorAll('.flash-toast').forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  }, 5000);

  // ── 5. Notifications (if logged in) ──
  const notifDot     = document.getElementById('notifDot');
  const notifContent = document.getElementById('notifContent');
  if (notifContent) {
    fetch('/api/v1/users/me/notifications', {
      headers: { 'Authorization': `Bearer ${getCookie('access_token_cookie') || ''}` }
    })
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (!data || !data.data) return;
      const notifs = data.data.slice(0, 5);
      if (notifs.length > 0) {
        const unread = notifs.filter(n => !n.is_read).length;
        if (unread > 0 && notifDot) notifDot.style.display = 'block';
        notifContent.innerHTML = notifs.map(n => `
          <div class="dropdown-item small py-2 border-bottom">
            <div class="fw-medium">${escapeHtml(n.message || n.type)}</div>
            <div class="text-muted" style="font-size:.72rem">${timeAgo(n.created_at)}</div>
          </div>
        `).join('');
      } else {
        notifContent.innerHTML = '<span class="text-muted small">No notifications</span>';
      }
    })
    .catch(() => {
      notifContent.innerHTML = '<span class="text-muted small">No notifications</span>';
    });
  }

  // ── 6. Search form mobile behaviour ──
  const searchForm = document.querySelector('.search-form');
  if (searchForm && window.innerWidth < 768) {
    searchForm.classList.add('d-none');
  }

});

/* ── Helpers ── */
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : '';
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

function timeAgo(isoStr) {
  if (!isoStr) return '';
  const diff = (Date.now() - new Date(isoStr)) / 1000;
  if (diff < 60)  return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
    .then(() => showToast('Link copied to clipboard!', 'success'))
    .catch(() => showToast('Could not copy link.', 'danger'));
}

function showToast(message, type = 'info') {
  const container = document.getElementById('flashContainer') || (() => {
    const c = document.createElement('div');
    c.id = 'flashContainer';
    c.className = 'flash-container';
    document.body.appendChild(c);
    return c;
  })();
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} alert-dismissible fade show flash-toast`;
  toast.innerHTML = `${escapeHtml(message)}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  container.appendChild(toast);
  setTimeout(() => bootstrap.Alert.getOrCreateInstance(toast).close(), 4000);
}
