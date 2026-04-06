# Dark/Light Mode Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-user Dark/Light Mode toggle to the sidebar, persisted in the database.

**Architecture:** CSS custom properties power both themes — `:root` defines light, `.dark` defines dark. The `User` model gets a `theme` field. A `set_theme` POST view (analog to Django's `set_language`) saves the preference and redirects back. `base.html` applies the `dark` class to `<html>` based on the authenticated user's stored preference.

**Tech Stack:** Django 5, Tailwind CSS, HTMX, Django TestCase

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `tailwind.config.js` | Modify | Replace hex values with CSS variable references |
| `static/src/main.css` | Modify | Add `:root` (light) and `.dark` theme blocks |
| `apps/accounts/models.py` | Modify | Add `theme` field to `User` |
| `apps/accounts/migrations/0002_user_theme.py` | Create | Migration for `theme` field |
| `apps/accounts/views.py` | Modify | Add `set_theme` function-based view |
| `apps/accounts/urls.py` | Modify | Register `set-theme/` URL |
| `apps/accounts/tests.py` | Create | Tests for model default and `set_theme` view |
| `templates/base.html` | Modify | Apply `dark` class to `<html>`, add toggle to sidebar |

---

## Task 1: Refactor CSS to custom properties

**Files:**
- Modify: `tailwind.config.js`
- Modify: `static/src/main.css`

- [ ] **Step 1: Replace color values in `tailwind.config.js`**

Replace the entire `colors` block in `tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.html",
    "./apps/**/*.py",
    "./mainty/**/*.py",
  ],
  theme: {
    extend: {
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
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          '"SF Mono"',
          "Menlo",
          "Consolas",
          '"Liberation Mono"',
          "monospace",
        ],
      },
      borderRadius: {
        DEFAULT: "6px",
        sm: "4px",
        md: "6px",
        lg: "8px",
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 2: Add theme blocks to `static/src/main.css`**

Prepend the following before the `@tailwind base;` line (keep everything below it unchanged):

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
  /* Dark Mode — Vercel-Dark */
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

- [ ] **Step 3: Rebuild Tailwind and verify dark mode still looks correct**

```bash
docker compose exec web python manage.py collectstatic --noinput
```

Open the app in the browser — it should look identical to before (dark mode is the current default and `<html>` still has `class="dark"` hardcoded in `base.html` for now). If colors look wrong, check that CSS variables are correctly referenced in `tailwind.config.js`.

- [ ] **Step 4: Commit**

```bash
git add tailwind.config.js static/src/main.css
git commit -m "refactor: move design tokens to CSS custom properties for theme support"
```

---

## Task 2: Add `theme` field to User model

**Files:**
- Modify: `apps/accounts/models.py`
- Create: `apps/accounts/migrations/0002_user_theme.py`
- Create: `apps/accounts/tests.py`

- [ ] **Step 1: Write the failing test**

Create `apps/accounts/tests.py`:

```python
from django.test import TestCase

from apps.accounts.models import User


class UserThemeDefaultTest(TestCase):
    def test_theme_defaults_to_dark(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.assertEqual(user.theme, "dark")

    def test_theme_can_be_set_to_light(self):
        user = User.objects.create_user(username="testuser2", password="testpass123")
        user.theme = "light"
        user.save(update_fields=["theme"])
        user.refresh_from_db()
        self.assertEqual(user.theme, "light")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker compose exec web python manage.py test apps.accounts.tests.UserThemeDefaultTest -v 2
```

Expected: FAIL — `AttributeError: type object 'User' has no attribute 'theme'` (or `FieldError`)

- [ ] **Step 3: Add `theme` field to `apps/accounts/models.py`**

Add the field after `password_changed_at`:

```python
THEME_CHOICES = [("dark", "Dark"), ("light", "Light")]

theme = models.CharField(
    max_length=5,
    choices=THEME_CHOICES,
    default="dark",
    verbose_name=_("Theme"),
)
```

Full updated model for reference:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    THEME_CHOICES = [("dark", "Dark"), ("light", "Light")]

    password_changed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Passwort geändert am"),
    )
    theme = models.CharField(
        max_length=5,
        choices=THEME_CHOICES,
        default="dark",
        verbose_name=_("Theme"),
    )

    class Meta:
        verbose_name = _("Benutzer")
        verbose_name_plural = _("Benutzer")

    @property
    def role(self):
        from .constants import Role
        group_names = {g.name for g in self.groups.all()}
        for role_name in Role.ALL:
            if role_name in group_names:
                return role_name
        return None

    def set_role(self, role_name):
        from django.contrib.auth.models import Group
        from .constants import Role
        self.groups.remove(*self.groups.filter(name__in=Role.ALL))
        if role_name:
            group = Group.objects.get(name=role_name)
            self.groups.add(group)

    def has_role(self, *role_names):
        return self.groups.filter(name__in=role_names).exists()
```

- [ ] **Step 4: Create and apply migration**

```bash
docker compose exec web python manage.py makemigrations accounts --name user_theme
docker compose exec web python manage.py migrate
```

Expected output: `Applying accounts.0002_user_theme... OK`

- [ ] **Step 5: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.accounts.tests.UserThemeDefaultTest -v 2
```

Expected: OK (2 tests pass)

- [ ] **Step 6: Commit**

```bash
git add apps/accounts/models.py apps/accounts/migrations/0002_user_theme.py apps/accounts/tests.py
git commit -m "feat: add theme field to User model (dark/light, default dark)"
```

---

## Task 3: Add `set_theme` view and URL

**Files:**
- Modify: `apps/accounts/views.py`
- Modify: `apps/accounts/urls.py`
- Modify: `apps/accounts/tests.py`

- [ ] **Step 1: Write the failing tests**

Append to `apps/accounts/tests.py`:

```python
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User


class SetThemeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="themeuser", password="testpass123")
        self.client.login(username="themeuser", password="testpass123")

    def test_set_theme_to_light(self):
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "/"},
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "light")

    def test_set_theme_to_dark(self):
        self.user.theme = "light"
        self.user.save(update_fields=["theme"])
        self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "dark", "next": "/"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "dark")

    def test_invalid_theme_ignored(self):
        self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "rainbow", "next": "/"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "dark")  # unchanged

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec web python manage.py test apps.accounts.tests.SetThemeViewTest -v 2
```

Expected: FAIL — `NoReverseMatch: Reverse for 'set_theme' not found`

- [ ] **Step 3: Add `set_theme` view to `apps/accounts/views.py`**

Append to the end of the file (after the existing imports, add `login_required` to the import from `django.contrib.auth.mixins`):

Add to top-level imports:
```python
from django.contrib.auth.decorators import login_required
```

Append the view:
```python
@login_required
def set_theme(request):
    if request.method == "POST":
        theme = request.POST.get("theme")
        if theme in ("dark", "light"):
            request.user.theme = theme
            request.user.save(update_fields=["theme"])
    return redirect(request.POST.get("next") or "/")
```

- [ ] **Step 4: Register URL in `apps/accounts/urls.py`**

Add to `urlpatterns`:
```python
path("set-theme/", views.set_theme, name="set_theme"),
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.accounts.tests.SetThemeViewTest -v 2
```

Expected: OK (4 tests pass)

- [ ] **Step 6: Commit**

```bash
git add apps/accounts/views.py apps/accounts/urls.py apps/accounts/tests.py
git commit -m "feat: add set_theme view and URL for per-user theme switching"
```

---

## Task 4: Wire up templates

**Files:**
- Modify: `templates/base.html`

- [ ] **Step 1: Update `<html>` tag in `templates/base.html`**

Change line 3 from:
```html
<html lang="{{ LANGUAGE_CODE }}" class="h-full">
```
to:
```html
<html lang="{{ LANGUAGE_CODE }}" class="{% if not user.is_authenticated or user.theme == 'dark' %}dark {% endif %}h-full">
```

- [ ] **Step 2: Add theme toggle to sidebar in `templates/base.html`**

Find the sidebar bottom section (the `<div class="px-3 py-4 border-t border-border shrink-0">` block that contains the language switcher). Add the theme toggle **above** the language switcher form:

```html
    {# Theme toggle #}
    <div class="px-3 py-4 border-t border-border shrink-0">
      {% if user.is_authenticated %}
      <form action="{% url 'accounts:set_theme' %}" method="post" class="mb-2">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        <div class="flex rounded border border-border overflow-hidden text-xs">
          <button name="theme" value="dark" type="submit"
            class="flex-1 py-1.5 transition-colors {% if user.theme == 'dark' %}bg-white text-black font-medium{% else %}text-content-secondary hover:text-white{% endif %}">
            Dark
          </button>
          <button name="theme" value="light" type="submit"
            class="flex-1 py-1.5 transition-colors {% if user.theme == 'light' %}bg-white text-black font-medium{% else %}text-content-secondary hover:text-white{% endif %}">
            Light
          </button>
        </div>
      </form>
      {% endif %}

      {# Language switcher — keep existing form here unchanged #}
```

The full sidebar bottom block should look like this after the edit:

```html
    {# Theme + Language #}
    <div class="px-3 py-4 border-t border-border shrink-0">
      {% if user.is_authenticated %}
      <form action="{% url 'accounts:set_theme' %}" method="post" class="mb-2">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        <div class="flex rounded border border-border overflow-hidden text-xs">
          <button name="theme" value="dark" type="submit"
            class="flex-1 py-1.5 transition-colors {% if user.theme == 'dark' %}bg-white text-black font-medium{% else %}text-content-secondary hover:text-white{% endif %}">
            Dark
          </button>
          <button name="theme" value="light" type="submit"
            class="flex-1 py-1.5 transition-colors {% if user.theme == 'light' %}bg-white text-black font-medium{% else %}text-content-secondary hover:text-white{% endif %}">
            Light
          </button>
        </div>
      </form>
      {% endif %}
      <form action="{% url 'set_language' %}" method="post">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        {% get_current_language as current_lang %}
        {% get_available_languages as lang_list %}
        <select
          name="language"
          onchange="this.form.submit()"
          class="w-full bg-surface-card text-content-secondary text-xs border border-border rounded px-2 py-1.5 focus:outline-none focus:border-white/40"
        >
          {% for code, name in lang_list %}
            <option value="{{ code }}" {% if code == current_lang %}selected{% endif %}>
              {{ name }}
            </option>
          {% endfor %}
        </select>
      </form>
    </div>
```

- [ ] **Step 3: Rebuild CSS and verify visually**

```bash
docker compose exec web python manage.py collectstatic --noinput
```

1. Open the app — should be in **Dark mode** (existing users default to `dark`)
2. Click **Light** button — page reloads, background turns white, sidebar/table/cards all switch to light palette
3. Click **Dark** button — switches back
4. The active button (Dark or Light) should have `bg-white text-black` styling
5. Log out and back in — preference should persist

- [ ] **Step 4: Run all accounts tests**

```bash
docker compose exec web python manage.py test apps.accounts -v 2
```

Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add templates/base.html
git commit -m "feat: wire dark/light mode toggle into sidebar and base template"
```
