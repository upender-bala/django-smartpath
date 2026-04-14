# Django SmartPath

**Stop copying file paths by hand.** Django SmartPath scans your project's `media/` and `static/` folders and lets you pick any file from a popup — then inserts the correct Django URL or template tag right at your cursor.

Works in **VS Code**, **PyCharm**, and **Sublime Text**.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works](#how-it-works)
3. [VS Code Extension — Detailed Usage](#vs-code-extension--detailed-usage)
4. [The `{% smartpath %}` Template Tag](#the--smartpath--template-tag)
5. [The `{% static %}` Tag (for static files)](#the--static--tag-for-static-files)
6. [CLI Reference](#cli-reference)
7. [Settings & Configuration](#settings--configuration)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install the pip library (required by all IDE plugins)
pip install django-smartpath

# 2. Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    ...
    'django_smartpath',
]

# 3. Install the VS Code extension
#    Search "Django SmartPath" in the Extensions panel (Ctrl+Shift+X)
#    — or install from the command line:
code --install-extension django-smartpath.vsix

# 4. Open any .py or .html file in your Django project
#    Press  Ctrl+Shift+D  (Cmd+Shift+D on macOS)
#    Pick a file from the popup → it's inserted at your cursor
```

---

## How It Works

Django SmartPath has two parts:

| Component | What it does |
|-----------|--------------|
| **pip library** (`django-smartpath`) | Scans your project from the CLI, powers the `{% smartpath %}` template tag |
| **IDE plugin** (VS Code / PyCharm / Sublime) | Calls the CLI, shows a searchable popup, inserts the result at cursor |

The IDE plugin calls:
```
python -m django_smartpath.cli scan --path /path/to/current/file.py --format full
```

The CLI walks up the directory tree from the current file, finds `manage.py` (your Django root), then scans every `media/`, `static/`, and app-level `<app>/static/` folder. Results come back as JSON, which the plugin turns into the popup you see.

**No server required. No Django needs to be running. Pure filesystem scan.**

---

## VS Code Extension — Detailed Usage

### Opening the file picker

With any `.py`, `.html`, `.htm`, or `.djhtml` file open and focused:

| Action | Shortcut |
|--------|----------|
| Open file picker | `Ctrl+Shift+D` (Windows/Linux) · `Cmd+Shift+D` (macOS) |
| Open via Command Palette | `Ctrl+Shift+P` → `Django SmartPath: Insert File Path` |

### What the popup looks like

```
Django SmartPath — HTML  (static → {% static '…' %}  |  media → {% smartpath '…' %})
────────────────────────────────────────────────────────────────────────────────────
Search 42 files... (/home/user/myproject)

🖼️ logo.png                   /media/images/logo.png
   $(database) media  •  images/logo.png  •  45.3KB  🖼 image

🎨 styles.css                  /static/css/styles.css
   $(file-code) static  •  css/styles.css  •  12.1KB

⚡ app.js                      /static/js/app.js
   $(file-code) static  •  js/app.js  •  8.7KB
```

- **Type anything** to filter by filename or path
- **Arrow keys** to navigate up/down
- **Enter** to insert the selected file at your cursor
- **Escape** to cancel

### Image preview panel

When you highlight an image file (`png`, `jpg`, `jpeg`, `gif`, `webp`, `svg`, etc.), a **preview panel opens beside your editor** automatically. It shows:

- The image rendered at full quality
- The filename and file size
- The Django URL that will be inserted

The preview panel closes when you select a non-image file or dismiss the picker.

### What gets inserted — Python files (`.py`)

In a Python file, the URL string is inserted:

```python
# You type:  logo
# You select: logo.png  (/media/images/logo.png)

# Result inserted at cursor:
"/media/images/logo.png"
```

Use this when constructing URLs in views, serializers, model methods, etc.:

```python
def get_logo_url(self):
    return "/media/images/logo.png"   # ← inserted by SmartPath
```

### What gets inserted — HTML template files (`.html`)

In an HTML template, the correct Django tag is inserted based on the file type:

**Static files** (CSS, JS, fonts, images in `static/`) → standard `{% static %}` tag:

```html
{% load static %}

<link rel="stylesheet" href="{% static 'css/styles.css' %}">
<script src="{% static 'js/app.js' %}"></script>
<img src="{% static 'images/logo.png' %}" alt="Logo">
```

**Media files** (user-uploaded content in `media/`) → `{% smartpath %}` tag:

```html
{% load smartpath %}

<img src="{% smartpath 'banner.jpg' %}" alt="Banner">
<a href="{% smartpath 'catalog.pdf' %}">Download Catalog</a>
```

> **Why two different tags?**
>
> `{% static %}` is Django's built-in tag for files in `STATICFILES_DIRS` / `STATIC_ROOT`.
> It works with `collectstatic` and CDN backends out of the box.
>
> `{% smartpath %}` handles files in `MEDIA_ROOT` (user-uploaded files), which
> `{% static %}` does not cover. It resolves filenames at render time by searching
> `MEDIA_ROOT`, `STATICFILES_DIRS`, and `STATIC_ROOT`.

### Searching and filtering

The search box filters on:
- **Filename** — type `logo` to find `logo.png`, `logo-2x.png`, etc.
- **Relative path** — type `images/` to see everything inside the `images/` folder
- **URL** — type `/media/` to see only media files
- **Extension** — type `.css` to see all stylesheets

### Dynamic scanning (no cache flush needed)

Every time you open the picker, the CLI rescans the filesystem. If you add a new image to `media/images/` in your terminal, it will appear the next time you press `Ctrl+Shift+D`. No restart, no cache flush.

---

## The `{% smartpath %}` Template Tag

### Setup

Add `django_smartpath` to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_smartpath',
]
```

### Usage in templates

```html
{% load smartpath %}

<img src="{% smartpath 'logo.png' %}" alt="Logo">
<link rel="stylesheet" href="{% smartpath 'styles.css' %}">
<script src="{% smartpath 'app.js' %}"></script>
<a href="{% smartpath 'catalog.pdf' %}">Download</a>
```

### How it resolves filenames

The tag searches in this order:

1. `MEDIA_ROOT` (recursive)
2. Each directory in `STATICFILES_DIRS` (recursive)
3. `STATIC_ROOT` (recursive)
4. `BASE_DIR/static/` (project-level static folder)

The first match wins. It returns the full Django URL, e.g. `/media/images/logo.png` or `/static/css/styles.css`.

If the file is **not found**, it returns `#smartpath-not-found:filename` so you can spot missing files easily in the browser dev tools.

### When to use `{% smartpath %}` vs `{% static %}`

| Use `{% static %}` when… | Use `{% smartpath %}` when… |
|--------------------------|------------------------------|
| File lives in `static/` or `STATICFILES_DIRS` | File lives in `media/` or `MEDIA_ROOT` |
| You want CDN / collectstatic integration | You need runtime lookup by filename only |
| You know the exact relative path | You only know the filename |

---

## The `{% static %}` Tag (for static files)

Django SmartPath automatically inserts the standard `{% static %}` tag for files found in your `static/` folders. This is Django's built-in tag — no extra setup beyond `{% load static %}` is needed.

```html
{% load static %}

<!-- Inserted by Django SmartPath when you pick a static file: -->
<link rel="stylesheet" href="{% static 'css/main.css' %}">
<img src="{% static 'images/hero.jpg' %}" alt="Hero">
```

The relative path inserted is relative to the root of your `static/` directory, matching how Django's `collectstatic` works.

---

## CLI Reference

The CLI is used directly by IDE plugins. You can also run it yourself for debugging or scripting.

### `django-smartpath scan`

Scan the Django project and list all media/static files.

```bash
# Scan from current directory
django-smartpath scan

# Scan from a specific file (IDE plugins use this)
django-smartpath scan --path /path/to/myproject/store/views.py

# Filter by name or path
django-smartpath scan --query logo
django-smartpath scan --query .css

# Output format
django-smartpath scan --format full      # full JSON (default)
django-smartpath scan --format minimal   # compact JSON array
```

**Example output (`--format full`):**
```json
{
  "files": [
    {
      "name": "logo.png",
      "relative_path": "images/logo.png",
      "absolute_path": "/home/user/myproject/media/images/logo.png",
      "url": "/media/images/logo.png",
      "type": "media",
      "extension": "png",
      "size": 46382,
      "template_tag": "{% smartpath 'logo.png' %}",
      "python_string": "\"/media/images/logo.png\""
    }
  ],
  "meta": {
    "project_root": "/home/user/myproject",
    "settings_file": "/home/user/myproject/myproject/settings.py",
    "media_url": "/media/",
    "static_url": "/static/",
    "scanned_dirs": [...],
    "total_files": 1
  }
}
```

### `django-smartpath check`

Check if the current directory is a Django project and show what was found.

```bash
django-smartpath check --path /path/to/project
```

```json
{
  "is_django_project": true,
  "project_root": "/home/user/myproject",
  "settings_file": "/home/user/myproject/myproject/settings.py",
  "media_root": "/home/user/myproject/media",
  "static_root": null
}
```

### `django-smartpath version`

```bash
django-smartpath version
# django-smartpath 1.0.0
```

---

## Settings & Configuration

### VS Code settings

Open VS Code settings (`Ctrl+,`) and search for `djangoSmartpath`:

| Setting | Default | Description |
|---------|---------|-------------|
| `djangoSmartpath.pythonPath` | `""` | Path to the Python executable with `django-smartpath` installed. Leave empty to auto-detect from the Python extension or `PATH`. |
| `djangoSmartpath.showFullPath` | `false` | Show the absolute filesystem path alongside the URL in the picker. |
| `djangoSmartpath.autoDetectFileType` | `true` | Automatically use `{% static %}` / `{% smartpath %}` in HTML and URL string in Python. |
| `djangoSmartpath.insertFormatPython` | `"url_string"` | Python insertion format: `url_string` inserts `"/media/file.png"`, `os_path` inserts the absolute filesystem path. |

**Example `.vscode/settings.json`:**
```json
{
  "djangoSmartpath.pythonPath": "/home/user/myproject/venv/bin/python",
  "djangoSmartpath.showFullPath": false
}
```

### Django settings required

```python
# settings.py

INSTALLED_APPS = [
    ...
    'django_smartpath',   # required for {% smartpath %} template tag
]

# Optional but recommended — SmartPath reads these to build correct URLs
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

---

## Troubleshooting

### "django-smartpath CLI failed: stdout maxBuffer length exceeded"

Your project has a very large number of files. The extension has a 50 MB buffer for CLI output. If you hit this:

1. **Use `--query` to filter**: configure `djangoSmartpath.queryOnOpen` to pre-filter results.
2. **Point to a venv Python**: set `djangoSmartpath.pythonPath` to a Python inside your virtual environment, not a global Python that may have many packages generating paths.
3. **Check your project root**: run `django-smartpath check --path .` to confirm the correct root is detected. If a parent directory is being scanned, move `manage.py` or the scan will be too broad.

### "No media/static files found"

1. Does your project have a `manage.py` file? SmartPath uses this to find the project root.
2. Do you have a `media/` or `static/` folder at the project root, or inside an app?
3. Run `django-smartpath scan` in the terminal to see what's detected and why.

```bash
cd /path/to/myproject
django-smartpath scan
# If this returns files, VS Code should too.
# If not, check that manage.py exists.
```

### "No module named django_smartpath"

The IDE plugin is using a different Python than where you installed the library.

```bash
# Find out which Python VS Code is using:
# Look in Output panel → Django SmartPath, or run:
which python3

# Install into that specific Python:
/path/to/that/python -m pip install django-smartpath

# Or set it explicitly in settings:
# "djangoSmartpath.pythonPath": "/path/to/venv/bin/python"
```

### Image preview doesn't appear

- Image preview requires the image to exist on disk at `absolute_path`
- SVG files are supported but may not render in all VS Code versions
- The preview panel opens *beside* your editor — check if it opened in a tab you can't see

### Wrong URL prefix (e.g., `/static/` instead of `/media/`)

SmartPath reads `MEDIA_URL` and `STATIC_URL` from your `settings.py`. If the URLs are set dynamically (e.g., via environment variables), SmartPath may fall back to the defaults (`/media/` and `/static/`). Set them as string literals in `settings.py` for best results.

---

## Project Structure

```
django-smartpath/
├── pip-library/                    ← Published to PyPI
│   ├── django_smartpath/
│   │   ├── scanner.py              ← Core file scanner
│   │   ├── cli.py                  ← CLI entry point
│   │   ├── apps.py
│   │   └── templatetags/
│   │       └── smartpath.py        ← {% smartpath %} tag
│   └── tests/
│
├── vscode-extension/               ← Published to VS Code Marketplace
│   ├── src/extension.ts            ← Main extension + image preview
│   └── package.json
│
├── pycharm-plugin/                 ← Published to JetBrains Marketplace
└── sublime-plugin/                 ← Published to Package Control
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
