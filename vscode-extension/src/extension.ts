/**
 * Django SmartPath - VS Code Extension
 *
 * Main extension source file.
 * Handles the command palette trigger, calls the django-smartpath CLI,
 * shows a Quick Pick UI with image thumbnails, and inserts the selected
 * path at cursor.
 */

import * as vscode from 'vscode';
import { exec, execFile } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

interface SmartPathFile {
  name: string;
  relative_path: string;
  absolute_path: string;
  url: string;
  type: 'media' | 'static';
  extension: string;
  size: number;
  python_string: string;
  template_tag: string;
}

interface SmartPathResult {
  files: SmartPathFile[];
  meta: {
    project_root: string;
    settings_file: string | null;
    media_url: string;
    static_url: string;
    scanned_dirs: Array<{ path: string; type: string; url_prefix: string }>;
    total_files: number;
  };
}

// ─────────────────────────────────────────────
// Python path resolution
// ─────────────────────────────────────────────

async function findPython(): Promise<string> {
  const config = vscode.workspace.getConfiguration('djangoSmartpath');
  const configuredPath = config.get<string>('pythonPath');

  if (configuredPath && configuredPath.trim()) {
    return configuredPath.trim();
  }

  // Try to get from Python extension
  try {
    const pythonExt = vscode.extensions.getExtension('ms-python.python');
    if (pythonExt) {
      const api = await pythonExt.activate();
      if (api && api.settings) {
        const pythonPath = api.settings.getExecutionDetails()?.execCommand?.[0];
        if (pythonPath) return pythonPath;
      }
    }
  } catch {
    // Python extension not available or API changed
  }

  // Fallback: try common paths
  const candidates = ['python3', 'python', 'python3.exe', 'python.exe'];
  for (const candidate of candidates) {
    try {
      await execAsync(`${candidate} --version`);
      return candidate;
    } catch {
      continue;
    }
  }

  throw new Error(
    'Could not find Python. Please set "djangoSmartpath.pythonPath" in settings, ' +
    'or install the Python extension for VS Code.'
  );
}

// ─────────────────────────────────────────────
// CLI invocation
// ─────────────────────────────────────────────

async function runSmartPathCLI(
  python: string,
  currentFilePath: string,
  query: string = ''
): Promise<SmartPathResult> {
  const args = [
    '-m', 'django_smartpath.cli',
    'scan',
    '--path', currentFilePath,
    '--format', 'full',
  ];

  if (query) {
    args.push('--query', query);
  }

  try {
    const { stdout } = await execFileAsync(python, args, {
      timeout: 30000,
      // 50 MB buffer — prevents "maxBuffer length exceeded" on large projects
      maxBuffer: 50 * 1024 * 1024,
    });

    return JSON.parse(stdout);
  } catch (error: any) {
    // Detect "maxBuffer length exceeded" specifically and give a clear message
    if (error.message && error.message.includes('maxBuffer')) {
      throw new Error(
        'Project has too many files to scan. ' +
        'Try narrowing the scan or set djangoSmartpath.pythonPath to a venv with fewer files.'
      );
    }
    if (error.code === 'MODULE_NOT_FOUND' || (error.stderr && error.stderr.includes('No module named'))) {
      throw new Error(
        'django-smartpath is not installed. Run: pip install django-smartpath'
      );
    }
    throw new Error(`django-smartpath CLI failed: ${error.stderr || error.message}`);
  }
}

// ─────────────────────────────────────────────
// File type helpers
// ─────────────────────────────────────────────

const IMAGE_EXTS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico', 'bmp']);
const CSS_EXTS   = new Set(['css', 'scss', 'sass', 'less']);
const JS_EXTS    = new Set(['js', 'ts', 'jsx', 'tsx']);
const FONT_EXTS  = new Set(['woff', 'woff2', 'ttf', 'eot', 'otf']);
const DOC_EXTS   = new Set(['pdf', 'doc', 'docx', 'txt']);
const MEDIA_EXTS = new Set(['mp3', 'mp4', 'wav', 'ogg', 'webm', 'avi', 'mov']);

function getFileIcon(ext: string, type: string): string {
  if (IMAGE_EXTS.has(ext)) { return '🖼️'; }
  if (CSS_EXTS.has(ext))   { return '🎨'; }
  if (JS_EXTS.has(ext))    { return '⚡'; }
  if (FONT_EXTS.has(ext))  { return '🔤'; }
  if (DOC_EXTS.has(ext))   { return '📄'; }
  if (MEDIA_EXTS.has(ext)) { return '🎵'; }
  return type === 'media' ? '📁' : '📦';
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) { return ''; }
  if (bytes < 1024) { return `${bytes}B`; }
  if (bytes < 1024 * 1024) { return `${(bytes / 1024).toFixed(1)}KB`; }
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

// ─────────────────────────────────────────────
// Determine insert format based on current file
// ─────────────────────────────────────────────

type InsertMode = 'python' | 'html';

function detectInsertMode(document: vscode.TextDocument): InsertMode {
  const langId = document.languageId;
  const fileName = document.fileName.toLowerCase();

  if (langId === 'python' || fileName.endsWith('.py')) {
    return 'python';
  }

  if (
    langId === 'html' ||
    langId === 'django-html' ||
    langId === 'jinja-html' ||
    langId === 'jinja' ||
    fileName.endsWith('.html') ||
    fileName.endsWith('.htm') ||
    fileName.endsWith('.djhtml')
  ) {
    return 'html';
  }

  return 'python';
}

// ─────────────────────────────────────────────
// Build correct Django template tag for HTML
// ─────────────────────────────────────────────

/**
 * For HTML files we ALWAYS use {% static 'relative/path' %}.
 * HTML templates should only reference static files — media files
 * belong in Python views, not HTML templates directly.
 */
function buildHtmlInsertText(file: SmartPathFile): string {
  return `{% static '${file.relative_path}' %}`;
}

/**
 * Filter files based on insert mode:
 *   HTML mode   → static files ONLY (HTML templates use {% static %})
 *   Python mode → ALL files (both media and static are valid in Python)
 */
function filterFilesForMode(files: SmartPathFile[], insertMode: InsertMode): SmartPathFile[] {
  if (insertMode === 'html') {
    return files.filter(f => f.type === 'static');
  }
  return files;
}

// ─────────────────────────────────────────────
// Quick Pick items
// ─────────────────────────────────────────────

interface SmartPathQuickPickItem extends vscode.QuickPickItem {
  file: SmartPathFile;
  insertText: string;
}

function buildQuickPickItems(
  files: SmartPathFile[],
  insertMode: InsertMode
): SmartPathQuickPickItem[] {
  return files.map((file) => {
    const icon = getFileIcon(file.extension, file.type);
    const size = formatFileSize(file.size);
    const typeLabel = file.type === 'media' ? '$(database) media' : '$(file-code) static';
    const imageHint = IMAGE_EXTS.has(file.extension) ? '  🖼 image' : '';

    const insertText = insertMode === 'html'
      ? buildHtmlInsertText(file)
      : file.python_string;

    return {
      file,
      insertText,
      label: `${icon} ${file.name}`,
      description: file.url,
      detail: `  ${typeLabel}  •  ${file.relative_path}${size ? '  •  ' + size : ''}${imageHint}`,
    };
  });
}

// ─────────────────────────────────────────────
// Image preview webview panel
// ─────────────────────────────────────────────

function showImagePreview(
  file: SmartPathFile,
  existingPanel: vscode.WebviewPanel | undefined
): vscode.WebviewPanel | undefined {
  if (!IMAGE_EXTS.has(file.extension) || !fs.existsSync(file.absolute_path)) {
    existingPanel?.dispose();
    return undefined;
  }

  const panel = existingPanel ?? vscode.window.createWebviewPanel(
    'djangoSmartpathPreview',
    'Image Preview',
    { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true },
    {
      enableScripts: false,
      localResourceRoots: [
        vscode.Uri.file('/'),
        ...(vscode.workspace.workspaceFolders?.map(f => f.uri) ?? []),
      ],
    }
  );

  const imgUri = panel.webview.asWebviewUri(vscode.Uri.file(file.absolute_path));
  panel.title = `Preview: ${file.name}`;
  panel.webview.html = buildPreviewHtml(file, imgUri.toString(), panel.webview.cspSource);

  return panel;
}

function buildPreviewHtml(
  file: SmartPathFile,
  imgSrc: string,
  cspSource: string
): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy"
      content="default-src 'none'; img-src ${cspSource};">
<style>
  body {
    margin: 0;
    padding: 16px;
    background: #1e1e1e;
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: var(--vscode-font-family, sans-serif);
    color: #ccc;
    box-sizing: border-box;
  }
  img {
    max-width: 100%;
    max-height: 60vh;
    border: 1px solid #444;
    border-radius: 4px;
    object-fit: contain;
    display: block;
  }
  .meta {
    margin-top: 10px;
    font-size: 11px;
    color: #888;
    text-align: center;
    word-break: break-all;
  }
  .url {
    margin-top: 6px;
    font-size: 12px;
    color: #9cdcfe;
    font-family: monospace;
    text-align: center;
  }
</style>
</head>
<body>
  <img src="${imgSrc}" alt="${file.name}" />
  <div class="meta">${file.name}&nbsp;•&nbsp;${formatFileSize(file.size) || '?'}</div>
  <div class="url">${file.url}</div>
</body>
</html>`;
}

// ─────────────────────────────────────────────
// Main command: insertPath
// ─────────────────────────────────────────────

async function insertPath(context: vscode.ExtensionContext) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('Django SmartPath: No active editor found.');
    return;
  }

  const document = editor.document;
  const currentFilePath = document.fileName;
  const insertMode = detectInsertMode(document);

  let python: string;
  try {
    python = await findPython();
  } catch (err: any) {
    vscode.window.showErrorMessage(`Django SmartPath: ${err.message}`);
    return;
  }

  // Show loading quick pick
  const quickPick = vscode.window.createQuickPick<SmartPathQuickPickItem>();

  quickPick.title = insertMode === 'html'
    ? "Django SmartPath — HTML  (static files only → {% static 'relative/path' %})"
    : 'Django SmartPath — Python (inserts URL string)';

  quickPick.placeholder = 'Type to filter files... (scanning project)';
  quickPick.matchOnDescription = true;
  quickPick.matchOnDetail = true;
  quickPick.busy = true;
  quickPick.items = [];
  quickPick.show();

  // Initial scan
  let allFiles: SmartPathFile[] = [];
  try {
    const result = await runSmartPathCLI(python, currentFilePath);
    // Filter: HTML mode shows only static files; Python mode shows all files
    allFiles = filterFilesForMode(result.files, insertMode);

    if (allFiles.length === 0) {
      quickPick.busy = false;
      if (insertMode === 'html') {
        quickPick.placeholder = 'No static files found. Check STATICFILES_DIRS in settings.py.';
      } else {
        quickPick.placeholder = 'No media/static files found. Make sure you are in a Django project.';
      }
    } else {
      quickPick.busy = false;
      const modeLabel = insertMode === 'html' ? 'static' : 'media+static';
      quickPick.placeholder = `Search ${allFiles.length} ${modeLabel} files... (${result.meta.project_root})`;
      quickPick.items = buildQuickPickItems(allFiles, insertMode);
    }
  } catch (err: any) {
    quickPick.hide();
    vscode.window.showErrorMessage(`Django SmartPath: ${err.message}`);
    return;
  }

  // Image preview panel (shown beside the editor when hovering an image item)
  let previewPanel: vscode.WebviewPanel | undefined;

  quickPick.onDidChangeActive((items) => {
    const active = items[0];
    if (!active) {
      previewPanel?.dispose();
      previewPanel = undefined;
      return;
    }
    const newPanel = showImagePreview(active.file, previewPanel);
    if (newPanel !== previewPanel) {
      previewPanel = newPanel;
      previewPanel?.onDidDispose(() => { previewPanel = undefined; });
    }
  });

  // Handle selection
  quickPick.onDidAccept(() => {
    const selected = quickPick.selectedItems[0];
    previewPanel?.dispose();
    previewPanel = undefined;
    quickPick.hide();

    if (!selected) { return; }

    editor.edit((editBuilder) => {
      for (const selection of editor.selections) {
        editBuilder.replace(selection, selected.insertText);
      }
    });

    vscode.window.setStatusBarMessage(
      `✓ Django SmartPath inserted: ${selected.insertText}`,
      3000
    );
  });

  quickPick.onDidHide(() => {
    previewPanel?.dispose();
    previewPanel = undefined;
    quickPick.dispose();
  });
}

// ─────────────────────────────────────────────
// Refresh cache command
// ─────────────────────────────────────────────

async function refreshCache(context: vscode.ExtensionContext) {
  vscode.window.showInformationMessage(
    'Django SmartPath: Cache refreshed. Files will be rescanned on next use.'
  );
}

// ─────────────────────────────────────────────
// Extension activation
// ─────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
  console.log('Django SmartPath extension is now active.');

  const insertPathCmd = vscode.commands.registerCommand(
    'django-smartpath.insertPath',
    () => insertPath(context)
  );

  const refreshCacheCmd = vscode.commands.registerCommand(
    'django-smartpath.refreshCache',
    () => refreshCache(context)
  );

  context.subscriptions.push(insertPathCmd, refreshCacheCmd);

  const hasShownWelcome = context.globalState.get('hasShownWelcome', false);
  if (!hasShownWelcome) {
    context.globalState.update('hasShownWelcome', true);
    vscode.window
      .showInformationMessage(
        'Django SmartPath installed! Make sure to run: pip install django-smartpath',
        'Open Docs',
        'Dismiss'
      )
      .then((choice) => {
        if (choice === 'Open Docs') {
          vscode.env.openExternal(
            vscode.Uri.parse('https://github.com/django-smartpath/django-smartpath')
          );
        }
      });
  }
}

export function deactivate() {}