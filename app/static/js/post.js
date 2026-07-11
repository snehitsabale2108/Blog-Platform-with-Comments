/* ═══════════════════════════════════════════════════════════
   INKWELL – post.js
   Like · Bookmark · Reading progress · ToC · Comments
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Reading Progress Bar ──
  const progressBar = document.createElement('div');
  progressBar.id = 'readingProgress';
  document.body.prepend(progressBar);

  const article = document.querySelector('.post-content');
  if (article) {
    window.addEventListener('scroll', () => {
      const rect = article.getBoundingClientRect();
      const total = article.offsetHeight;
      const read  = Math.max(0, -rect.top);
      const progress = Math.min(1, read / total);
      progressBar.style.transform = `scaleX(${progress})`;
    }, { passive: true });
  }

  // ── Table of Contents ──
  buildToc();

  // ── Like Button ──
  const likeBtn   = document.getElementById('likeBtn');
  const likeCount = document.getElementById('likeCount');
  if (likeBtn && typeof POST_SLUG !== 'undefined') {
    const isLiked = likeBtn.dataset.liked === 'true';
    if (isLiked) likeBtn.classList.add('liked');

    likeBtn.addEventListener('click', async () => {
      if (!IS_LOGGED_IN) { window.location = '/auth/login'; return; }
      const res = await fetch(`/posts/${POST_SLUG}/like`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        likeCount.textContent = data.count;
        const icon = likeBtn.querySelector('i');
        if (data.liked) {
          likeBtn.classList.add('liked');
          icon.className = 'bi bi-heart-fill text-danger';
          likeBtn.style.transform = 'scale(1.25)';
          setTimeout(() => likeBtn.style.transform = '', 250);
        } else {
          likeBtn.classList.remove('liked');
          icon.className = 'bi bi-heart';
        }
      }
    });
  }

  // ── Bookmark Button ──
  const bookmarkBtn = document.getElementById('bookmarkBtn');
  if (bookmarkBtn && typeof POST_SLUG !== 'undefined') {
    const isBookmarked = bookmarkBtn.dataset.bookmarked === 'true';
    if (isBookmarked) bookmarkBtn.classList.add('bookmarked');

    bookmarkBtn.addEventListener('click', async () => {
      if (!IS_LOGGED_IN) { window.location = '/auth/login'; return; }
      const res = await fetch(`/posts/${POST_SLUG}/bookmark`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const icon = bookmarkBtn.querySelector('i');
        if (data.bookmarked) {
          bookmarkBtn.classList.add('bookmarked');
          icon.className = 'bi bi-bookmark-fill text-primary';
          showToast('Post bookmarked!', 'success');
        } else {
          bookmarkBtn.classList.remove('bookmarked');
          icon.className = 'bi bi-bookmark';
          showToast('Bookmark removed.', 'info');
        }
      }
    });
  }

  // ── Comment Likes ──
  document.querySelectorAll('.comment-like-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!IS_LOGGED_IN) { window.location = '/auth/login'; return; }
      const id  = btn.dataset.commentId;
      const res = await fetch(`/comments/${id}/like`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const countEl = document.querySelector(`.like-count-${id}`);
        if (countEl) countEl.textContent = data.count;
        const icon = btn.querySelector('i');
        if (data.liked) {
          icon.className = 'bi bi-heart-fill text-danger';
        } else {
          icon.className = 'bi bi-heart';
        }
      }
    });
  });

});

// ── Reply / Edit helpers ──
function toggleReplyForm(commentId) {
  const form = document.getElementById(`reply-form-${commentId}`);
  if (form) form.classList.toggle('d-none');
}
function toggleEditForm(commentId) {
  const body = document.getElementById(`comment-body-${commentId}`);
  const form = document.getElementById(`edit-form-${commentId}`);
  if (body && form) {
    body.classList.toggle('d-none');
    form.classList.toggle('d-none');
  }
}
function cancelEdit(commentId) {
  document.getElementById(`comment-body-${commentId}`)?.classList.remove('d-none');
  document.getElementById(`edit-form-${commentId}`)?.classList.add('d-none');
}

// ── Table of Contents ──
function buildToc() {
  const toc     = document.getElementById('toc');
  const tocNav  = document.getElementById('tocNav');
  const content = document.querySelector('.post-content');
  if (!toc || !tocNav || !content) return;

  const headings = content.querySelectorAll('h2, h3');
  if (headings.length < 2) return;

  toc.style.display = 'block';
  headings.forEach((h, i) => {
    if (!h.id) h.id = `heading-${i}`;
    const a = document.createElement('a');
    a.href        = `#${h.id}`;
    a.textContent = h.textContent;
    a.className   = h.tagName === 'H3' ? 'toc-h3' : '';
    a.addEventListener('click', e => {
      e.preventDefault();
      document.getElementById(h.id).scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    tocNav.appendChild(a);
  });

  // Scroll spy
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const id = entry.target.id;
      const link = tocNav.querySelector(`a[href="#${id}"]`);
      if (link) link.classList.toggle('active', entry.isIntersecting);
    });
  }, { rootMargin: '-20% 0px -60% 0px' });
  headings.forEach(h => obs.observe(h));
}

// re-use showToast from main.js
