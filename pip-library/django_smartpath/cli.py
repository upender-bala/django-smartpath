"""
cli.py - Command-line interface for django-smartpath.
IDE plugins call this to get file lists as JSON.

Usage:
    django-smartpath scan --path /path/to/project/file.py
    django-smartpath scan --path /path/to/project --query logo
    django-smartpath scan --path /path/to/project --format minimal
"""

import argparse
import json
import sys
import os

from .scanner import scan_project, get_files_json


def cmd_scan(args):
    """Scan command: returns file list as JSON."""
    path = args.path or os.getcwd()

    # Resolve to absolute path
    path = os.path.abspath(path)

    query = args.query or ''

    result_json = get_files_json(path, query)

    if args.format == 'minimal':
        # Compact output for performance
        data = json.loads(result_json)
        minimal = [
            {
                'name': f['name'],
                'url': f['url'],
                'type': f['type'],
                'python_string': f['python_string'],
                'template_tag': f['template_tag'],
            }
            for f in data['files']
        ]
        print(json.dumps(minimal))
    else:
        print(result_json)

    return 0


def cmd_version(args):
    """Print version."""
    from . import __version__
    print(f"django-smartpath {__version__}")
    return 0


def cmd_check(args):
    """Check if path is inside a Django project."""
    path = args.path or os.getcwd()
    path = os.path.abspath(path)

    from .scanner import find_django_root, find_settings_file
    root = find_django_root(path)

    result = {
        'is_django_project': root is not None,
        'project_root': root,
        'settings_file': find_settings_file(root) if root else None,
    }
    print(json.dumps(result))
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='django-smartpath',
        description='Smart file path insertion for Django projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan from current directory
  django-smartpath scan

  # Scan from specific file (e.g., the file being edited)
  django-smartpath scan --path /home/user/myproject/myapp/views.py

  # Filter by query
  django-smartpath scan --path /home/user/myproject --query logo

  # Minimal output (faster for large projects)
  django-smartpath scan --path /home/user/myproject --format minimal

  # Check if a path is inside a Django project
  django-smartpath check --path /home/user/myproject/views.py
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # scan command
    scan_parser = subparsers.add_parser('scan', help='Scan project for media/static files')
    scan_parser.add_argument(
        '--path', '-p',
        type=str,
        default=None,
        help='Path to the file being edited or project root (default: current directory)'
    )
    scan_parser.add_argument(
        '--query', '-q',
        type=str,
        default='',
        help='Filter files by name (optional)'
    )
    scan_parser.add_argument(
        '--format', '-f',
        choices=['full', 'minimal'],
        default='full',
        help='Output format: full (default) or minimal'
    )
    scan_parser.set_defaults(func=cmd_scan)

    # check command
    check_parser = subparsers.add_parser('check', help='Check if path is a Django project')
    check_parser.add_argument('--path', '-p', type=str, default=None)
    check_parser.set_defaults(func=cmd_check)

    # version command
    version_parser = subparsers.add_parser('version', help='Print version')
    version_parser.set_defaults(func=cmd_version)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
