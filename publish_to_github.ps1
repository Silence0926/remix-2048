$ErrorActionPreference = 'Stop'

$repoUrl = 'https://github.com/Silence0926/remix-2048.git'
$repoDir = Join-Path $env:TEMP 'remix-2048-github-publish'
$sourceDir = $PSScriptRoot

Write-Host '2048 Remix - GitHub Publisher' -ForegroundColor Cyan
Write-Host "Source: $sourceDir"
Write-Host "Target: $repoUrl"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git was not found. Install Git for Windows first: https://git-scm.com/download/win'
}

$name = (& git config --global user.name 2>$null)
$email = (& git config --global user.email 2>$null)
if ([string]::IsNullOrWhiteSpace($name) -or [string]::IsNullOrWhiteSpace($email)) {
    throw 'Git author identity is not configured. Run: git config --global user.name "Your GitHub name" and git config --global user.email "Your GitHub email"'
}

if (Test-Path $repoDir) {
    $isRepo = Test-Path (Join-Path $repoDir '.git')
    if (-not $isRepo) {
        throw "The target folder exists but is not a Git repository: $repoDir. Rename or remove it, then run this script again."
    }
    Write-Host 'Updating existing temporary clone...' -ForegroundColor Yellow
    git -C $repoDir pull --ff-only origin main
} else {
    Write-Host 'Cloning the GitHub repository. Git Credential Manager may open a browser sign-in...' -ForegroundColor Yellow
    git clone --branch main $repoUrl $repoDir
}

if ($LASTEXITCODE -ne 0) { throw 'Git clone/pull failed.' }

$excludeDirs = @('.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache')
$excludeFiles = @('*.pyc', '*.pyo', '*.sqlite', '*.sqlite3', 'game_stats.json')
$robocopyArgs = @($sourceDir, $repoDir, '/E', '/R:2', '/W:1', '/NFL', '/NDL', '/NP')
foreach ($dir in $excludeDirs) { $robocopyArgs += @('/XD', $dir) }
foreach ($file in $excludeFiles) { $robocopyArgs += @('/XF', $file) }
& robocopy @robocopyArgs | Out-Host
$copyCode = $LASTEXITCODE
if ($copyCode -ge 8) { throw "File copy failed. Robocopy exit code: $copyCode" }

Push-Location $repoDir
try {
    git add -A
    if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }

    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'No changes to publish. The GitHub repository already matches this source folder.' -ForegroundColor Green
        exit 0
    }

    git commit -m 'feat: publish complete 2048 Remix source project'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }

    Write-Host 'Pushing source files to GitHub...' -ForegroundColor Yellow
    git push origin main
    if ($LASTEXITCODE -ne 0) { throw 'git push failed. Check the Git Credential Manager sign-in and repository permissions, then rerun this script.' }

    Write-Host 'Source upload completed.' -ForegroundColor Green
    Write-Host 'Verify the repository at: https://github.com/Silence0926/remix-2048'
} finally {
    Pop-Location
}
