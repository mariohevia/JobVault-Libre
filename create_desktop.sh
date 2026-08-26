#!/usr/bin/env sh
set -eu

# ========= Config (change these) =========
VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
REPO_OWNER="mariohevia"
REPO_NAME="JobVault-Libre"
APPIMAGE_BASENAME="JobVault-Libre"

# Optional overrides (leave empty to auto-extract icon from the AppImage)
# ICON_FILE="/path/to/icon.png"

# ========= Derived values =========
TAG="v${VERSION}"
APPIMAGE_FILE="${APPIMAGE_BASENAME}-v${VERSION}-x86_64.AppImage"
DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${TAG}/${APPIMAGE_FILE}"

APP_ID="jobvault-libre"
APP_DISPLAY_NAME="JobVault Libre"

# Install locations (system-wide if possible; otherwise per-user)
SYS_APP_DIR="/opt/${APP_DISPLAY_NAME}"
SYS_BIN_LINK="/usr/local/bin/${APP_ID}"
SYS_DESKTOP_DIR="/usr/share/applications"
SYS_ICON_DIR="/usr/share/icons/hicolor/256x256/apps"

USER_APP_DIR="${HOME}/.local/opt/${APP_DISPLAY_NAME}"
USER_BIN_DIR="${HOME}/.local/bin"
USER_DESKTOP_DIR="${HOME}/.local/share/applications"
USER_ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }; }
need_cmd curl
need_cmd chmod
need_cmd mkdir
need_cmd rm
need_cmd mv
need_cmd ln
need_cmd mktemp
need_cmd find
need_cmd sort
need_cmd head

is_root() { [ "$(id -u)" -eq 0 ]; }
have_sudo() { command -v sudo >/dev/null 2>&1; }

run_as_root() {
  if is_root; then
    sh -c "$*"
  elif have_sudo; then
    sudo sh -c "$*"
  else
    return 1
  fi
}

choose_icon_from_extract() {
  extract_dir="$1"

  # Prefer standard icon locations inside the AppImage
  # Pick the largest hicolor size folder available.
  icon_path="$(find "${extract_dir}/squashfs-root" \
    \( -path "*/usr/share/icons/hicolor/*/apps/*.png" -o -path "*/usr/share/pixmaps/*.png" -o -name "*.png" -o -name "*.svg" \) \
    2>/dev/null \
    | sort -V \
    | tail -n 1 \
    || true)"

  if [ -z "${icon_path}" ]; then
    echo ""
  else
    echo "${icon_path}"
  fi
}

write_desktop_file() {
  desktop_path="$1"
  exec_path="$2"
  icon_name="$3"

  cat > "${desktop_path}" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Comment=Track and manage your job applications
Exec=${exec_path}
Icon=${icon_name}
Terminal=false
Categories=Office;Utility;
StartupNotify=true
EOF
}

main() {
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "${tmpdir}"' EXIT

  echo "Downloading: ${DOWNLOAD_URL}"
  curl -fL --retry 3 --retry-delay 2 -o "${tmpdir}/${APPIMAGE_FILE}" "${DOWNLOAD_URL}"

  chmod +x "${tmpdir}/${APPIMAGE_FILE}"

  # Try system-wide install first; otherwise per-user.
  if run_as_root "true" 2>/dev/null; then
    app_dir="${SYS_APP_DIR}"
    bin_link="${SYS_BIN_LINK}"
    desktop_dir="${SYS_DESKTOP_DIR}"
    icon_dir="${SYS_ICON_DIR}"
    exec_target="${app_dir}/${APP_ID}.AppImage"
    desktop_path="${desktop_dir}/${APP_ID}.desktop"
    icon_dest="${icon_dir}/${APP_ID}.png"

    run_as_root "mkdir -p '${app_dir}' '${desktop_dir}' '${icon_dir}'"
    run_as_root "mv -f '${tmpdir}/${APPIMAGE_FILE}' '${exec_target}'"
    run_as_root "chmod +x '${exec_target}'"
    run_as_root "ln -sf '${exec_target}' '${bin_link}'"
  else
    app_dir="${USER_APP_DIR}"
    bin_link="${USER_BIN_DIR}/${APP_ID}"
    desktop_dir="${USER_DESKTOP_DIR}"
    icon_dir="${USER_ICON_DIR}"
    exec_target="${app_dir}/${APP_ID}.AppImage"
    desktop_path="${desktop_dir}/${APP_ID}.desktop"
    icon_dest="${icon_dir}/${APP_ID}.png"

    mkdir -p "${app_dir}" "${USER_BIN_DIR}" "${desktop_dir}" "${icon_dir}"
    mv -f "${tmpdir}/${APPIMAGE_FILE}" "${exec_target}"
    chmod +x "${exec_target}"
    ln -sf "${exec_target}" "${bin_link}"
  fi

  # Icon: either user-supplied ICON_FILE or auto-extract from AppImage
  if [ "${ICON_FILE:-}" != "" ]; then
    if [ ! -f "${ICON_FILE}" ]; then
      echo "ICON_FILE set but not found: ${ICON_FILE}" >&2
      exit 1
    fi
    if run_as_root "true" 2>/dev/null && ! is_root; then
      # If installing system-wide via sudo, copy as root
      run_as_root "cp -f '${ICON_FILE}' '${icon_dest}'"
    else
      cp -f "${ICON_FILE}" "${icon_dest}"
    fi
  else
    # Extract and pick an icon from inside the AppImage
    extract_root="${tmpdir}/extract"
    mkdir -p "${extract_root}"

    # Run extraction without requiring root
    (cd "${extract_root}" && "${exec_target}" --appimage-extract >/dev/null 2>&1) || true

    icon_src="$(choose_icon_from_extract "${extract_root}")"
    if [ -z "${icon_src}" ]; then
      echo "Warning: could not extract an icon from the AppImage. Desktop file will still be created." >&2
    else
      # If svg, keep as svg; if png, keep as png. Desktop Icon= uses name without extension in many menus,
      # but using a full path is reliable.
      icon_ext="${icon_src##*.}"
      icon_dest="${icon_dest%.*}.${icon_ext}"

      if run_as_root "true" 2>/dev/null && ! is_root; then
        run_as_root "cp -f '${icon_src}' '${icon_dest}'"
      else
        cp -f "${icon_src}" "${icon_dest}"
      fi
    fi
  fi

  # Desktop file: use full paths for reliability
  # Exec should point to the symlink for PATH-friendly launching.
  exec_for_desktop="${bin_link}"
  icon_for_desktop="${APP_ID}"
  if [ -f "${icon_dest}" ]; then
    icon_for_desktop="${icon_dest}"
  fi

  if run_as_root "true" 2>/dev/null && ! is_root && [ "${desktop_dir}" = "${SYS_DESKTOP_DIR}" ]; then
    tmp_desktop="${tmpdir}/${APP_ID}.desktop"
    write_desktop_file "${tmp_desktop}" "${exec_for_desktop}" "${icon_for_desktop}"
    run_as_root "cp -f '${tmp_desktop}' '${desktop_path}'"
    run_as_root "chmod 644 '${desktop_path}'"
  else
    write_desktop_file "${desktop_path}" "${exec_for_desktop}" "${icon_for_desktop}"
    chmod 644 "${desktop_path}"
  fi

  echo "Installed:"
  echo "  AppImage: ${exec_target}"
  echo "  Launcher: ${desktop_path}"
  echo "  Command:  ${bin_link}"
  if [ -f "${icon_dest}" ]; then
    echo "  Icon:     ${icon_dest}"
  fi

  # Optional: refresh desktop database if available (system-wide)
  if command -v update-desktop-database >/dev/null 2>&1; then
    if [ "${desktop_dir}" = "${SYS_DESKTOP_DIR}" ]; then
      run_as_root "update-desktop-database '${desktop_dir}' >/dev/null 2>&1 || true" || true
    else
      update-desktop-database "${desktop_dir}" >/dev/null 2>&1 || true
    fi
  fi
}

main "$@"
