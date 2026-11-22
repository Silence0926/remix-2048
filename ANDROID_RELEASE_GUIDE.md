# Android Release Guide (No iOS)

Last update: 2026-07-28

## 1) Prerequisites

Install tools:
- Node.js LTS
- Android Studio (includes SDK + platform tools)
- Java 17 (usually bundled with Android Studio)

Check:
- node -v
- npm -v
- adb version

## 2) Set Production API URL

Edit web/config.js and set:
window.REMIX2048_API_BASE = "https://your-api-domain/api";

Tip:
- Keep https in production.
- If API domain changes, update this first.

## 3) Generate Android Project from Current Web

From repo root:
- powershell -ExecutionPolicy Bypass -File scripts/setup_android_wrapper.ps1

This will:
- install Capacitor dependencies
- add Android platform project
- sync web assets from web/ into Android project

## 4) Open in Android Studio

Commands:
- cd android-wrapper
- npm run open

Then in Android Studio:
- wait Gradle sync finish
- verify package id: com.remix2048.game
- verify app name: 2048 Remix

## 5) Signing Config (Play requirement)

In Android Studio:
- Build -> Generate Signed Bundle / APK
- Choose Android App Bundle (AAB)
- Create/choose keystore
- Build release bundle

Keep keystore and passwords safe. Do not commit them.

## 6) Play Console Upload

Prepare listing assets:
- app icon (512x512)
- feature graphic (1024x500)
- phone screenshots
- privacy policy URL (host web/privacy.html content)

Upload:
- Create app in Play Console
- Fill Data Safety and content rating
- Upload .aab to internal testing first
- Fix warnings, then roll out production

## 7) Release Checklist

Must pass before production:
- App launches offline and online
- Leaderboard API reachable via production URL
- Privacy and terms pages accessible
- No debug logs/secrets in shipped config
- Internal test on at least 2 Android devices

## 8) Update Flow After New Web Changes

Whenever web files change:
- cd android-wrapper
- npm run sync
- npm run open
- rebuild signed AAB
