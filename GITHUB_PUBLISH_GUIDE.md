# Publish 2048 Remix to GitHub (Windows)

This repository contains a helper script that copies the complete project into the existing GitHub repository and pushes it to `main`.

## Requirements

- Windows 10/11
- Git for Windows: https://git-scm.com/download/win
- A GitHub account with write access to `Silence0926/remix-2048`
- Git Credential Manager (included with current Git for Windows) for browser-based sign-in; no manually created Personal Access Token is required.

## Steps

1. Extract the project ZIP to a normal folder, for example `C:\Users\YourName\Downloads\2048_project`.
2. Open PowerShell in that extracted folder.
3. If Git has not been configured on this computer, set the commit identity once:

   ```powershell
   git config --global user.name "Your GitHub name"
   git config --global user.email "Your GitHub email"
   ```

4. Run the publisher:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\publish_to_github.ps1
   ```

5. If Git Credential Manager opens a browser, sign in to GitHub and authorize Git. The script then commits and pushes the project to `main`.
6. Verify the uploaded files at https://github.com/Silence0926/remix-2048.

The script uses the existing repository, preserves its Git history, and excludes local caches, virtual environments, Python bytecode, and runtime SQLite/save files. It does not create, display, or store a Personal Access Token.
