# django-smartpath — Complete Publishing & Testing Guide

This guide walks you through:
1. Publishing the pip library to PyPI
2. Publishing the VS Code extension to the VS Code Marketplace
3. Publishing the PyCharm plugin to JetBrains Marketplace
4. Publishing the Sublime Text plugin to Package Control
5. End-to-end testing from a brand new Django project

---

## PART 1 — Publishing the pip library to PyPI

### Prerequisites

```bash
pip install --upgrade build twine
```

You also need a PyPI account at https://pypi.org/account/register/

### Step 1 — Build the distribution

```bash
cd django-smartpath/pip-library/

# Build both wheel and source distribution
python -m build

# You should now see:
# dist/django_smartpath-1.0.0-py3-none-any.whl
# dist/django-smartpath-1.0.0.tar.gz
```

### Step 2 — Test on TestPyPI first (recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ django-smartpath

# Quick smoke test
django-smartpath version
# Should print: django-smartpath 1.0.0
```

### Step 3 — Upload to real PyPI

```bash
python -m twine upload dist/*
# Enter your PyPI username and password (or use API token)
```

### Step 4 — Verify the live install

```bash
# In a fresh virtual environment:
python -m venv test_env
source test_env/bin/activate   # Windows: test_env\Scripts\activate

pip install django-smartpath
django-smartpath version
# Output: django-smartpath 1.0.0

django-smartpath --help
# Shows full help with all commands
```

### Using an API token (recommended over password)

1. Go to https://pypi.org/manage/account/token/
2. Create a token scoped to the `django-smartpath` project
3. Create `~/.pypirc`:

```ini
[pypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmcA...  (your token here)
```

Then `twine upload dist/*` will use it automatically.

### Automating with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Build
        run: |
          pip install build
          python -m build
        working-directory: pip-library
      - name: Publish
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: pip-library/dist/
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

---

## PART 2 — Publishing the VS Code Extension

### Prerequisites

```bash
npm install -g @vscode/vsce
```

You need a Microsoft account and a publisher profile at:
https://marketplace.visualstudio.com/manage

### Step 1 — Create a publisher

1. Go to https://marketplace.visualstudio.com/manage
2. Sign in with your Microsoft account
3. Click "Create publisher"
4. Name it `django-smartpath` (must match `publisher` in `package.json`)

### Step 2 — Get a Personal Access Token

1. Go to https://dev.azure.com
2. Click your profile → Personal access tokens
3. Create new token:
   - Name: `vsce-publish`
   - Organization: All accessible organizations
   - Scopes: Marketplace → Manage
4. Copy the token

### Step 3 — Log in with vsce

```bash
cd django-smartpath/vscode-extension/
npm install
vsce login django-smartpath
# Paste your Personal Access Token when prompted
```

### Step 4 — Add the extension icon

Create or place a 128×128 PNG icon at:
```
vscode-extension/images/icon.png
```

You can use any Django-themed icon. A simple green Django logo on dark background works well.

### Step 5 — Compile TypeScript

```bash
cd vscode-extension/
npm install
npm run compile
# This creates out/extension.js
```

### Step 6 — Package the extension

```bash
vsce package
# Creates: django-smartpath-1.0.0.vsix
```

### Step 7 — Test locally before publishing

```bash
# Install in VS Code
code --install-extension django-smartpath-1.0.0.vsix

# Open a Django project
# Press Ctrl+Shift+D
# Verify the popup appears
```

### Step 8 — Publish to marketplace

```bash
vsce publish
# Or: vsce publish minor   (bumps minor version)
# Or: vsce publish patch   (bumps patch version)
```

After a few minutes, the extension will be live at:
`https://marketplace.visualstudio.com/items?itemName=django-smartpath.django-smartpath`

### Automating with GitHub Actions

```yaml
name: Publish VS Code Extension

on:
  push:
    tags:
      - 'vscode-v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install and compile
        run: |
          npm install
          npm run compile
        working-directory: vscode-extension
      - name: Publish
        run: npx vsce publish --pat ${{ secrets.VSCE_PAT }}
        working-directory: vscode-extension
```

---

## PART 3 — Publishing the PyCharm Plugin

### Prerequisites

- JDK 17+ installed
- Gradle (included via Gradle wrapper in the plugin)
- JetBrains Marketplace account at https://plugins.jetbrains.com/

### Step 1 — Create a JetBrains Marketplace account

1. Register at https://plugins.jetbrains.com/
2. Go to Developer → Upload plugin
3. Note your vendor/publisher details

### Step 2 — Get a Publish Token

1. Go to https://plugins.jetbrains.com/author/me/tokens
2. Create a new permanent token
3. Copy it — you'll use it as `PUBLISH_TOKEN`

### Step 3 — Build the plugin

```bash
cd django-smartpath/pycharm-plugin/

# Build the plugin JAR
./gradlew buildPlugin

# The plugin zip will be at:
# build/distributions/django-smartpath-1.0.0.zip
```

### Step 4 — Test locally in PyCharm

```bash
# Run PyCharm sandbox with plugin installed
./gradlew runIde
```

This opens a fresh PyCharm instance with your plugin. Test by:
1. Opening a Django project
2. Pressing Ctrl+Shift+D
3. Verifying the file picker appears and inserts correctly

### Step 5 — Sign the plugin (required for Marketplace)

```bash
# Install the JetBrains Plugin Signer
# First, generate a certificate:
./gradlew signPlugin \
  -Pcertificate.chain="$(cat chain.crt)" \
  -Pprivate.key="$(cat private.pem)" \
  -Pprivate.key.password="your_password"
```

See JetBrains documentation for generating certificates:
https://plugins.jetbrains.com/docs/intellij/plugin-signing.html

### Step 6 — Publish to JetBrains Marketplace

```bash
./gradlew publishPlugin -Ppublish.token="your_token_here"
```

Or manually upload at:
https://plugins.jetbrains.com/plugin/add

### Automating with GitHub Actions

```yaml
name: Publish PyCharm Plugin

on:
  push:
    tags:
      - 'pycharm-v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
      - name: Publish
        run: ./gradlew publishPlugin
        working-directory: pycharm-plugin
        env:
          PUBLISH_TOKEN: ${{ secrets.JETBRAINS_TOKEN }}
          CERTIFICATE_CHAIN: ${{ secrets.CERTIFICATE_CHAIN }}
          PRIVATE_KEY: ${{ secrets.PRIVATE_KEY }}
          PRIVATE_KEY_PASSWORD: ${{ secrets.PRIVATE_KEY_PASSWORD }}
```

---

## PART 4 — Publishing the Sublime Text Plugin to Package Control

Package Control works differently — it pulls from your GitHub repository, not from an uploaded file. You do NOT submit a binary; instead you submit a repository URL.

### Step 1 — Create the GitHub repository

1. Create a new GitHub repo named `sublime-django-smartpath`
2. Push all files from `django-smartpath/sublime-plugin/` to the repo root

```bash
cd django-smartpath/sublime-plugin/
git init
git add .
git commit -m "Initial release v1.0.0"
git remote add origin https://github.com/YOUR_USERNAME/sublime-django-smartpath.git
git push -u origin main
```

### Step 2 — Tag a release

```bash
git tag v1.0.0
git push origin v1.0.0
```

### Step 3 — Submit to Package Control

1. Fork the Package Control channel repository:
   https://github.com/wbond/package_control_channel

2. Add your package to `repository/d.json` (alphabetical by name):

```json
{
    "name": "Django SmartPath",
    "details": "https://github.com/YOUR_USERNAME/sublime-django-smartpath",
    "labels": ["python", "django", "productivity"],
    "releases": [
        {
            "sublime_text": ">=3000",
            "tags": true
        }
    ]
}
```

3. Create a Pull Request to the main channel repository

4. The Package Control team reviews and merges (usually within a few days)

### Step 4 — Verify the submission

Once merged, users can install via:
```
Package Control: Install Package → Django SmartPath
```

---

## PART 5 — End-to-End Testing Walkthrough

Follow these steps exactly to test everything from scratch on a brand new machine.

---

### STEP 1 — Create a brand new Django project

```bash
# Create a fresh virtual environment
python -m venv smartpath-test-env
source smartpath-test-env/bin/activate   # Windows: smartpath-test-env\Scripts\activate

# Install Django
pip install django

# Create a new Django project
django-admin startproject myshop
cd myshop

# Create an app
python manage.py startapp store

# Verify it works
python manage.py runserver
# Should show: Starting development server at http://127.0.0.1:8000/
# Press Ctrl+C to stop
```

---

### STEP 2 — Install django-smartpath from PyPI

```bash
# You must be in the same virtual environment
pip install django-smartpath

# Verify installation
django-smartpath version
# Expected output: django-smartpath 1.0.0

django-smartpath --help
# Expected: shows scan, check, version subcommands
```

---

### STEP 3 — Configure Django settings

Open `myshop/myshop/settings.py` and update:

```python
import os

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps ...
    'store',
    'django_smartpath',        # ← ADD THIS
]

# Add at the bottom:
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

---

### STEP 4 — Add image and CSS files to media and static folders

```bash
# Still inside myshop/ directory

# Create the folder structure
mkdir -p media/images
mkdir -p media/documents
mkdir -p static/css
mkdir -p static/js
mkdir -p static/fonts

# Add fake image files
echo "fake png content" > media/images/logo.png
echo "fake jpg content" > media/images/banner.jpg
echo "fake gif content" > media/images/loading.gif
echo "fake pdf content" > media/documents/catalog.pdf

# Add fake CSS and JS files
echo "body { margin: 0; }" > static/css/styles.css
echo "body { color: red; }" > static/css/theme.css
echo 'console.log("hello");' > static/js/app.js
echo 'console.log("utils");' > static/js/utils.js

# Add an app-level static file
mkdir -p store/static/store/images
echo "fake icon" > store/static/store/images/product-icon.svg
```

---

### STEP 5 — Test the CLI directly (before using IDE plugin)

```bash
# Make sure you are in the myshop/ directory
cd myshop/

# Scan the project from the root
django-smartpath scan

# Expected: JSON output listing all files you just created.
# You should see logo.png, banner.jpg, styles.css, app.js, etc.
# Each file has: name, url, type, python_string, template_tag

# Test filtering
django-smartpath scan --query logo
# Expected: only logo.png appears

django-smartpath scan --query css
# Expected: styles.css and theme.css appear

# Test from a specific file path (simulates VS Code calling it)
django-smartpath scan --path /absolute/path/to/myshop/store/views.py

# Test the check command
django-smartpath check --path .
# Expected JSON: {"is_django_project": true, "project_root": "...", ...}

# Test minimal format (what IDE plugins use)
django-smartpath scan --format minimal
# Expected: compact JSON array
```

---

### STEP 6 — Install the VS Code extension

1. Open VS Code
2. Press `Ctrl+Shift+X` to open Extensions panel
3. Search for: `Django SmartPath`
4. Click **Install**
5. Reload VS Code when prompted

**Alternative — install from .vsix file:**
```bash
code --install-extension django-smartpath-1.0.0.vsix
```

---

### STEP 7 — Test in VS Code — Python file

1. Open VS Code
2. Open the `myshop/` folder: `File → Open Folder → select myshop`
3. Open `store/views.py`
4. Add some content so the file is not empty:
   ```python
   from django.shortcuts import render

   def product_list(request):
       # put cursor on the next line:
       return render(request, 'store/list.html', {})
   ```
5. Place your cursor on the empty line between the function definition and return
6. Press **Ctrl+Shift+D** (or **Cmd+Shift+D** on macOS)

**Expected result:**
- A popup appears immediately
- The title shows: `Django SmartPath — Python (inserts URL string)`
- You can see all files: logo.png, banner.jpg, styles.css, app.js, etc.
- Each item shows: the filename, its URL, and a small preview of what will be inserted

7. Type `logo` in the search box
8. You should see only `logo.png` in the filtered results
9. Press **Enter** or click on it

**Expected result:**
```python
def product_list(request):
    "/media/images/logo.png"    # ← this was inserted at your cursor
    return render(request, 'store/list.html', {})
```

The text `"/media/images/logo.png"` appears **exactly where your cursor was**, with no extra steps.

---

### STEP 8 — Test in VS Code — HTML template file

1. Create a template directory and file:
   ```bash
   mkdir -p store/templates/store
   touch store/templates/store/list.html
   ```

2. Open `store/templates/store/list.html` in VS Code
3. Add:
   ```html
   {% load smartpath %}
   <!DOCTYPE html>
   <html>
   <head>
       <!-- Put cursor here -->
   </head>
   <body>
       <!-- Put cursor here -->
   </body>
   </html>
   ```
4. Place cursor on the `<!-- Put cursor here -->` line inside `<head>`
5. Press **Ctrl+Shift+D**

**Expected result:**
- Popup title shows: `Django SmartPath — Template (inserts {% smartpath %})`
- Same file list appears

6. Type `styles` to filter, select `styles.css`

**Expected result:**
```html
<head>
    {% smartpath 'styles.css' %}    <!-- ← inserted at cursor -->
</head>
```

7. Repeat in the `<body>` section, pick `logo.png`

**Expected result:**
```html
<body>
    {% smartpath 'logo.png' %}    <!-- ← inserted at cursor -->
</body>
```

---

### STEP 9 — Test that new files appear instantly (dynamic scanning)

1. Keep VS Code open on `views.py`
2. In your terminal (without restarting anything):
   ```bash
   echo "new image" > media/images/new-product.webp
   ```
3. Go back to VS Code
4. Press **Ctrl+Shift+D** again

**Expected result:** `new-product.webp` appears in the list immediately.
No restart. No cache flush. It's there.

---

### STEP 10 — Test the template tag actually works at runtime

1. Update `store/views.py`:
   ```python
   from django.shortcuts import render

   def product_list(request):
       return render(request, 'store/list.html', {})
   ```

2. Update `store/templates/store/list.html`:
   ```html
   {% load smartpath %}
   <!DOCTYPE html>
   <html>
   <head>
       <link rel="stylesheet" href="{% smartpath 'styles.css' %}">
   </head>
   <body>
       <img src="{% smartpath 'logo.png' %}" alt="Logo">
       <h1>It works!</h1>
   </body>
   </html>
   ```

3. Update `myshop/urls.py`:
   ```python
   from django.contrib import admin
   from django.urls import path
   from django.conf import settings
   from django.conf.urls.static import static
   from store import views

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', views.product_list, name='product_list'),
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

4. Run the server:
   ```bash
   python manage.py runserver
   ```

5. Open http://127.0.0.1:8000/ in your browser

**Expected result:**
- The page loads without errors
- View source shows: `<link rel="stylesheet" href="/static/css/styles.css">`
- And: `<img src="/media/images/logo.png" alt="Logo">`

The `{% smartpath %}` tag resolved the filenames to their correct Django URLs at render time.

---

## Troubleshooting

### "django-smartpath not installed" error in IDE

```bash
# Check which Python the IDE is using
which python   # or: where python on Windows

# Install in that specific Python
/path/to/that/python -m pip install django-smartpath

# Or set pythonPath in your IDE settings to point to
# the Python where you installed django-smartpath
```

### No files appear in popup

```bash
# Run the CLI manually to diagnose:
django-smartpath scan --path /path/to/your/views.py

# Check:
# 1. Is there a manage.py in your project root?
# 2. Do you have a media/ or static/ folder?
# 3. Are there files in those folders?

django-smartpath check --path /path/to/your/views.py
# This tells you if the project root was found
```

### VS Code extension not activating

- The extension activates for `.py`, `.html`, `.djhtml`, `.jinja-html` files
- Make sure you have one of these file types open
- Check the VS Code Output panel → select "Django SmartPath" from dropdown

### PyCharm popup not showing

- Make sure `pip install django-smartpath` was run in the Python interpreter
  your project is configured to use (check Settings → Python Interpreter)
- Try running `django-smartpath scan` in PyCharm's built-in terminal

### Sublime Text plugin not triggering

- Make sure Package Control installation completed without errors
- Check Sublime Text console (View → Show Console) for Python errors
- Verify `python_path` in DjangoSmartPath settings points to your Python

---

## Running the test suite

```bash
cd django-smartpath/pip-library/

pip install pytest pytest-django django

pytest tests/ -v

# Expected output:
# tests/test_scanner.py::TestFindDjangoRoot::test_finds_root_from_file_in_project PASSED
# tests/test_scanner.py::TestFindDjangoRoot::test_finds_root_from_project_dir PASSED
# tests/test_scanner.py::TestFindDjangoRoot::test_returns_none_outside_django_project PASSED
# tests/test_scanner.py::TestScanDirectory::test_scans_media_folder PASSED
# tests/test_scanner.py::TestScanDirectory::test_file_has_required_fields PASSED
# tests/test_scanner.py::TestScanDirectory::test_url_is_correct_format PASSED
# tests/test_scanner.py::TestScanDirectory::test_template_tag_format PASSED
# tests/test_scanner.py::TestScanDirectory::test_returns_empty_for_nonexistent_dir PASSED
# tests/test_scanner.py::TestScanProject::test_scans_full_project PASSED
# tests/test_scanner.py::TestScanProject::test_finds_both_media_and_static PASSED
# tests/test_scanner.py::TestGetFilesJson::test_returns_valid_json PASSED
# tests/test_scanner.py::TestGetFilesJson::test_query_filters_results PASSED
# tests/test_scanner.py::TestGetFilesJson::test_empty_query_returns_all PASSED
#
# 13 passed in 0.XXs
```

---

## Repository structure

```
django-smartpath/
│
├── pip-library/                    # Published to PyPI as "django-smartpath"
│   ├── django_smartpath/
│   │   ├── __init__.py             # Version info
│   │   ├── scanner.py              # Core file scanner
│   │   ├── cli.py                  # CLI entry point (called by IDE plugins)
│   │   ├── apps.py                 # Django app config
│   │   └── templatetags/
│   │       ├── __init__.py
│   │       └── smartpath.py        # {% smartpath 'file.png' %} tag
│   ├── tests/
│   │   └── test_scanner.py
│   ├── README.md
│   ├── pyproject.toml
│   └── setup.py
│
├── vscode-extension/               # Published to VS Code Marketplace
│   ├── src/
│   │   └── extension.ts            # Main extension logic
│   ├── package.json                # Extension manifest
│   ├── tsconfig.json
│   └── .vscodeignore
│
├── pycharm-plugin/                 # Published to JetBrains Marketplace
│   ├── src/main/
│   │   ├── java/com/djangosmartpath/
│   │   │   └── InsertPathAction.java
│   │   └── resources/META-INF/
│   │       └── plugin.xml
│   └── build.gradle
│
└── sublime-plugin/                 # Published to Package Control
    ├── DjangoSmartPath.py          # Main plugin
    ├── Default (Windows).sublime-keymap
    ├── Default (OSX).sublime-keymap
    ├── Default (Linux).sublime-keymap
    ├── Default.sublime-commands
    ├── DjangoSmartPath.sublime-settings
    └── messages.json
```
