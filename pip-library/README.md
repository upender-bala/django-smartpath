# django-smartpath

**Smart media/static file path insertion for Django — works in VS Code, PyCharm, and Sublime Text.**

Stop manually copying file paths. Press a keyboard shortcut inside your editor, search your Django project's media and static files, click one, and the correct Django URL or template tag is inserted **directly at your cursor** — no terminal, no browser, no copy-pasting.

---

## How it works

```
Developer presses Ctrl+Shift+D
         │
         ▼
IDE Plugin invokes:
  python -m django_smartpath.cli scan --path /current/file.py
         │
         ▼
CLI walks up directory tree → finds manage.py → scans media/ and static/
         │
         ▼
Returns JSON list of all files with their Django URLs
         │
         ▼
IDE shows searchable popup
         │
         ▼
Developer picks "logo.png"
         │
    ┌────┴────┐
    │         │
  .py file  .html file
    │         │
    ▼         ▼
"/media/   {% smartpath
images/      'logo.png'
logo.png"    %}
```

---

## Quick Start

### Step 1 — Install the Python library

```bash
pip install django-smartpath
```

### Step 2 — Add to Django INSTALLED_APPS (for template tag support)

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_smartpath',
]
```

### Step 3 — Install your IDE plugin

| IDE | Install |
|-----|---------|
| **VS Code** | Search `Django SmartPath` in the Extensions panel, or [install from marketplace](https://marketplace.visualstudio.com/items?itemName=django-smartpath.django-smartpath) |
| **PyCharm** | Settings → Plugins → Marketplace → search `Django SmartPath` |
| **Sublime Text** | Package Control → Install Package → `Django SmartPath` |

### Step 4 — Use it

1. Open any `.py` or `.html` file inside your Django project
2. Place your cursor where you want the path inserted
3. Press **Ctrl+Shift+D** (or **Cmd+Shift+D** on macOS)
4. Type to filter, press Enter to insert

---

## What gets inserted

### In `.py` files (views, models, etc.)

```python
# You press Ctrl+Shift+D, pick "logo.png"
# This gets inserted at your cursor:
"/media/images/logo.png"

# Example in context:
def my_view(request):
    logo_url = "/media/images/logo.png"   # ← inserted by SmartPath
    return render(request, 'index.html', {'logo': logo_url})
```

### In `.html` Django template files

```html
<!-- You press Ctrl+Shift+D, pick "logo.png" -->
<!-- This gets inserted at your cursor: -->
{% smartpath 'logo.png' %}

<!-- Example in context: -->
{% load smartpath %}
<img src="{% smartpath 'logo.png' %}">
<link rel="stylesheet" href="{% smartpath 'styles.css' %}">
```

The `{% smartpath %}` template tag resolves the filename at **render time** by searching your `MEDIA_ROOT` and `STATICFILES_DIRS`, so it always points to the correct URL even if files move between folders.

---

## CLI Reference

The `django-smartpath` command is what IDE plugins call internally. You can also use it directly:

```bash
# Scan from current directory
django-smartpath scan

# Scan from a specific file (as if you are editing it)
django-smartpath scan --path /home/user/myproject/myapp/views.py

# Filter results
django-smartpath scan --path /home/user/myproject --query logo

# Minimal output (faster, less data)
django-smartpath scan --path /home/user/myproject --format minimal

# Check if a path is inside a Django project
django-smartpath check --path /home/user/myproject/views.py

# Print version
django-smartpath version
```

### Example JSON output

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
      "size": 24576,
      "python_string": "\"/media/images/logo.png\"",
      "template_tag": "{% smartpath 'logo.png' %}"
    },
    {
      "name": "styles.css",
      "relative_path": "css/styles.css",
      "absolute_path": "/home/user/myproject/static/css/styles.css",
      "url": "/static/css/styles.css",
      "type": "static",
      "extension": "css",
      "size": 8192,
      "python_string": "\"/static/css/styles.css\"",
      "template_tag": "{% smartpath 'styles.css' %}"
    }
  ],
  "meta": {
    "project_root": "/home/user/myproject",
    "settings_file": "/home/user/myproject/myproject/settings.py",
    "media_url": "/media/",
    "static_url": "/static/",
    "scanned_dirs": [
      {"path": "/home/user/myproject/media", "type": "media", "url_prefix": "/media/"},
      {"path": "/home/user/myproject/static", "type": "static", "url_prefix": "/static/"}
    ],
    "total_files": 2
  }
}
```

---

## Template Tag

After adding `django_smartpath` to `INSTALLED_APPS`, load and use the tag:

```html
{% load smartpath %}

<!-- Images -->
<img src="{% smartpath 'logo.png' %}" alt="Logo">

<!-- Stylesheets -->
<link rel="stylesheet" href="{% smartpath 'styles.css' %}">

<!-- JavaScript -->
<script src="{% smartpath 'app.js' %}"></script>

<!-- Any file -->
<a href="{% smartpath 'report.pdf' %}">Download PDF</a>
```

The tag searches `MEDIA_ROOT`, `STATICFILES_DIRS`, `STATIC_ROOT`, and any `static/` subfolder in your project root, in that order. Returns the URL of the first matching file.

---

## Project structure support

django-smartpath automatically finds:

```
myproject/                  ← found via manage.py
├── manage.py
├── myproject/
│   └── settings.py         ← reads MEDIA_URL and STATIC_URL
├── media/                  ← ✅ scanned (MEDIA_ROOT)
│   ├── images/
│   │   ├── logo.png
│   │   └── banner.jpg
│   └── documents/
│       └── report.pdf
├── static/                 ← ✅ scanned (project-level)
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── myapp/
│   └── static/             ← ✅ scanned (app-level static)
│       └── myapp/
│           └── icon.svg
└── otherapp/
    └── static/             ← ✅ scanned (app-level static)
        └── otherapp/
            └── data.json
```

---

## Configuration

### VS Code settings (`settings.json`)

```json
{
    // Path to Python with django-smartpath installed (auto-detected if empty)
    "djangoSmartpath.pythonPath": "",

    // Show full absolute path alongside URL in picker
    "djangoSmartpath.showFullPath": false,

    // Auto-detect .py vs .html and insert appropriate format
    "djangoSmartpath.autoDetectFileType": true,

    // For Python files: insert URL string or OS path
    "djangoSmartpath.insertFormatPython": "url_string"
}
```

### PyCharm

No configuration needed. Uses Python from the project SDK automatically.

To set a custom Python: **Settings → Tools → Django SmartPath → Python Path**

### Sublime Text (`DjangoSmartPath.sublime-settings`)

Access via **Preferences → Package Settings → Django SmartPath → Settings**

```json
{
    // Path to Python executable (auto-detected if empty)
    "python_path": "",

    // Show [MEDIA] / [STATIC] labels in picker
    "show_file_type": true
}
```

---

## Virtualenv / Conda support

If you use a virtual environment, make sure to either:

**Option A** — Activate your venv before opening your IDE:
```bash
source .venv/bin/activate  # or: conda activate myenv
code .                     # or: pycharm ., subl .
```

**Option B** — Set the Python path in your IDE plugin settings to point to the venv Python directly:
```
# VS Code settings.json
"djangoSmartpath.pythonPath": "/home/user/myproject/.venv/bin/python"

# Sublime Text settings
"python_path": "/home/user/myproject/.venv/bin/python"
```

---

## Supported file types

| Category | Extensions |
|----------|-----------|
| Images | `.png` `.jpg` `.jpeg` `.gif` `.webp` `.svg` `.ico` `.bmp` `.tiff` |
| Stylesheets | `.css` `.scss` `.sass` `.less` |
| JavaScript | `.js` `.ts` `.jsx` `.tsx` |
| Fonts | `.woff` `.woff2` `.ttf` `.eot` `.otf` |
| Documents | `.pdf` `.txt` |
| Audio/Video | `.mp3` `.mp4` `.wav` `.ogg` `.webm` `.avi` `.mov` |
| Data | `.json` `.xml` `.csv` |
| Archives | `.zip` `.tar` `.gz` |

---

## Keyboard shortcuts

| OS | Shortcut |
|----|---------|
| Windows / Linux | **Ctrl + Shift + D** |
| macOS | **Cmd + Shift + D** |

Customizable in each IDE's keyboard shortcut settings.

---

## Requirements

- Python 3.8+
- Django 3.2, 4.0, 4.1, 4.2, or 5.0
- No other Python dependencies

---

## License

MIT — see [LICENSE](LICENSE)
