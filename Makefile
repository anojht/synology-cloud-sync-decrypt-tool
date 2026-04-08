.PHONY: help sync run test clean _clean-build build build-arm64 build-x86_64 dist-arm64 dist-x86_64 dist-all

APP_NAME := Open Source Synology Cloud Sync Decryption Tool
APP_PATH := dist/$(APP_NAME).app
PY_ARM64 := cpython-3.12-macos-aarch64-none
PY_X86_64 := cpython-3.12-macos-x86_64-none

# Files copied alongside the .app inside each release zip.
RELEASE_DOCS := COPYRIGHTS LICENSE README.md

help:
	@echo "Development:"
	@echo "  sync            Install dev + build deps into .venv"
	@echo "  run             Run the app from source"
	@echo "  test            Run pytest against the test fixtures"
	@echo "  clean           Remove .venv, build/, dist/, dist-zips/"
	@echo ""
	@echo "Build single architecture (.app at $(APP_PATH)):"
	@echo "  build           Alias for build-arm64"
	@echo "  build-arm64     Apple Silicon (M1/M2/M3)"
	@echo "  build-x86_64    Intel — requires Rosetta 2 on Apple Silicon hosts"
	@echo ""
	@echo "Release packaging (zips to dist-zips/):"
	@echo "  dist-arm64      Build + zip arm64 .app"
	@echo "  dist-x86_64     Build + zip x86_64 .app"
	@echo "  dist-all        Build + zip both architectures"
	@echo ""
	@echo "Note: build-arm64 and build-x86_64 each wipe .venv and dist/."
	@echo "      Use 'dist-all' if you want both .apps in the same run."

sync:
	uv sync --all-groups

run:
	uv run python Synology.py

test:
	uv run pytest

clean: _clean-build
	rm -rf .venv dist-zips

# Robust clean of build artifacts. Finder racing the rm to (re)create
# ``.DS_Store`` inside ``dist/`` causes ``rm -rf`` to fail with
# "Directory not empty"; deleting files first via ``find -delete`` and
# then the directories sidesteps it.
_clean-build:
	@find build dist -type f -delete 2>/dev/null || true
	@rm -rf build dist 2>/dev/null || true

# ---------------------------------------------------------------------------
# Architecture-specific builds
# ---------------------------------------------------------------------------
# Each build resets .venv to the target arch's CPython, syncs deps so uv
# pulls per-arch wheels for lz4 / Pillow / pycryptodomex, then runs py2app.

build: build-arm64

build-arm64: _clean-build
	uv python install $(PY_ARM64)
	rm -rf .venv
	uv venv --python $(PY_ARM64)
	uv sync --all-groups
	uv run python setup.py py2app
	@echo
	@file "$(APP_PATH)/Contents/MacOS/$(APP_NAME)"

build-x86_64: _clean-build
	@/usr/bin/arch -x86_64 /usr/bin/true 2>/dev/null || (echo "Rosetta 2 not available. Install with: softwareupdate --install-rosetta --agree-to-license"; exit 1)
	uv python install $(PY_X86_64)
	rm -rf .venv
	uv venv --python $(PY_X86_64)
	uv sync --all-groups
	uv run python setup.py py2app
	@echo
	@file "$(APP_PATH)/Contents/MacOS/$(APP_NAME)"

# ---------------------------------------------------------------------------
# Release packaging
# ---------------------------------------------------------------------------
# Each dist-* target builds the .app and zips it into dist-zips/. dist-all
# stages the arm64 zip BEFORE the x86_64 build wipes dist/, so both zips
# survive in dist-zips/.

dist-zips:
	mkdir -p dist-zips

dist-arm64: dist-zips build-arm64
	$(call _stage_and_zip,arm64)

dist-x86_64: dist-zips build-x86_64
	$(call _stage_and_zip,x86_64)

# Stage the .app + release docs into ``dist-zips/<APP> (<arch>)/`` and zip
# that directory so the archive contains the binary alongside COPYRIGHTS,
# LICENSE, and README.md under a single self-explanatory top-level folder.
define _stage_and_zip
	rm -rf "dist-zips/$(APP_NAME) ($(1))"
	mkdir -p "dist-zips/$(APP_NAME) ($(1))"
	cp -R "$(APP_PATH)" "dist-zips/$(APP_NAME) ($(1))/"
	cp $(RELEASE_DOCS) "dist-zips/$(APP_NAME) ($(1))/"
	cd dist-zips && /usr/bin/ditto -c -k --sequesterRsrc --keepParent "$(APP_NAME) ($(1))" "$(APP_NAME)-$(1).zip"
	rm -rf "dist-zips/$(APP_NAME) ($(1))"
	@echo "wrote dist-zips/$(APP_NAME)-$(1).zip"
endef

dist-all: dist-arm64 dist-x86_64
	@echo
	@ls -lh dist-zips/
