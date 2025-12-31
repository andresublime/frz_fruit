#!/bin/bash
# Install browser dependencies for Playwright/Chromium on Debian/Ubuntu

echo "Installing browser dependencies for Playwright..."

# Update package list
sudo apt-get update

# Install required libraries for Chromium/Playwright
sudo apt-get install -y \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    libnss3 \
    libnspr4 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils

echo ""
echo "✓ Browser dependencies installed!"
echo ""
echo "You can now run: uv run generate_html.py"
