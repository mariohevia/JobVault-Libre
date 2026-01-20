

```bash
pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onefile \
  --name JobVaultLibre \
  --icon assets/JV_logo.png \
  --add-data "assets:assets" \
  src/app.py
```
  
* Your executable is at: `dist/JobVaultLibre`
* Your icon is at: `.assets/JV_logo.png`

All commands are safe and distro-agnostic.

---

## 1) Create the AppDir directory tree

```bash
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
```

---

## 2) Copy the application binary

```bash
cp dist/JobVaultLibre AppDir/usr/bin/
chmod +x AppDir/usr/bin/JobVaultLibre
```

---

## 3) Copy the icon

```bash
cp .assets/JV_logo.png AppDir/usr/share/icons/hicolor/256x256/apps/jobvaultlibre.png
```

> Icon name **must match** the `Icon=` field in the `.desktop` file (without extension).

---

## 4) Create the desktop file

```bash
cat > AppDir/usr/share/applications/jobvaultlibre.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=JobVault Libre
Comment=Track and manage job applications
Exec=JobVaultLibre
Icon=jobvaultlibre
Terminal=false
Categories=Office;Utility;
EOF
```

---

## 5) Create AppRun launcher

```bash
cat > AppDir/JobVaultLibre.AppRun << 'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/JobVaultLibre" "$@"
EOF

chmod +x AppDir/JobVaultLibre.AppRun
```

---

## 6) Verify AppDir structure

Run:

```bash
find AppDir -type f -maxdepth 4
```

You should see:

```
AppDir/JobVaultLibre.AppRun
AppDir/usr/bin/JobVaultLibre
AppDir/usr/share/applications/jobvaultlibre.desktop
AppDir/usr/share/icons/hicolor/256x256/apps/jobvaultlibre.png
```

---

## 7) (Next step) Build the AppImage

Once AppDir is ready:

```bash
linuxdeploy --appdir AppDir --output appimage    
```

This will produce:

```
JobVault_Libre-x86_64.AppImage
```