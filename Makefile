# django-smartpath — Master Makefile
# Run from the repo root.

.PHONY: all pip-build pip-publish pip-test vscode-build vscode-publish \
        pycharm-build pycharm-publish sublime-push clean help

help:
	@echo ""
	@echo "django-smartpath build targets"
	@echo "─────────────────────────────────────────"
	@echo "  make pip-test        Run pip library test suite"
	@echo "  make pip-build       Build wheel + sdist for PyPI"
	@echo "  make pip-publish     Upload to PyPI (needs ~/.pypirc)"
	@echo ""
	@echo "  make vscode-build    Compile TypeScript + package .vsix"
	@echo "  make vscode-publish  Publish to VS Code Marketplace"
	@echo ""
	@echo "  make pycharm-build   Build PyCharm plugin .zip"
	@echo "  make pycharm-publish Publish to JetBrains Marketplace"
	@echo ""
	@echo "  make sublime-push    Push Sublime plugin to GitHub (triggers Package Control)"
	@echo ""
	@echo "  make all             Build everything"
	@echo "  make clean           Remove all build artifacts"
	@echo ""

# ─────────────────────────────────────────────
# Pip library
# ─────────────────────────────────────────────

pip-test:
	cd pip-library && pip install pytest pytest-django django && pytest tests/ -v

pip-build:
	cd pip-library && pip install --upgrade build && python -m build

pip-publish: pip-build
	cd pip-library && pip install --upgrade twine && python -m twine upload dist/*

pip-publish-test: pip-build
	cd pip-library && python -m twine upload --repository testpypi dist/*

# ─────────────────────────────────────────────
# VS Code extension
# ─────────────────────────────────────────────

vscode-install-deps:
	cd vscode-extension && npm install

vscode-compile: vscode-install-deps
	cd vscode-extension && npm run compile

vscode-build: vscode-compile
	cd vscode-extension && npx vsce package

vscode-publish: vscode-compile
	cd vscode-extension && npx vsce publish

# ─────────────────────────────────────────────
# PyCharm plugin
# ─────────────────────────────────────────────

pycharm-build:
	cd pycharm-plugin && ./gradlew buildPlugin

pycharm-test:
	cd pycharm-plugin && ./gradlew runIde

pycharm-publish:
	cd pycharm-plugin && ./gradlew publishPlugin

# ─────────────────────────────────────────────
# Sublime Text plugin
# ─────────────────────────────────────────────

sublime-push:
	cd sublime-plugin && git add . && git commit -m "Update" && git push origin main

# ─────────────────────────────────────────────
# All
# ─────────────────────────────────────────────

all: pip-build vscode-build pycharm-build
	@echo "All builds complete."

# ─────────────────────────────────────────────
# Clean
# ─────────────────────────────────────────────

clean:
	rm -rf pip-library/dist/
	rm -rf pip-library/build/
	rm -rf pip-library/*.egg-info/
	rm -rf vscode-extension/out/
	rm -f  vscode-extension/*.vsix
	rm -rf pycharm-plugin/build/
	@echo "Clean complete."
