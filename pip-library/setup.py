"""
setup.py for django-smartpath

To build and publish:
    python -m pip install --upgrade build twine
    python -m build
    python -m twine upload dist/*

Or use the Makefile:
    make publish
"""

from setuptools import setup, find_packages
import os

# Read README for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-smartpath',
    version='1.0.0',
    author='django-smartpath contributors',
    author_email='hello@django-smartpath.dev',
    description='Smart media/static file path insertion for Django — works in VS Code, PyCharm, Sublime Text',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/django-smartpath/django-smartpath',
    project_urls={
        'Bug Tracker': 'https://github.com/django-smartpath/django-smartpath/issues',
        'Documentation': 'https://django-smartpath.readthedocs.io/',
        'Source Code': 'https://github.com/django-smartpath/django-smartpath',
    },
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    package_data={
        'django_smartpath': ['templatetags/*.py'],
    },
    python_requires='>=3.8',
    install_requires=[
        # No external dependencies — uses only stdlib + Django
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-django',
            'django>=3.2',
        ],
    },
    entry_points={
        'console_scripts': [
            'django-smartpath=django_smartpath.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    keywords='django, static files, media files, developer tools, ide, vscode, pycharm, sublime text',
    license='MIT',
)
