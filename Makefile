.PHONY: all linux windows macos clean

PYINSTALLER := pyinstaller
LINUXDEPLOY := linuxdeploy

APP_NAME := JobVault-Libre
APP_DIR := AppDir

SOURCE := src/myapp/app.py
RESOURCES := src/myapp/resources
ICON_PNG := src/myapp/assets/JV_logo.png
ICON_ICO := src/myapp/assets/JV_logo.ico
VERSION := $(shell python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

BINARY := dist/$(APP_NAME)
APPIMAGE := $(APP_NAME)-x86_64.AppImage

all:
	@:

linux:
	@echo "Building $(APP_NAME) v$(VERSION) for Linux..."

	$(PYINSTALLER) \
		--noconfirm \
		--clean \
		--windowed \
		--onefile \
		--name $(APP_NAME) \
		--icon $(ICON_ICO) \
		--add-data "$(RESOURCES):myapp/resources" \
		$(SOURCE)

	rm -rf $(APP_DIR)

	mkdir -p $(APP_DIR)/usr/bin
	mkdir -p $(APP_DIR)/usr/share/applications
	mkdir -p $(APP_DIR)/usr/share/icons/hicolor/256x256/apps

	cp $(BINARY) $(APP_DIR)/usr/bin/$(APP_NAME)
	chmod +x $(APP_DIR)/usr/bin/$(APP_NAME)

	cp $(ICON_PNG) \
		$(APP_DIR)/usr/share/icons/hicolor/256x256/apps/jobvaultlibre.png

	printf '%s\n' \
		'[Desktop Entry]' \
		'Type=Application' \
		'Name=JobVault Libre' \
		'Comment=Track and manage job applications' \
		'Exec=$(APP_NAME)' \
		'Icon=jobvaultlibre' \
		'Terminal=false' \
		'Categories=Office;Utility;' \
		> $(APP_DIR)/usr/share/applications/jobvaultlibre.desktop

	printf '%s\n' \
		'#!/bin/sh' \
		'HERE="$$(dirname "$$(readlink -f "$$0")")"' \
		'exec "$$HERE/usr/bin/$(APP_NAME)" "$$@"' \
		> $(APP_DIR)/$(APP_NAME).AppRun

	chmod +x $(APP_DIR)/$(APP_NAME).AppRun

	$(LINUXDEPLOY) \
		--appdir $(APP_DIR) \
		--output appimage
		--output-file $(APPIMAGE)

	@echo "Linux AppImage created: $(APPIMAGE)"

windows:
	@:

macos:
	@:

clean:
	rm -rf build
	rm -rf dist
	rm -rf $(APP_DIR)
	rm -f $(APPIMAGE).AppImage
	rm -f $(APP_NAME).spec