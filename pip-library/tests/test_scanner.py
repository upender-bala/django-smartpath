"""
Tests for django-smartpath scanner.
Run with: pytest tests/
"""

import os
import json
import tempfile
import pytest
from pathlib import Path


@pytest.fixture
def fake_django_project(tmp_path):
    """Create a minimal fake Django project structure."""
    # manage.py
    (tmp_path / 'manage.py').write_text("# fake manage.py")

    # settings.py
    settings_dir = tmp_path / 'myproject'
    settings_dir.mkdir()
    (settings_dir / '__init__.py').write_text('')
    (settings_dir / 'settings.py').write_text("""
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
""")

    # media folder with files
    media = tmp_path / 'media'
    (media / 'images').mkdir(parents=True)
    (media / 'images' / 'logo.png').write_bytes(b'fake png')
    (media / 'images' / 'banner.jpg').write_bytes(b'fake jpg')
    (media / 'documents' / 'report.pdf').mkdir(parents=True)
    (media / 'documents').mkdir(exist_ok=True)
    (media / 'documents' / 'report.pdf').write_bytes(b'fake pdf')

    # static folder with files
    static = tmp_path / 'static'
    (static / 'css').mkdir(parents=True)
    (static / 'js').mkdir(parents=True)
    (static / 'css' / 'styles.css').write_text('body { margin: 0; }')
    (static / 'js' / 'app.js').write_text('console.log("hello");')
    (static / 'favicon.ico').write_bytes(b'fake ico')

    return tmp_path


class TestFindDjangoRoot:
    def test_finds_root_from_file_in_project(self, fake_django_project):
        from django_smartpath.scanner import find_django_root
        views_py = fake_django_project / 'myproject' / 'views.py'
        views_py.write_text('# fake views')
        result = find_django_root(str(views_py))
        assert result == str(fake_django_project)

    def test_finds_root_from_project_dir(self, fake_django_project):
        from django_smartpath.scanner import find_django_root
        result = find_django_root(str(fake_django_project))
        assert result == str(fake_django_project)

    def test_returns_none_outside_django_project(self, tmp_path):
        from django_smartpath.scanner import find_django_root
        result = find_django_root(str(tmp_path))
        assert result is None


class TestScanDirectory:
    def test_scans_media_folder(self, fake_django_project):
        from django_smartpath.scanner import scan_directory
        media_dir = str(fake_django_project / 'media')
        files = scan_directory(media_dir, '/media/', 'media')
        assert len(files) >= 3
        names = [f['name'] for f in files]
        assert 'logo.png' in names
        assert 'banner.jpg' in names

    def test_file_has_required_fields(self, fake_django_project):
        from django_smartpath.scanner import scan_directory
        media_dir = str(fake_django_project / 'media')
        files = scan_directory(media_dir, '/media/', 'media')
        assert len(files) > 0
        file = files[0]
        assert 'name' in file
        assert 'url' in file
        assert 'relative_path' in file
        assert 'python_string' in file
        assert 'template_tag' in file
        assert 'type' in file

    def test_url_is_correct_format(self, fake_django_project):
        from django_smartpath.scanner import scan_directory
        media_dir = str(fake_django_project / 'media')
        files = scan_directory(media_dir, '/media/', 'media')
        logo = next(f for f in files if f['name'] == 'logo.png')
        assert logo['url'] == '/media/images/logo.png'
        assert logo['python_string'] == '"/media/images/logo.png"'

    def test_template_tag_format(self, fake_django_project):
        from django_smartpath.scanner import scan_directory
        media_dir = str(fake_django_project / 'media')
        files = scan_directory(media_dir, '/media/', 'media')
        logo = next(f for f in files if f['name'] == 'logo.png')
        assert logo['template_tag'] == "{% smartpath 'logo.png' %}"

    def test_returns_empty_for_nonexistent_dir(self):
        from django_smartpath.scanner import scan_directory
        files = scan_directory('/nonexistent/path', '/media/', 'media')
        assert files == []


class TestScanProject:
    def test_scans_full_project(self, fake_django_project):
        from django_smartpath.scanner import scan_project
        result = scan_project(str(fake_django_project))
        assert 'files' in result
        assert 'meta' in result
        assert result['meta']['project_root'] == str(fake_django_project)
        assert result['meta']['total_files'] > 0

    def test_finds_both_media_and_static(self, fake_django_project):
        from django_smartpath.scanner import scan_project
        result = scan_project(str(fake_django_project))
        types = {f['type'] for f in result['files']}
        assert 'media' in types
        assert 'static' in types


class TestGetFilesJson:
    def test_returns_valid_json(self, fake_django_project):
        from django_smartpath.scanner import get_files_json
        output = get_files_json(str(fake_django_project))
        data = json.loads(output)
        assert 'files' in data

    def test_query_filters_results(self, fake_django_project):
        from django_smartpath.scanner import get_files_json
        output = get_files_json(str(fake_django_project), query='logo')
        data = json.loads(output)
        assert all('logo' in f['name'].lower() or 'logo' in f['relative_path'].lower()
                   for f in data['files'])

    def test_empty_query_returns_all(self, fake_django_project):
        from django_smartpath.scanner import get_files_json
        all_output = get_files_json(str(fake_django_project))
        filtered_output = get_files_json(str(fake_django_project), query='')
        all_data = json.loads(all_output)
        filtered_data = json.loads(filtered_output)
        assert len(all_data['files']) == len(filtered_data['files'])


class TestSettings:
    """Minimal Django settings for template tag tests."""
    DATABASES = {}
    INSTALLED_APPS = ['django_smartpath']
    TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                  'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {}}]
    MEDIA_URL = '/media/'
    STATIC_URL = '/static/'
    USE_TZ = True
    SECRET_KEY = 'test-secret-key'
