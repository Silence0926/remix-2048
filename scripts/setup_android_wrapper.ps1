$ErrorActionPreference = "Stop"

Write-Host "== 2048 Remix Android Wrapper Setup =="
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$wrapperDir = Join-Path $repoRoot "android-wrapper"
Push-Location $wrapperDir

if (-not (Test-Path "node_modules")) {
  Write-Host "Installing npm dependencies..."
  npm install
  if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
}

if (-not (Test-Path "android")) {
  Write-Host "Adding Android platform..."
  npx cap add android
  if ($LASTEXITCODE -ne 0) { throw "npx cap add android failed" }
}

Write-Host "Syncing web assets into Android project..."
npx cap sync android
if ($LASTEXITCODE -ne 0) { throw "npx cap sync android failed" }

Write-Host "Done. To open Android Studio run:"
Write-Host "  cd android-wrapper"
Write-Host "  npm run open"

Pop-Location
