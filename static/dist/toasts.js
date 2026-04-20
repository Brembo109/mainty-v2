/* mainty toast system
   Public API:
     Toasts.show({ variant, title, msg, action, duration, id })
     Toasts.dismiss(element)
   Variants: 'ok' | 'info' | 'warn' | 'danger'
   Defaults: ok/info 5s, warn 7s, danger persistent.
*/
(function () {
  const MAX_VISIBLE = 3;
  const DEFAULT_DURATION = { ok: 5000, info: 5000, warn: 7000, danger: 0 };

  function getStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      stack.setAttribute('role', 'region');
      stack.setAttribute('aria-live', 'polite');
      stack.setAttribute('aria-label', 'Benachrichtigungen');
      document.body.appendChild(stack);
    }
    return stack;
  }

  function show({ variant = 'info', title = '', msg = '', action = null, duration, id = null } = {}) {
    const stack = getStack();

    if (id) {
      const existing = stack.querySelector(`[data-toast-id="${CSS.escape(id)}"]`);
      if (existing) dismiss(existing, { immediate: true });
    }

    while (stack.children.length >= MAX_VISIBLE) {
      dismiss(stack.firstElementChild, { immediate: true });
    }

    const dur = duration != null ? duration : (DEFAULT_DURATION[variant] ?? 5000);

    const el = document.createElement('div');
    el.className = `toast toast-${variant}`;
    if (id) el.dataset.toastId = id;
    if (dur > 0) el.style.setProperty('--toast-duration', `${dur}ms`);
    el.setAttribute('role', variant === 'danger' ? 'alert' : 'status');

    el.innerHTML = `
      <span class="toast-icon" aria-hidden="true"></span>
      <div class="toast-body">
        <div class="toast-title"></div>
        ${msg ? '<div class="toast-msg"></div>' : ''}
        ${action ? '<a class="toast-action" href="#"></a>' : ''}
      </div>
      <button class="toast-close" aria-label="Schließen">×</button>
      ${dur > 0 ? '<div class="toast-progress"></div>' : ''}
    `;

    el.querySelector('.toast-title').textContent = title;
    if (msg) el.querySelector('.toast-msg').textContent = msg;
    if (action) {
      const a = el.querySelector('.toast-action');
      a.textContent = action.label;
      a.href = action.href || '#';
      if (action.onClick) a.addEventListener('click', (e) => { e.preventDefault(); action.onClick(e); });
    }

    el.querySelector('.toast-close').addEventListener('click', () => dismiss(el));

    stack.appendChild(el);

    if (dur > 0) {
      let timer = setTimeout(() => dismiss(el), dur);
      el.addEventListener('mouseenter', () => { clearTimeout(timer); });
      el.addEventListener('mouseleave', () => { timer = setTimeout(() => dismiss(el), dur * 0.5); });
    }

    return el;
  }

  function dismiss(el, { immediate = false } = {}) {
    if (!el) return;
    if (immediate) { el.remove(); return; }
    el.setAttribute('data-leaving', '');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }

  function consumeServerMessages() {
    const bag = document.querySelector('[data-django-messages]');
    if (!bag) return;
    bag.querySelectorAll('[data-message]').forEach((item) => {
      show({
        variant: item.dataset.level || 'info',
        title:   item.dataset.title || item.textContent.trim(),
        msg:     item.dataset.msg || '',
      });
    });
    bag.remove();
  }

  function hookHtmx() {
    document.body.addEventListener('toast', (ev) => show(ev.detail));
  }

  document.addEventListener('DOMContentLoaded', () => {
    consumeServerMessages();
    hookHtmx();
  });
  document.body && document.body.addEventListener('htmx:afterSwap', consumeServerMessages);

  window.Toasts = { show, dismiss };
})();
