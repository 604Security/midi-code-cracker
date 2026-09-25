#!/bin/bash

# ================================
# MegaSpy Clue Trigger Script
# ================================
#
# Runs when the code is cracked: speaks a message and opens the clue image.
# Override the image with CLUE_IMAGE=/path/to/pic.jpg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMG="${CLUE_IMAGE:-$SCRIPT_DIR/clue.jpg}"
MSG="Congrats mega spy, you cracked the code. You have received a new clue. Examine this picture and follow the clue."

echo "[*] MegaSpy clue script triggered"

# 🔊 Speak victory
if command -v espeak-ng >/dev/null 2>&1; then
    espeak-ng -s 140 "$MSG"
elif command -v espeak >/dev/null 2>&1; then
    espeak -s 170 "$MSG"
else
    echo "[!] espeak not installed"
fi

if [ ! -f "$IMG" ]; then
    echo "[!] Clue image not found: $IMG"
    echo "[*] Put your clue picture at $SCRIPT_DIR/clue.jpg or set CLUE_IMAGE"
    exit 0
fi

# 🖼️ Open image (best available viewer)
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$IMG" >/dev/null 2>&1 &
elif command -v feh >/dev/null 2>&1; then
    feh "$IMG" &
elif command -v display >/dev/null 2>&1; then
    display "$IMG" &
else
    echo "[!] No image viewer found"
fi

exit 0
