/* ═══════════════════════════════════════════════════════════
   INKWELL – editor.js
   Quill rich editor · Cover upload · Autosave · Word count
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  if (typeof Quill === 'undefined') return;

  // ── Quill Init ──
  const quill = new Quill('#editor', {
    theme: 'snow',
    placeholder: 'Write your story here…',
    modules: {
      toolbar: [
        [{ header: [2, 3, 4, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        [{ list: 'ordered' }, { list: 'bullet' }],
        ['link', 'image'],
        [{ align: [] }],
        ['clean'],
      ]
    }
  });

  // Pre-fill content from hidden input (edit mode)
  const hiddenContent = document.getElementById('hiddenContent');
  const titleInput    = document.getElementById('titleInput');
  const titleCounter  = document.getElementById('titleCounter');
  const wordCountEl   = document.getElementById('wordCount');
  const readTimeEl    = document.getElementById('readTime');
  const statusText    = document.getElementById('statusText');

  // Word count & read time
  quill.on('text-change', () => {
    const text  = quill.getText().trim();
    const words = text ? text.split(/\s+/).length : 0;
    if (wordCountEl) wordCountEl.textContent = words.toLocaleString();
    if (readTimeEl)  readTimeEl.textContent  = `~${Math.max(1, Math.ceil(words / 200))} min`;
    autoSave();
  });

  // Title char counter
  if (titleInput && titleCounter) {
    const updateCounter = () => titleCounter.textContent = `${titleInput.value.length}/255`;
    titleInput.addEventListener('input', updateCounter);
    updateCounter();
  }

  // ── Form Submit helpers ──
  const form          = document.getElementById('postForm');
  const postAction    = document.getElementById('postAction');
  const saveDraftBtn  = document.getElementById('saveDraftBtn');
  const publishBtn    = document.getElementById('publishBtn');

  function submitForm(action) {
    hiddenContent.value = quill.root.innerHTML;
    postAction.value    = action;
    form.submit();
  }

  if (saveDraftBtn)  saveDraftBtn.addEventListener('click', () => submitForm('draft'));
  if (publishBtn)    publishBtn.addEventListener('click',   () => submitForm('publish'));

  // ── Cover Image Upload ──
  const coverZone    = document.getElementById('coverUploadZone');
  const coverInput   = document.getElementById('coverInput');
  const placeholder  = document.getElementById('coverPlaceholder');

  if (coverZone && coverInput) {
    coverZone.addEventListener('click', (e) => {
      if (!e.target.closest('.btn-remove-cover')) coverInput.click();
    });
    coverZone.addEventListener('dragover', (e) => { e.preventDefault(); coverZone.style.borderColor = 'var(--ink-primary)'; });
    coverZone.addEventListener('dragleave', () => { coverZone.style.borderColor = ''; });
    coverZone.addEventListener('drop', (e) => {
      e.preventDefault();
      coverZone.style.borderColor = '';
      const file = e.dataTransfer.files[0];
      if (file) handleCoverFile(file);
    });

    coverInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) handleCoverFile(file);
    });

    function handleCoverFile(file) {
      if (!file.type.startsWith('image/')) { showToast('Please select an image file.', 'danger'); return; }
      if (file.size > 5 * 1024 * 1024)    { showToast('Image must be under 5MB.', 'danger'); return; }
      const reader = new FileReader();
      reader.onload = (ev) => {
        let preview = coverZone.querySelector('#coverPreview');
        if (!preview) {
          preview = document.createElement('img');
          preview.id = 'coverPreview';
          preview.className = 'cover-preview-img';
          if (placeholder) placeholder.style.display = 'none';
          // Remove button
          let removeBtn = coverZone.querySelector('.btn-remove-cover');
          if (!removeBtn) {
            removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn-remove-cover';
            removeBtn.innerHTML = '<i class="bi bi-x"></i>';
            removeBtn.onclick = () => removeCover();
            coverZone.appendChild(removeBtn);
          }
          coverZone.insertBefore(preview, coverZone.firstChild);
        }
        preview.src = ev.target.result;
      };
      reader.readAsDataURL(file);
    }
  }

  // ── Autosave (localStorage) ──
  const AUTOSAVE_KEY = `inkwell_draft_${window.location.pathname}`;
  let autoSaveTimer;

  function autoSave() {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
      const data = {
        title: titleInput?.value || '',
        content: quill.root.innerHTML,
        saved: new Date().toISOString(),
      };
      localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(data));
      if (statusText) {
        statusText.textContent = 'Autosaved';
        setTimeout(() => statusText.textContent = 'Draft', 2000);
      }
    }, 2000);
  }

  // Load autosaved content if title is empty (new post only)
  if (titleInput && !titleInput.value) {
    const saved = localStorage.getItem(AUTOSAVE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        if (data.title) titleInput.value = data.title;
        if (data.content) quill.root.innerHTML = data.content;
      } catch (e) {}
    }
  }

  // Clear autosave on submit
  if (form) {
    form.addEventListener('submit', () => localStorage.removeItem(AUTOSAVE_KEY));
  }
});

function removeCover() {
  const zone  = document.getElementById('coverUploadZone');
  const input = document.getElementById('coverInput');
  const ph    = document.getElementById('coverPlaceholder');
  zone.querySelectorAll('.cover-preview-img, .btn-remove-cover').forEach(el => el.remove());
  if (ph) ph.style.display = '';
  if (input) input.value = '';
}
