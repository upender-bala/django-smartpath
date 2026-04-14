"""
scanner.py - Dynamically scans Django project for media and static files.
Returns structured file data for IDE plugin consumption.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional


# Common static/media file extensions
SUPPORTED_EXTENSIONS = {
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.bmp', '.tiff',
    # CSS / JS
    '.css', '.js', '.ts', '.jsx', '.tsx',
    # Fonts
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    # Documents
    '.pdf', '.txt',
    # Audio / Video
    '.mp3', '.mp4', '.wav', '.ogg', '.webm', '.avi', '.mov',
    # Data
    '.json', '.xml', '.csv',
    # Archives
    '.zip', '.tar', '.gz',
}


def find_django_root(start_path: str) -> Optional[str]:
    """
    Walk up from start_path to find the Django project root.
    Identified by the presence of manage.py.
    """
    current = Path(start_path).resolve()
    # Walk up directory tree
    for directory in [current] + list(current.parents):
        if (directory / 'manage.py').exists():
            return str(directory)
    return None


def find_settings_file(project_root: str) -> Optional[str]:
    """Find Django settings.py in the project."""
    root = Path(project_root)
    # Common locations
    for settings_path in root.rglob('settings.py'):
        # Skip virtual environments
        parts = settings_path.parts
        skip_dirs = {'venv', '.venv', 'env', '.env', 'node_modules', '__pycache__'}
        if not any(part in skip_dirs for part in parts):
            return str(settings_path)
    return None


def parse_settings_for_paths(settings_file: str, project_root: str) -> Dict:
    """
    Parse Django settings to extract MEDIA_ROOT, STATIC_ROOT, and STATICFILES_DIRS.
    Returns dict with resolved absolute paths.
    """
    result = {
        'media_root': None,
        'media_url': '/media/',
        'static_root': None,
        'static_url': '/static/',
        'staticfiles_dirs': [],
    }

    if not settings_file or not os.path.exists(settings_file):
        return result

    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract MEDIA_URL
        import re
        media_url_match = re.search(r"MEDIA_URL\s*=\s*['\"]([^'\"]+)['\"]", content)
        if media_url_match:
            result['media_url'] = media_url_match.group(1)

        # Extract STATIC_URL
        static_url_match = re.search(r"STATIC_URL\s*=\s*['\"]([^'\"]+)['\"]", content)
        if static_url_match:
            result['static_url'] = static_url_match.group(1)

    except Exception:
        pass

    return result


def scan_directory(base_dir: str, url_prefix: str, folder_type: str) -> List[Dict]:
    """
    Recursively scan a directory and return file metadata.

    Args:
        base_dir: Absolute path to scan
        url_prefix: URL prefix (e.g., '/media/' or '/static/')
        folder_type: 'media' or 'static'

    Returns:
        List of file dicts with path info
    """
    files = []
    base_path = Path(base_dir)

    if not base_path.exists() or not base_path.is_dir():
        return files

    for file_path in base_path.rglob('*'):
        if not file_path.is_file():
            continue

        # Skip hidden files and common junk
        parts = file_path.parts
        skip_dirs = {'__pycache__', '.git', 'node_modules', '.DS_Store'}
        if any(part in skip_dirs or part.startswith('.') for part in parts[len(base_path.parts):]):
            continue

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        # Relative path from base_dir
        relative = file_path.relative_to(base_path)
        relative_str = str(relative).replace('\\', '/')  # normalize for all OS

        # Django URL
        url = url_prefix.rstrip('/') + '/' + relative_str

        # File size
        try:
            size = file_path.stat().st_size
        except OSError:
            size = 0

        files.append({
            'name': file_path.name,
            'relative_path': relative_str,
            'absolute_path': str(file_path),
            'url': url,
            'type': folder_type,
            'extension': ext.lstrip('.'),
            'size': size,
            # For template tag: just the filename
            'template_tag': "{{% smartpath '{name}' %}}".format(name=file_path.name),
            # For Python string: full URL
            'python_string': '"{url}"'.format(url=url),
        })

    return files


def scan_project(project_path: str) -> Dict:
    """
    Main entry point: scan a Django project and return all media/static files.

    Args:
        project_path: Path to scan from (can be any file/dir inside project)

    Returns:
        Dict with 'files' list and 'meta' information
    """
    # Find project root
    if os.path.isfile(project_path):
        search_from = os.path.dirname(project_path)
    else:
        search_from = project_path

    project_root = find_django_root(search_from)

    if not project_root:
        # Fallback: treat provided path as root
        project_root = search_from

    settings_file = find_settings_file(project_root)
    settings = parse_settings_for_paths(settings_file, project_root)

    all_files = []
    scanned_dirs = []

    # --- Scan media folder ---
    media_candidates = [
        os.path.join(project_root, 'media'),
        os.path.join(project_root, 'mediafiles'),
    ]
    for candidate in media_candidates:
        if os.path.isdir(candidate):
            files = scan_directory(candidate, settings['media_url'], 'media')
            all_files.extend(files)
            scanned_dirs.append({'path': candidate, 'type': 'media', 'url_prefix': settings['media_url']})
            break

    # --- Scan static folders ---
    static_candidates = [
        os.path.join(project_root, 'static'),
        os.path.join(project_root, 'staticfiles'),
        os.path.join(project_root, 'assets'),
    ]
    for candidate in static_candidates:
        if os.path.isdir(candidate):
            files = scan_directory(candidate, settings['static_url'], 'static')
            all_files.extend(files)
            scanned_dirs.append({'path': candidate, 'type': 'static', 'url_prefix': settings['static_url']})

    # Also check each Django app for static/ subfolder
    if project_root:
        for item in os.listdir(project_root):
            item_path = os.path.join(project_root, item)
            if not os.path.isdir(item_path):
                continue
            skip = {'media', 'static', 'staticfiles', 'mediafiles', 'assets',
                    'venv', '.venv', 'env', 'node_modules', '.git', '__pycache__'}
            if item in skip or item.startswith('.'):
                continue
            # Check for app-level static folder
            app_static = os.path.join(item_path, 'static')
            if os.path.isdir(app_static):
                files = scan_directory(app_static, settings['static_url'], 'static')
                all_files.extend(files)
                scanned_dirs.append({'path': app_static, 'type': 'static', 'url_prefix': settings['static_url']})

    return {
        'files': all_files,
        'meta': {
            'project_root': project_root,
            'settings_file': settings_file,
            'media_url': settings['media_url'],
            'static_url': settings['static_url'],
            'scanned_dirs': scanned_dirs,
            'total_files': len(all_files),
        }
    }


def get_files_json(project_path: str, query: str = '') -> str:
    """
    Get filtered file list as JSON string.
    This is the primary function called by the CLI.

    Args:
        project_path: Path inside Django project
        query: Optional filter string

    Returns:
        JSON string
    """
    result = scan_project(project_path)

    if query:
        q = query.lower()
        result['files'] = [
            f for f in result['files']
            if q in f['name'].lower() or q in f['relative_path'].lower()
        ]

    return json.dumps(result, indent=2)
