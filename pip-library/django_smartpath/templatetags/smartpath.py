"""
Django template tags for django-smartpath.

Usage in templates:
    {% load smartpath %}
    <img src="{% smartpath 'logo.png' %}">

This resolves 'logo.png' by searching MEDIA_ROOT and STATICFILES_DIRS,
returning the first matching URL.

Setup in settings.py:
    INSTALLED_APPS = [
        ...
        'django_smartpath',
    ]
"""

from django import template
from django.conf import settings
from pathlib import Path

register = template.Library()


def _find_file_url(filename: str) -> str:
    """
    Search media and static directories for the given filename.
    Returns the Django URL for the first match found.
    """
    # Check MEDIA_ROOT
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    media_url = getattr(settings, 'MEDIA_URL', '/media/')

    if media_root:
        for found in Path(media_root).rglob(filename):
            if found.is_file():
                relative = found.relative_to(media_root)
                return media_url.rstrip('/') + '/' + str(relative).replace('\\', '/')

    # Check STATICFILES_DIRS
    static_url = getattr(settings, 'STATIC_URL', '/static/')
    staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', [])

    for static_dir in staticfiles_dirs:
        for found in Path(static_dir).rglob(filename):
            if found.is_file():
                relative = found.relative_to(static_dir)
                return static_url.rstrip('/') + '/' + str(relative).replace('\\', '/')

    # Check STATIC_ROOT as fallback
    static_root = getattr(settings, 'STATIC_ROOT', None)
    if static_root and Path(static_root).exists():
        for found in Path(static_root).rglob(filename):
            if found.is_file():
                relative = found.relative_to(static_root)
                return static_url.rstrip('/') + '/' + str(relative).replace('\\', '/')

    # Check project-level static/ folder
    base_dir = getattr(settings, 'BASE_DIR', None)
    if base_dir:
        project_static = Path(base_dir) / 'static'
        if project_static.exists():
            for found in project_static.rglob(filename):
                if found.is_file():
                    relative = found.relative_to(project_static)
                    return static_url.rstrip('/') + '/' + str(relative).replace('\\', '/')

    # Return empty string with warning if not found
    return f'#smartpath-not-found:{filename}'


@register.simple_tag
def smartpath(filename):
    """
    Template tag that resolves a filename to its Django URL.

    Usage:
        {% load smartpath %}
        <img src="{% smartpath 'logo.png' %}">
        <link rel="stylesheet" href="{% smartpath 'styles.css' %}">

    Args:
        filename: Name of the file to find (just the filename, not full path)

    Returns:
        Full Django URL to the file, e.g., '/media/images/logo.png'
    """
    return _find_file_url(str(filename))
