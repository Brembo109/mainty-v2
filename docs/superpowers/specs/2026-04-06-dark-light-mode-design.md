# Dark/Light Mode Switch — Design Spec

**Date:** 2026-04-06  
**Status:** Approved

## Summary

Add a Dark/Light Mode toggle to mainty-v2. The user's preference is stored per account in the database. The toggle is a labeled segmented control (Dark | Light) in the sidebar, next to the existing language switcher.

## Approach

CSS Custom Properties with server-side persistence. Tailwind color tokens are refactored to reference CSS variables. Two theme blocks in `main.css` define the color values. The `<html>` element receives a `dark` class based on the authenticated user's stored preference. Switching themes works via a Form POST (identical pattern to the language switcher), causing a page reload.

No template changes beyond `base.html` are required after the CSS refactor.

## Section 1: CSS Architecture

### `tailwind.config.js`

All hardcoded hex color values are replaced with CSS variable references:

```js
colors: {
  surface: {
    DEFAULT: "var(--color-surface)",
    card: "var(--color-surface-card)",
    elevated: "var(--color-surface-elevated)",
  },
  border: {
    DEFAULT: "var(--color-border)",
    subtle: "var(--color-border-subtle)",
    strong: "var(--color-border-strong)",
  },
  content: {
    primary: "var(--color-content-primary)",
    secondary: "var(--color-content-secondary)",
    tertiary: "var(--color-content-tertiary)",
  },
  status: {
    success: "var(--color-status-success)",
    warning: "var(--color-status-warning)",
    danger: "var(--color-status-danger)",
    "success-bg": "var(--color-status-success-bg)",
    "warning-bg": "var(--color-status-warning-bg)",
    "danger-bg": "var(--color-status-danger-bg)",
  },
}
```

### `static/src/main.css`

Two theme blocks added before `@tailwind base`:

```css
:root {
  /* Light Mode */
  --color-surface: #ffffff;
  --color-surface-card: #f5f5f5;
  --color-surface-elevated: #fafafa;
  --color-border: #e5e5e5;
  --color-border-subtle: #f0f0f0;
  --color-border-strong: #d4d4d4;
  --color-content-primary: #0a0a0a;
  --color-content-secondary: #737373;
  --color-content-tertiary: #a3a3a3;
  --color-status-success: #00c853;
  --color-status-warning: #ffd600;
  --color-status-danger: #ff1744;
  --color-status-success-bg: rgba(0, 200, 83, 0.1);
  --color-status-warning-bg: rgba(255, 214, 0, 0.1);
  --color-status-danger-bg: rgba(255, 23, 68, 0.1);
}

.dark {
  /* Dark Mode — Vercel-Dark palette */
  --color-surface: #000000;
  --color-surface-card: #111111;
  --color-surface-elevated: #0a0a0a;
  --color-border: #222222;
  --color-border-subtle: #1a1a1a;
  --color-border-strong: #333333;
  --color-content-primary: #ffffff;
  --color-content-secondary: #888888;
  --color-content-tertiary: #555555;
  --color-status-success: #00c853;
  --color-status-warning: #ffd600;
  --color-status-danger: #ff1744;
  --color-status-success-bg: rgba(0, 200, 83, 0.1);
  --color-status-warning-bg: rgba(255, 214, 0, 0.1);
  --color-status-danger-bg: rgba(255, 23, 68, 0.1);
}
```

Status colors are identical in both themes (vibrant colors work on both backgrounds).

## Section 2: User Model + View

### `accounts/models.py`

Add one field to `CustomUser`:

```python
THEME_CHOICES = [("dark", "Dark"), ("light", "Light")]
theme = models.CharField(max_length=5, choices=THEME_CHOICES, default="dark")
```

One migration required.

### `accounts/views.py`

New `set_theme` view, analogous to Django's `set_language`:

```python
@login_required
def set_theme(request):
    if request.method == "POST":
        theme = request.POST.get("theme")
        if theme in ("dark", "light"):
            request.user.theme = theme
            request.user.save(update_fields=["theme"])
    return redirect(request.POST.get("next", "/"))
```

### `accounts/urls.py`

```python
path("set-theme/", views.set_theme, name="set_theme"),
```

## Section 3: Templates

### `templates/base.html` — `<html>` tag

```html
<html lang="{{ LANGUAGE_CODE }}"
      class="{% if not user.is_authenticated or user.theme == 'dark' %}dark {% endif %}h-full">
```

Unauthenticated users (login page) default to Dark.

### Sidebar toggle (in `templates/base.html`, sidebar bottom section)

Added inside the existing `px-3 py-4 border-t border-border` block, above or below the language switcher:

```html
<form action="{% url 'accounts:set_theme' %}" method="post">
  {% csrf_token %}
  <input name="next" type="hidden" value="{{ request.get_full_path }}">
  <div class="flex rounded border border-border overflow-hidden text-xs">
    <button name="theme" value="dark"
      class="flex-1 py-1.5 transition-colors
        {% if user.theme == 'dark' %}bg-white text-black font-medium
        {% else %}text-content-secondary hover:text-white{% endif %}">
      Dark
    </button>
    <button name="theme" value="light"
      class="flex-1 py-1.5 transition-colors
        {% if user.theme == 'light' %}bg-white text-black font-medium
        {% else %}text-content-secondary hover:text-white{% endif %}">
      Light
    </button>
  </div>
</form>
```

## Out of Scope

- Per-browser fallback via `prefers-color-scheme` media query
- Instant switching without page reload (would require JS)
- Theme preference for unauthenticated users
