# Commands — Complete Terminal Reference
**Every command to run the AISec + Pursh platform, broken down word by word**

> How to read this file: Each command is dissected into its parts so you understand *what you are typing*, not just *that it works*. Format: `command` → explanation of each word → what actually happens when you press Enter.

---

## Table of Contents

1. [Terminal Basics](#1-terminal-basics)
2. [Navigation & File System](#2-navigation--file-system)
3. [Python Environment Setup](#3-python-environment-setup)
4. [Starting the AISec Runner](#4-starting-the-aisec-runner)
5. [Starting the Dashboard (Next.js)](#5-starting-the-dashboard-nextjs)
6. [SSH — Remote Server Access](#6-ssh--remote-server-access)
7. [Git — Source Code Management](#7-git--source-code-management)
8. [Semgrep — SAST Scanner](#8-semgrep--sast-scanner)
9. [OWASP ZAP — DAST Scanner](#9-owasp-zap--dast-scanner)
10. [Trivy — Container & Filesystem Scanner](#10-trivy--container--filesystem-scanner)
11. [Syft — SBOM Generator](#11-syft--sbom-generator)
12. [Grype — Vulnerability Scanner on SBOM](#12-grype--vulnerability-scanner-on-sbom)
13. [Gitleaks — Secrets Scanner](#13-gitleaks--secrets-scanner)
14. [Checkov — IaC Scanner](#14-checkov--iac-scanner)
15. [Prowler — Cloud Security Scanner](#15-prowler--cloud-security-scanner)
16. [Docker — Container Commands](#16-docker---container-commands)
17. [Supabase CLI](#17-supabase-cli)
18. [Piping — Connecting Commands Together](#18-piping--connecting-commands-together)
19. [Environment Variables](#19-environment-variables)
20. [Process Management](#20-process-management)
21. [Log Viewing & Filtering](#21-log-viewing--filtering)
22. [Network & API Testing (curl)](#22-network--api-testing-curl)
23. [Full Startup Sequence — Everything at Once](#23-full-startup-sequence--everything-at-once)

---

## 1. Terminal Basics

### What is a terminal?
The terminal (also called command line, shell, console, or CLI) is a text interface where you type instructions directly to your computer's operating system. Instead of clicking buttons, you type commands. The operating system reads them and executes them immediately.

**Shells — the language your terminal speaks:**
- **PowerShell** — Windows default in this project (`.ps1` scripts)
- **Bash** — Linux/macOS default (`.sh` scripts) — also available via Git Bash on Windows
- **zsh** — macOS default since Catalina — same syntax as bash for most things

### Command anatomy
Every command follows this pattern:
```
program  --flag  --option value  argument
```

Example:
```
semgrep  --config  p/owasp-top-ten  ./pursh/backend
   ^         ^           ^               ^
 program   flag        value         argument
 (what    (modifier)  (which         (what to
 to run)              ruleset)        scan)
```

### The prompt
```
PS C:\Users\prabh\Downloads\ci_cd_seclab>
^  ^                                    ^
|  current directory you are in        cursor (type here)
PowerShell indicator
```

On Linux/Mac:
```
prabh@server:~/ci_cd_seclab$
^     ^        ^             ^
user  machine  directory    cursor
```

---

## 2. Navigation & File System

### `cd` — Change Directory
```powershell
cd internal\aisec\runner
```
- `cd` → "change directory" — move your terminal's current location
- `internal\aisec\runner` → the path to move into (backslash on Windows, forward slash on Linux/Mac)
- **What happens:** Your prompt changes to show the new location. All commands you run now execute from inside `runner/`.

```powershell
cd ..
```
- `..` → means "one folder up" — go to the parent directory
- **What happens:** If you were in `runner/`, you are now in `aisec/`

```powershell
cd ~
```
- `~` → shorthand for your home directory (e.g., `C:\Users\prabh` on Windows)
- **What happens:** Jumps to your user's home folder from anywhere

---

### `ls` / `dir` — List Files
```powershell
ls
```
- `ls` → "list" — show all files and folders in the current directory
- On Windows PowerShell, `ls` is an alias for `Get-ChildItem`
- **What happens:** Prints a list of everything in the current folder

```powershell
ls -la
```
(Linux/Mac/Git Bash)
- `ls` → list files
- `-l` → "long format" — show permissions, owner, size, date
- `-a` → "all" — include hidden files (files starting with `.` like `.env`)
- **What happens:** Shows every file including hidden ones with full details

---

### `pwd` — Print Working Directory
```powershell
pwd
```
- `pwd` → "print working directory" — shows your current location as a full path
- **What happens:** Prints something like `C:\Users\prabh\Downloads\ci_cd_seclab`
- **When to use:** When you are lost and need to know exactly where you are

---

### `mkdir` — Make Directory
```powershell
mkdir scan_results
```
- `mkdir` → "make directory" — create a new folder
- `scan_results` → the name of the folder to create
- **What happens:** A new empty folder named `scan_results` appears in your current location

---

### `cat` — Display File Contents
```bash
cat results/semgrep.json
```
- `cat` → "concatenate" — originally for joining files, now commonly used just to print file contents
- `results/semgrep.json` → the file to display
- **What happens:** Prints the entire file content to your terminal screen

---

## 3. Python Environment Setup

### `python` vs `python3`
```bash
python --version
python3 --version
```
- `python` → runs the Python interpreter
- `--version` → a flag telling Python to print its version number and exit
- **What happens:** Prints `Python 3.12.x` — tells you which Python version is installed
- **Why this matters:** Python 2 and Python 3 are incompatible. AISec uses Python 3.12.

---

### `pip install` — Install Python Packages
```bash
pip install -r requirements.txt
```
- `pip` → "Pip Installs Packages" — Python's package manager (like npm for Node.js)
- `install` → the pip command to install packages
- `-r` → "requirements file" — flag telling pip to read packages from a file instead of specifying one by name
- `requirements.txt` → the file listing all packages and their versions the project needs
- **What happens:** pip reads every line in `requirements.txt`, downloads each package from PyPI (Python Package Index), and installs them into your Python environment. This is like `npm install`.

---

### `python -m venv` — Create Virtual Environment
```bash
python -m venv venv
```
- `python` → run the Python interpreter
- `-m` → "module" — run a Python module as a script instead of an interactive session
- `venv` → the module name (Virtual ENVironment — a Python standard library tool)
- `venv` (second one) → the name of the folder to create the virtual environment in
- **What happens:** Creates a self-contained Python installation in a folder called `venv/`. This isolates the project's packages from other Python projects on your system.

```bash
# Activate the virtual environment:
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux/Mac:
source venv/bin/activate
```
- `source` → (Linux/Mac) runs a script in the current shell session (so environment changes persist)
- `venv/bin/activate` → the script that sets `PATH` to use this venv's Python first
- **What happens after activation:** Your prompt shows `(venv)` prefix. Now `python` and `pip` commands use the project's isolated packages, not your system Python.

---

### `deactivate` — Exit Virtual Environment
```bash
deactivate
```
- No flags, no arguments — just `deactivate`
- **What happens:** Removes the venv from PATH. You're back to system Python.

---

## 4. Starting the AISec Runner

### Navigate to the runner directory
```powershell
cd C:\Users\prabh\Downloads\ci_cd_seclab\internal\aisec\runner
```

### Install dependencies (first time only)
```powershell
pip install -r requirements.txt
```
See [pip install explanation above](#pip-install----install-python-packages).

### `uvicorn` — Start the Runner Server
```powershell
uvicorn main:app --reload --port 8002
```
- `uvicorn` → an ASGI (Asynchronous Server Gateway Interface) web server for Python — the fastest way to run FastAPI apps
- `main` → the Python file to load (`main.py` — note: no `.py` extension)
- `:app` → inside `main.py`, find the variable called `app` (which is `app = FastAPI(...)`) — that is what uvicorn serves
- `--reload` → "hot reload" — whenever you save a change to any Python file, uvicorn automatically restarts. Without this, you would have to stop and restart manually after every code change.
- `--port 8002` → listen on port 8002. Ports are like apartment numbers in a building (your computer). The runner lives at apartment 8002. Default would be 8000 but we use 8002 to avoid conflicts.
- **What happens:** The runner starts and prints:
  ```
  INFO:     Started server process [12345]
  INFO:     Uvicorn running on http://0.0.0.0:8002
  ```
  The terminal is now "occupied" by the server. Keep it running. Open a new terminal for other commands.

---

### With host binding (for network access)
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```
- `--host 0.0.0.0` → listen on all network interfaces, not just localhost. `0.0.0.0` means "accept connections from any IP address on this machine". `127.0.0.1` (default) means "only from this machine itself".
- **What happens:** Other machines on your network can reach the runner at `http://your-ip:8002`. Required when the dashboard runs in Docker or on a different machine.

---

### With environment variables loaded
```powershell
# Windows PowerShell:
$env:SUPABASE_URL="https://xxx.supabase.co"; $env:SUPABASE_JWT_SECRET="your-key"; uvicorn main:app --reload --port 8002

# Linux/Mac:
SUPABASE_URL="https://xxx.supabase.co" SUPABASE_JWT_SECRET="your-key" uvicorn main:app --reload --port 8002
```
- `$env:VARIABLE_NAME="value"` → (PowerShell) set an environment variable for this session
- `VARIABLE="value"` → (Bash) set a variable only for the next command
- **What happens:** uvicorn starts with those variables available to the app, so `os.getenv("SUPABASE_URL")` returns the value. Better approach: use a `.env` file with `python-dotenv`.

---

### `python -m py_compile` — Syntax Check Without Running
```powershell
python -m py_compile main.py
```
- `python` → run Python
- `-m py_compile` → run the `py_compile` module — it checks Python syntax without executing the code
- `main.py` → the file to check
- **What happens:** If there are syntax errors (typos, missing colons, bad indentation), they print to screen. If the file is clean, nothing prints — silence means success. Always run this before restarting uvicorn.

---

## 5. Starting the Dashboard (Next.js)

### What is Next.js?
Next.js is a React framework — a set of tools built on top of React (a JavaScript UI library) that adds server-side rendering, routing, and API routes. The AISec dashboard is built with Next.js 15.

### Navigate to dashboard
```powershell
cd C:\Users\prabh\Downloads\ci_cd_seclab\internal\aisec\dashboard
```

### `npm install` — Install Node.js Dependencies
```powershell
npm install
```
- `npm` → "Node Package Manager" — the package manager for JavaScript/Node.js (like `pip` for Python)
- `install` → the npm command to install all dependencies
- No arguments → npm reads `package.json` in the current directory and installs everything listed there
- **What happens:** npm reads `package.json`, downloads all packages (React, Next.js, Tailwind CSS, TypeScript, etc.) from the npm registry, and puts them in a `node_modules/` folder. Also creates/updates `package-lock.json` which locks exact versions for reproducibility.

---

### `npm run dev` — Start Development Server
```powershell
npm run dev
```
- `npm` → Node Package Manager
- `run` → the npm subcommand that executes a script defined in `package.json`
- `dev` → the name of the script to run. In `package.json` you'll find: `"scripts": { "dev": "next dev" }` — so `npm run dev` → `next dev`
- `next` → (executed by npm) the Next.js CLI
- `dev` → (Next.js flag) start in development mode with hot reloading, detailed error messages, and no production optimizations
- **What happens:** Next.js compiles your TypeScript + React components, starts a local HTTP server on port 3000, and watches files for changes. Open `http://localhost:3000` in your browser to see the dashboard.
- **Terminal output:**
  ```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
  - Ready in 2.1s
  ```

---

### `npm run build` — Build for Production
```powershell
npm run build
```
- `npm run` → execute a package.json script
- `build` → script defined as `"build": "next build"` in package.json
- `next build` → compiles TypeScript, bundles JavaScript, optimizes images, generates static pages where possible
- **What happens:** Creates an optimized production build in `.next/` folder. Takes 30–120 seconds. Shows output sizes for each page. Run this before deploying to a server.

---

### `npm run start` — Run Production Build Locally
```powershell
npm run start
```
- `npm run start` → runs `next start`
- `next start` → serves the pre-built production bundle (from `npm run build`)
- **What happens:** Unlike `npm run dev`, this serves the optimized build with no hot reload. Use this to test production behavior locally before deploying.

---

### `npx tsc --noEmit` — TypeScript Type Check
```powershell
npx tsc --noEmit
```
- `npx` → "Node Package Execute" — runs a package's binary without installing it globally. Here it runs the `tsc` binary from your local `node_modules/.bin/tsc`
- `tsc` → TypeScript Compiler
- `--noEmit` → check types but do NOT output any JavaScript files — only report errors
- **What happens:** The TypeScript compiler reads all `.ts` and `.tsx` files and checks if types are correct (e.g., you passed a string where a number was expected). No output = no type errors. Errors print to screen with file and line number.

---

## 6. SSH — Remote Server Access

### What is SSH?
SSH (Secure Shell) is a protocol for logging into and running commands on a remote computer over an encrypted connection. When your runner is deployed on a cloud server instead of your laptop, you use SSH to reach it.

### `ssh` — Connect to Remote Server
```bash
ssh username@server-ip-address
```
- `ssh` → Secure Shell — the program that creates an encrypted connection
- `username` → your account name on the remote server (e.g., `ubuntu`, `ec2-user`, `root`)
- `@` → separator between username and server address
- `server-ip-address` → the IP or hostname of the remote machine (e.g., `54.123.45.67` or `runner.aisec.internal`)
- **What happens:** SSH negotiates an encrypted tunnel to the server. If successful, your terminal prompt changes to show the remote server's prompt. You are now running commands *on that machine*, not yours.

---

### `ssh` with a key file (AWS EC2 style)
```bash
ssh -i ~/.ssh/aisec-runner.pem ubuntu@54.123.45.67
```
- `ssh` → Secure Shell program
- `-i` → "identity file" — specify which private key to use for authentication (instead of password)
- `~/.ssh/aisec-runner.pem` → path to your private key file. `~` = home directory, `.ssh` = hidden folder for SSH keys, `aisec-runner.pem` = the key file downloaded when you created the EC2 instance on AWS
- `ubuntu` → the default username for Ubuntu-based AWS EC2 instances
- `@54.123.45.67` → the public IP of your EC2 instance (find in AWS Console → EC2 → Instances)
- **What happens:** SSH uses public-key cryptography: your `.pem` file is the private key; AWS holds the matching public key on the server. No password needed — the math proves you are who you say you are.

---

### Fix key file permissions (required on Linux/Mac)
```bash
chmod 400 ~/.ssh/aisec-runner.pem
```
- `chmod` → "change mode" — change file permissions
- `400` → permission code: `4` = read, `0` = no write/execute for group, `0` = no access for others. Only you can read it — SSH refuses to use key files that others can read (security requirement)
- `~/.ssh/aisec-runner.pem` → the key file to protect
- **What happens:** Sets the file to read-only for your user only. SSH will reject the key with `WARNING: UNPROTECTED PRIVATE KEY FILE!` if this isn't done.

---

### `scp` — Secure Copy Files to/from Remote
```bash
scp ./scan_results/semgrep.json ubuntu@54.123.45.67:/home/ubuntu/results/
```
- `scp` → "Secure Copy Protocol" — copy files over SSH
- `./scan_results/semgrep.json` → local file to copy (source)
- `ubuntu@54.123.45.67` → remote server (same format as ssh)
- `:/home/ubuntu/results/` → `:` separates the server from the path. The remote destination directory
- **What happens:** Uploads the local file to the remote server over an encrypted SSH connection. The remote directory must exist.

```bash
# Download FROM remote server TO local:
scp ubuntu@54.123.45.67:/home/ubuntu/results/semgrep.json ./local_results/
```

---

### `ssh` — Run a Single Command Remotely (no interactive session)
```bash
ssh ubuntu@54.123.45.67 "uvicorn main:app --port 8002 &"
```
- Everything in quotes after the server address is a command to run on the remote machine
- `&` → run in background on the remote machine (so SSH can disconnect without killing the process)
- **What happens:** Connects, runs the command, disconnects. The process keeps running on the server.

---

### `ssh` tunnel — Access Remote Port Locally
```bash
ssh -L 8002:localhost:8002 ubuntu@54.123.45.67
```
- `-L` → "local port forwarding"
- `8002:localhost:8002` → format is `local_port:remote_host:remote_port`. Map your local port 8002 → remote machine's localhost:8002
- **What happens:** While this SSH connection is open, `http://localhost:8002` on your machine actually hits the runner running on the remote server. Useful for testing a remote runner as if it were local, without opening firewall ports.

---

## 7. Git — Source Code Management

### `git clone` — Download a Repository
```bash
git clone https://github.com/yourorg/ci_cd_seclab.git
```
- `git` → the Git version control program
- `clone` → git subcommand: copy a remote repository to your machine
- `https://github.com/...` → the URL of the remote repository (GitHub, GitLab, etc.)
- **What happens:** Downloads the entire repository (all files + full history) into a new folder named after the repo (`ci_cd_seclab/`).

---

### `git status` — See What Changed
```bash
git status
```
- `git status` → shows which files are modified, which are staged for commit, and which are untracked (new files Git doesn't know about yet)
- **What happens:** Prints a report. Green files = staged (ready to commit). Red files = modified but not staged.

---

### `git add` — Stage Changes
```bash
git add internal/aisec/runner/main.py
```
- `git add` → move file changes into the "staging area" (a holding zone before committing)
- `internal/aisec/runner/main.py` → the specific file to stage
- **What happens:** Git marks these changes as "ready to be committed". Nothing is saved permanently yet.

```bash
git add .
```
- `.` → current directory — stages ALL modified and new files in the current folder and subfolders
- **Use carefully:** Can accidentally stage secrets or large files. Prefer naming files explicitly.

---

### `git commit` — Save a Snapshot
```bash
git commit -m "fix: parallel pre-checks with asyncio.gather"
```
- `git commit` → create a permanent snapshot of staged changes in the repository history
- `-m` → "message" — provide the commit message inline (without this, git opens a text editor)
- `"fix: parallel pre-checks..."` → the commit message describing what changed and why. Convention: `type: description` where type = `fix`, `feat`, `docs`, `refactor`, `test`, `chore`
- **What happens:** Git saves the staged changes permanently with a unique ID (SHA hash), your name, timestamp, and the message. This is your "save point" in history.

---

### `git push` — Upload to Remote
```bash
git push origin main
```
- `git push` → upload local commits to a remote repository
- `origin` → the name of the remote (default name for the remote you cloned from; run `git remote -v` to see)
- `main` → the branch name to push to
- **What happens:** Your local commits are uploaded to GitHub/GitLab. Other team members (and CI/CD pipelines) can now see your changes.

---

### `git pull` — Download Latest Changes
```bash
git pull origin main
```
- `git pull` → fetch latest changes from remote AND merge them into your current branch
- `origin main` → from the `origin` remote, the `main` branch
- **What happens:** Downloads any commits others have pushed since your last pull, and merges them into your local files. This is how you stay current with the team.

---

### `git log` — View History
```bash
git log --oneline -20
```
- `git log` → show commit history
- `--oneline` → compact format: one line per commit (hash + message)
- `-20` → show only the last 20 commits
- **What happens:** Prints the 20 most recent commits. Press `q` to exit.

---

## 8. Semgrep — SAST Scanner

### What is SAST? What is Semgrep?
SAST = Static Application Security Testing. It reads your source code (without running it) and finds patterns that match known vulnerabilities. Semgrep is a fast, open-source SAST tool that uses pattern-matching rules.

### Basic scan
```bash
semgrep --config p/owasp-top-ten ./pursh/backend
```
- `semgrep` → run the Semgrep program
- `--config` → specify which rules to use
- `p/owasp-top-ten` → a pre-built rule pack from Semgrep's registry. `p/` = "pack" (community rulesets). `owasp-top-ten` = rules covering all 10 OWASP vulnerability categories
- `./pursh/backend` → the directory to scan. `./` = current directory. Semgrep will recursively scan all Python, JavaScript, etc. files inside
- **What happens:** Semgrep reads every source file, matches each line against all rules in the owasp-top-ten pack, and prints findings with file name, line number, rule ID, and description.

---

### Scan with JSON output (for machine processing)
```bash
semgrep --config p/owasp-top-ten --json ./pursh/backend > semgrep_results.json
```
- `--json` → output findings in JSON format instead of human-readable text
- `>` → "redirect" — instead of printing to screen, send output INTO the file `semgrep_results.json`
- **What happens:** Creates/overwrites `semgrep_results.json` with structured JSON that the runner can parse. The `>` operator is called output redirection.

---

### Scan with SARIF output (for Jira/GitHub integration)
```bash
semgrep --config p/owasp-top-ten --sarif --output semgrep.sarif ./pursh/backend
```
- `--sarif` → output in SARIF format (Static Analysis Results Interchange Format) — the standard format that GitHub, Azure DevOps, and Jira understand for security findings
- `--output semgrep.sarif` → write SARIF to this file (alternative to `>` redirect)
- **What happens:** Creates a SARIF file that can be uploaded to GitHub Code Scanning or parsed by the AISec ingest API.

---

### Multiple rule packs
```bash
semgrep --config p/owasp-top-ten --config p/security-audit --config p/python --json ./pursh/backend > semgrep_results.json
```
- Multiple `--config` flags → run multiple rule packs in one scan
- `p/security-audit` → broader security audit rules beyond just OWASP
- `p/python` → Python-specific security rules
- **What happens:** Semgrep runs all three rulesets simultaneously. Findings from all rules appear in one output file.

---

### Exclude directories from scan
```bash
semgrep --config p/owasp-top-ten --exclude-dir venv --exclude-dir node_modules --exclude-dir .git --json ./pursh > semgrep_results.json
```
- `--exclude-dir venv` → skip the `venv/` folder (your virtual environment — not your code)
- `--exclude-dir node_modules` → skip npm packages (not your code)
- `--exclude-dir .git` → skip git internals
- **What happens:** Semgrep scans only your actual source code, not libraries. This dramatically reduces noise and scan time.

---

### Run a specific rule only
```bash
semgrep --config "r/python.lang.security.audit.sqli.avoid-sqli" ./pursh/backend
```
- `r/` → "rule" (a single rule, not a pack)
- `python.lang.security.audit.sqli.avoid-sqli` → the full rule ID
- **What happens:** Runs only this one SQL injection rule. Useful when investigating a specific vulnerability class.

---

### Semgrep with severity filter
```bash
semgrep --config p/owasp-top-ten --severity ERROR --json ./pursh/backend > semgrep_results.json
```
- `--severity ERROR` → only report findings at ERROR severity (Semgrep's highest level). Options: `INFO`, `WARNING`, `ERROR`
- **What happens:** Filters out low-severity informational findings. Useful for CI/CD gates where you only want to fail on serious issues.

---

## 9. OWASP ZAP — DAST Scanner

### What is DAST? What is ZAP?
DAST = Dynamic Application Security Testing. Unlike SAST which reads code, DAST runs against a *live running application* and attacks it like a real hacker would — probing for XSS, SQL injection in HTTP responses, insecure headers, etc. OWASP ZAP (Zed Attack Proxy) is the most widely-used open-source DAST tool.

### ZAP baseline scan (safe, no attacks)
```bash
docker run --rm \
  -v $(pwd)/zap_results:/zap/wrk \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t http://host.docker.internal:8002 \
  -J zap_baseline.json \
  -r zap_report.html
```
Breaking this down line by line:

- `docker run` → run a Docker container (a packaged application with all its dependencies)
- `--rm` → "remove" — automatically delete the container after it finishes. Without this, stopped containers pile up and waste disk space
- `-v $(pwd)/zap_results:/zap/wrk` → "volume mount" — map a folder from your machine into the container
  - `$(pwd)` → run the `pwd` command and insert the output — gives the current directory path
  - `/zap_results` → a subfolder of current directory (created on your machine)
  - `:/zap/wrk` → mapped to `/zap/wrk` inside the container (ZAP looks here for output files)
  - So: files ZAP writes to `/zap/wrk/` inside container → appear in `./zap_results/` on your machine
- `ghcr.io/zaproxy/zaproxy:stable` → the Docker image to use. `ghcr.io` = GitHub Container Registry, `zaproxy/zaproxy` = the image, `:stable` = the tag (version)
- `zap-baseline.py` → the script to run inside the container. Baseline = passive scan only (observes traffic, no active attacks). Safe to run against production-like environments.
- `-t http://host.docker.internal:8002` → "target" — the URL to scan. `host.docker.internal` is a special DNS name that resolves to your host machine's IP from inside Docker. Port 8002 = the runner. In production you'd use the actual URL.
- `-J zap_baseline.json` → output a JSON report named `zap_baseline.json`
- `-r zap_report.html` → also output a human-readable HTML report

**What happens:** ZAP starts inside Docker, connects to your running app at port 8002, passively observes the pages/endpoints, checks for security misconfigurations (missing security headers, cookies without HttpOnly flag, etc.), and writes findings to JSON + HTML files in your `zap_results/` folder.

---

### ZAP full active scan (aggressive — only on test environments)
```bash
docker run --rm \
  -v $(pwd)/zap_results:/zap/wrk \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py \
  -t http://host.docker.internal:8002 \
  -J zap_full.json \
  -r zap_full_report.html
```
- `zap-full-scan.py` → active scanning — ZAP actually sends attack payloads (SQL injection strings, XSS payloads, etc.) to your app. **NEVER run against production.** Only run against a test/staging environment.
- **What happens:** ZAP crawls the app, then for every input field and URL parameter, sends malicious payloads and checks if the app is vulnerable. Much slower than baseline (minutes to hours) but finds active vulnerabilities.

---

## 10. Trivy — Container & Filesystem Scanner

### What is Trivy?
Trivy is an open-source security scanner made by Aqua Security. It scans container images, filesystems, and Git repositories for:
- Known CVEs (Common Vulnerabilities and Exposures) in OS packages and libraries
- Misconfigurations in Dockerfiles and IaC files
- Secrets accidentally committed to code

### Scan filesystem for vulnerabilities
```bash
trivy fs --format json --output trivy_fs.json ./pursh
```
- `trivy` → run the Trivy scanner
- `fs` → "filesystem" scan mode — scan a directory of source code and dependency files (not a container image)
- `--format json` → output in JSON format. Options: `table` (human-readable), `json`, `sarif`, `cyclonedx`, `spdx`
- `--output trivy_fs.json` → write output to this file
- `./pursh` → scan the `pursh/` directory
- **What happens:** Trivy finds your `requirements.txt` (Python), `package.json` (Node.js), `go.mod` (Go), etc. and checks every listed dependency against the CVE databases (NVD, OSV, GitHub Advisory). Prints findings with CVE ID, severity, affected package, and fixed version.

---

### Scan with severity filter
```bash
trivy fs --severity HIGH,CRITICAL --format json --output trivy_critical.json ./pursh
```
- `--severity HIGH,CRITICAL` → only report findings at HIGH or CRITICAL severity. Options: `UNKNOWN`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- **What happens:** Filters out Medium/Low/Unknown findings. Use this for CI/CD gates — only fail the build on High+ CVEs.

---

### Scan a Docker image
```bash
trivy image --format json --output trivy_image.json pursh-backend:latest
```
- `trivy` → Trivy scanner
- `image` → image scan mode — scan a Docker container image
- `--format json` → JSON output
- `--output trivy_image.json` → write to this file
- `pursh-backend:latest` → the Docker image to scan. `pursh-backend` = image name, `latest` = tag
- **What happens:** Trivy downloads/reads the container image layers, extracts all installed OS packages (Alpine, Debian, Ubuntu packages) and language libraries, and checks them against CVE databases. More thorough than filesystem scan because it sees what's actually installed in the running container.

---

### Scan with .trivyignore (accept known risks)
```bash
trivy fs --ignorefile .trivyignore --format json --output trivy_fs.json ./pursh
```
- `--ignorefile .trivyignore` → path to a file listing CVEs to ignore (accepted risks with justification)
- `.trivyignore` → a file in your repo that looks like:
  ```
  # CVE-2024-1234 — accepted risk, no fix available, mitigated by WAF
  CVE-2024-1234
  ```
- **What happens:** Trivy runs the full scan but skips any CVEs listed in `.trivyignore`. Findings that appear only in `.trivyignore` are suppressed from output. This is the enterprise pattern for "baseline-aware" scanning.

---

### Generate SBOM with Trivy
```bash
trivy fs --format cyclonedx --output sbom.cdx.json ./pursh
```
- `--format cyclonedx` → output in CycloneDX format (a standard SBOM format — Software Bill of Materials)
- `sbom.cdx.json` → the SBOM file
- **What happens:** Instead of a vulnerability report, generates a complete inventory of every library and component in your project in machine-readable CycloneDX JSON. This SBOM can then be scanned by Grype for vulnerabilities.

---

## 11. Syft — SBOM Generator

### What is Syft?
Syft is an open-source SBOM (Software Bill of Materials) generator made by Anchore. An SBOM is a complete ingredient list of your software — every library, package, and component with exact versions. Syft generates SBOMs from source directories or container images.

### Generate SBOM from filesystem
```bash
syft dir:./pursh --output cyclonedx-json=sbom_pursh.cdx.json
```
- `syft` → run the Syft tool
- `dir:./pursh` → scan a directory. `dir:` is a scheme prefix telling Syft this is a local folder, not a container image
- `--output` → specify output format and file
- `cyclonedx-json=sbom_pursh.cdx.json` → format is `cyclonedx-json` (CycloneDX in JSON format), write to `sbom_pursh.cdx.json`
- **What happens:** Syft scans the directory for package manifests (`requirements.txt`, `package.json`, `Pipfile.lock`, `yarn.lock`, etc.), identifies every dependency and its version, and writes a structured CycloneDX SBOM file.

---

### Generate SBOM from Docker image
```bash
syft pursh-backend:latest --output cyclonedx-json=sbom_image.cdx.json
```
- `pursh-backend:latest` → the Docker image to scan (no prefix needed for images)
- **What happens:** Syft reads the container image's layers, finds all installed packages (OS + language), and generates an SBOM. More complete than filesystem because it captures packages installed via `apt`, `apk`, etc.

---

### SPDX format (alternative SBOM standard)
```bash
syft dir:./pursh --output spdx-json=sbom_pursh.spdx.json
```
- `spdx-json` → SPDX (Software Package Data Exchange) format — another SBOM standard used by Linux Foundation projects
- **When to use:** CycloneDX is preferred for security tooling. SPDX is preferred for license compliance and open-source governance.

---

## 12. Grype — Vulnerability Scanner on SBOM

### What is Grype?
Grype is a vulnerability scanner made by Anchore that works with SBOMs. While Syft generates the ingredient list, Grype checks that list against CVE databases. The pair is: Syft → generates SBOM → Grype → scans SBOM for vulnerabilities.

### Scan a Syft-generated SBOM
```bash
grype sbom:./sbom_pursh.cdx.json --output json > grype_results.json
```
- `grype` → run the Grype scanner
- `sbom:./sbom_pursh.cdx.json` → input type. `sbom:` prefix tells Grype to read an SBOM file (not scan a directory directly). `./sbom_pursh.cdx.json` = the SBOM file Syft generated
- `--output json` → output in JSON format
- `>` → redirect output to file `grype_results.json`
- **What happens:** Grype reads the SBOM's component list, checks each one against the Grype vulnerability database (pulled from NVD, GitHub Advisory, OSV.dev, etc.), and reports which components have known CVEs with severity ratings and fix versions.

---

### Scan a directory directly (Grype can skip Syft)
```bash
grype dir:./pursh --output json > grype_results.json
```
- `dir:./pursh` → Grype will internally run its own SBOM generation and immediately scan it
- **What happens:** Combines Syft + Grype in one step. Less flexible but simpler for quick scans.

---

### Fail on severity threshold (for CI gates)
```bash
grype sbom:./sbom_pursh.cdx.json --fail-on high
```
- `--fail-on high` → exit with a non-zero exit code if any findings are HIGH or above. Options: `negligible`, `low`, `medium`, `high`, `critical`
- **What happens:** Returns exit code `1` (failure) if HIGH/CRITICAL vulnerabilities are found, exit code `0` (success) if not. CI/CD pipelines check the exit code to decide whether to pass or fail the build.

---

## 13. Gitleaks — Secrets Scanner

### What is Gitleaks?
Gitleaks scans your Git repository for accidentally committed secrets — API keys, passwords, private keys, tokens. It checks both current files AND all historical commits so you can't "fix" a leaked secret just by deleting it from the latest commit.

### Scan current repository
```bash
gitleaks detect --source . --report-format json --report-path gitleaks_report.json
```
- `gitleaks` → run Gitleaks
- `detect` → detection mode (as opposed to `protect` mode which runs as a pre-commit hook)
- `--source .` → scan the current directory (`.`) as a Git repository
- `--report-format json` → output format: `json`, `csv`, `sarif`
- `--report-path gitleaks_report.json` → write report to this file
- **What happens:** Gitleaks scans every file in every commit in the git history against 150+ built-in patterns (AWS access keys, GitHub tokens, Stripe keys, private keys, JWT secrets, etc.) and reports any matches with the file, line, commit hash, and matched pattern.

---

### Scan with verbose output (see what it's checking)
```bash
gitleaks detect --source . --verbose --report-format json --report-path gitleaks_report.json
```
- `--verbose` → print each file being scanned as Gitleaks processes it
- **What happens:** Shows real-time progress. Useful when a scan seems stuck — you can see what file it's on.

---

### Scan only current files (not history)
```bash
gitleaks detect --source . --no-git --report-format json --report-path gitleaks_staged.json
```
- `--no-git` → scan files directly without using git history. Faster, but only checks current state.
- **When to use:** In pre-commit hooks where you only care about what's about to be committed.

---

### Allow known false positives
```bash
gitleaks detect --source . --baseline-path .gitleaks_baseline.json --report-format json --report-path gitleaks_report.json
```
- `--baseline-path .gitleaks_baseline.json` → a file of previously accepted findings. Any finding matching the baseline is excluded from the new report.
- **What happens:** Gitleaks runs the full scan but suppresses findings that you've already reviewed and accepted. This prevents re-alerting on findings you've already triaged.

---

## 14. Checkov — IaC Scanner

### What is IaC? What is Checkov?
IaC = Infrastructure as Code — defining your servers, databases, networks in code files (Terraform, Kubernetes YAML, Dockerfile, etc.) instead of clicking through a cloud console. Checkov scans these files for misconfigurations — things like S3 buckets with public access, security groups open to the internet, or containers running as root.

### Scan Terraform files
```bash
checkov -d ./infra/terraform --output json > checkov_results.json
```
- `checkov` → run Checkov
- `-d ./infra/terraform` → "directory" — scan this directory for IaC files (Checkov auto-detects Terraform `.tf` files, Kubernetes YAML, Dockerfiles, etc.)
- `--output json` → output in JSON format. Options: `cli` (human), `json`, `sarif`, `csv`, `junitxml`
- `>` → redirect to file
- **What happens:** Checkov reads all `.tf` files, evaluates 1000+ built-in checks (CIS AWS benchmarks, HIPAA controls, GDPR controls, etc.) and reports which resources fail which checks with the check ID, description, and failing resource.

---

### Scan with specific framework
```bash
checkov -d . --framework terraform --output json > checkov_tf.json
checkov -d . --framework dockerfile --output json > checkov_docker.json
checkov -d . --framework kubernetes --output json > checkov_k8s.json
```
- `--framework terraform` → only scan Terraform files (skip Dockerfiles, K8s, etc.)
- **When to use:** When you want separate reports per IaC type.

---

### Skip specific checks (accepted risks)
```bash
checkov -d ./infra/terraform --skip-check CKV_AWS_18,CKV_AWS_21 --output json > checkov_results.json
```
- `--skip-check CKV_AWS_18,CKV_AWS_21` → skip these specific Checkov check IDs
- `CKV_AWS_18` = "Ensure S3 Bucket has access logging enabled" (example)
- **What happens:** Runs the full scan but suppresses the listed checks. Document the reason in your `.checkov_skip` file or accepted-risks tracker.

---

## 15. Prowler — Cloud Security Scanner

### What is Prowler?
Prowler is an open-source cloud security tool that audits your AWS (and GCP, Azure) account configuration against security benchmarks — CIS AWS Foundations, HIPAA, GDPR, NIST, AWS Well-Architected. It checks hundreds of AWS service configurations: IAM policies, S3 permissions, CloudTrail settings, GuardDuty status, etc.

### Basic AWS scan
```bash
prowler aws --output-formats json --output-directory ./prowler_results
```
- `prowler` → run Prowler
- `aws` → target cloud provider (also: `gcp`, `azure`, `kubernetes`)
- `--output-formats json` → output format: `json`, `csv`, `html`, `ocsf`, `sarif`
- `--output-directory ./prowler_results` → write all output files here
- **What happens:** Prowler uses your AWS credentials (from environment variables or `~/.aws/credentials`) to make read-only AWS API calls across ALL regions and ALL services, checking hundreds of configuration rules. Can take 5–20 minutes. Requires IAM permissions to read AWS service configurations.

---

### Scan specific compliance framework
```bash
prowler aws --compliance hipaa_aws --output-formats json --output-directory ./prowler_results
```
- `--compliance hipaa_aws` → only run checks that map to HIPAA requirements. Options include: `cis_1.4_aws`, `gdpr_aws`, `hipaa_aws`, `nist_800_53_revision_5_aws`, `soc2_aws`
- **What happens:** Instead of 300+ checks, runs only the subset relevant to HIPAA. Faster and focused output for compliance reporting.

---

### Set AWS credentials for Prowler
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
prowler aws --output-formats json --output-directory ./prowler_results
```
- `export` → (Bash) set an environment variable visible to all commands in this session
- `AWS_ACCESS_KEY_ID` → AWS authentication: your access key ID (the "username" part)
- `AWS_SECRET_ACCESS_KEY` → AWS authentication: your secret key (the "password" part)
- `AWS_DEFAULT_REGION` → which AWS region to connect to by default
- **What happens:** Prowler reads these environment variables (standard AWS SDK convention) to authenticate to your AWS account. **NEVER put real keys in code files — only in environment variables or AWS credentials file.**

---

## 16. Docker — Container Commands

### What is Docker?
Docker packages applications and all their dependencies into "containers" — isolated, self-contained environments that run the same way on any machine. ZAP, for example, runs as a Docker container so you don't need to install Java and ZAP manually.

### `docker build` — Build an Image
```bash
docker build -t pursh-backend:latest ./pursh/backend
```
- `docker` → the Docker CLI
- `build` → build a Docker image from a Dockerfile
- `-t pursh-backend:latest` → "tag" — give the image a name and version tag. `pursh-backend` = name, `latest` = tag
- `./pursh/backend` → the "build context" — the directory containing the `Dockerfile` and files to copy into the image
- **What happens:** Docker reads the `Dockerfile`, executes each instruction (install OS packages, copy code, set startup command), and produces a layered image stored locally. This image can then be run as a container.

---

### `docker run` — Start a Container
```bash
docker run -d -p 8002:8002 --name aisec-runner pursh-backend:latest
```
- `docker run` → create and start a container from an image
- `-d` → "detached" — run in background. Without this, Docker occupies your terminal (like uvicorn without &)
- `-p 8002:8002` → "publish port" — map host port 8002 → container port 8002. Format: `host_port:container_port`. Without this, the container's port is not reachable from outside.
- `--name aisec-runner` → give the container a memorable name (instead of a random name Docker assigns)
- `pursh-backend:latest` → the image to run
- **What happens:** Docker starts the container, running the CMD from the Dockerfile. The app inside is accessible at `http://localhost:8002`.

---

### `docker ps` — List Running Containers
```bash
docker ps
docker ps -a
```
- `docker ps` → list currently running containers
- `-a` → "all" — also show stopped containers (not just running ones)
- **What happens:** Prints table of containers with ID, image, command, ports, and status.

---

### `docker logs` — View Container Output
```bash
docker logs aisec-runner
docker logs -f aisec-runner
```
- `docker logs` → print a container's stdout/stderr output
- `aisec-runner` → the container name (from `--name` when you ran it)
- `-f` → "follow" — keep streaming new log lines (like `tail -f`). Press Ctrl+C to stop following.
- **What happens:** Shows everything the application inside the container has printed. Essential for debugging.

---

### `docker stop` and `docker rm`
```bash
docker stop aisec-runner
docker rm aisec-runner
```
- `docker stop` → gracefully stop a running container (sends SIGTERM, waits 10s, then SIGKILL)
- `docker rm` → remove a stopped container (frees disk space and lets you reuse the name)
- **What happens:** Two-step process. Stop → then remove. Or combine: `docker rm -f aisec-runner` (force stop + remove in one command).

---

### `docker-compose up` — Start All Services
```bash
docker-compose up -d
docker-compose up --build -d
```
- `docker-compose` → tool for running multi-container apps defined in `docker-compose.yml`
- `up` → start all services defined in the compose file
- `-d` → detached (background)
- `--build` → rebuild images before starting (picks up code changes)
- **What happens:** Docker reads `docker-compose.yml`, builds any images that need building, creates a network, and starts all containers (runner, dashboard, database, etc.) in the right order.

---

## 17. Supabase CLI

### What is Supabase CLI?
The Supabase CLI lets you manage your Supabase project from the terminal — run a local Supabase instance, apply database migrations, generate TypeScript types from your schema, and more.

### `supabase login` — Authenticate
```bash
supabase login
```
- `supabase` → the Supabase CLI
- `login` → opens a browser to authenticate with your Supabase account
- **What happens:** Browser opens, you log in to supabase.com, CLI receives an access token and stores it locally.

---

### `supabase db push` — Apply Schema Changes
```bash
supabase db push
```
- `supabase db` → Supabase CLI database subcommands
- `push` → apply all pending SQL migration files to your remote Supabase project
- **What happens:** Reads files in `supabase/migrations/`, compares with what's already applied, and runs any new `.sql` files against your remote Postgres database.

---

### `supabase gen types typescript` — Generate TypeScript Types
```bash
supabase gen types typescript --project-id abcdefghijklmn > database.types.ts
```
- `supabase gen types typescript` → generate TypeScript type definitions from your database schema
- `--project-id abcdefghijklmn` → your Supabase project reference ID (found in Supabase dashboard → Settings → General)
- `>` → redirect output to file
- `database.types.ts` → the output file. Import these types in your Next.js dashboard for type-safe database queries.
- **What happens:** Reads your Supabase database's public schema and generates TypeScript interfaces for every table, so TypeScript knows the shape of `scan_runs`, `ai_analyses`, etc.

---

## 18. Piping — Connecting Commands Together

### What is piping?
Piping (`|`) sends the output of one command directly as the input to another command. Instead of writing to a file and then reading it, the data flows directly from command to command in memory.

```
command1 | command2 | command3
   ^           ^           ^
output of   receives    receives
command1    command1's  command2's
  flows     output as   output as
   into     its input   its input
command2
```

---

### `|` — Pipe operator

```bash
trivy fs --format json . | python -c "
import sys, json
data = json.load(sys.stdin)
vulns = data.get('Results', [])
for r in vulns:
    for v in r.get('Vulnerabilities', []):
        if v['Severity'] in ['HIGH', 'CRITICAL']:
            print(f\"{v['Severity']}: {v['VulnerabilityID']} — {v['PkgName']}\")
"
```
- `trivy fs --format json .` → scan current directory, output JSON to stdout
- `|` → pipe the JSON output directly to the next command
- `python -c "..."` → run a Python one-liner. `-c` = "code" — the string after is Python code
- `sys.stdin` → inside the Python script, `sys.stdin` receives what was piped in (the Trivy JSON)
- **What happens:** Trivy's JSON output flows into Python without creating any intermediate file. Python filters and prints only HIGH/CRITICAL findings in a cleaner format.

---

### `grep` — Filter output
```bash
semgrep --config p/owasp-top-ten . 2>&1 | grep -i "sql\|injection\|cwe-89"
```
- `semgrep ... .` → run Semgrep (outputs to stdout)
- `2>&1` → "redirect stderr (2) to stdout (1)" — merge error output into regular output so `grep` sees everything
- `|` → pipe all output to grep
- `grep` → search for matching lines
- `-i` → case-insensitive matching
- `"sql\|injection\|cwe-89"` → match lines containing "sql" OR "injection" OR "cwe-89" (`\|` = OR in grep)
- **What happens:** Semgrep's full output flows into grep, which only lets through lines mentioning SQL/injection topics. You see just the relevant findings without scrolling through everything else.

---

### `jq` — JSON processor
```bash
cat trivy_fs.json | jq '.Results[].Vulnerabilities[] | select(.Severity == "CRITICAL") | {CVE: .VulnerabilityID, Package: .PkgName, Fix: .FixedVersion}'
```
- `cat trivy_fs.json` → print the file to stdout
- `|` → pipe to jq
- `jq` → command-line JSON processor — filter, transform, and extract JSON data
- `'.Results[].Vulnerabilities[]'` → navigate JSON: access `Results` array, then `Vulnerabilities` inside each element
- `| select(.Severity == "CRITICAL")` → jq pipe (inside jq syntax) → filter to only CRITICAL items
- `| {CVE: .VulnerabilityID, Package: .PkgName, Fix: .FixedVersion}` → reshape each item into a simpler object with just three fields
- **What happens:** Extracts only critical vulnerability details from Trivy's full JSON report, printing a clean summary of CVE ID, package name, and fix version.

---

### `tee` — Write to file AND show on screen simultaneously
```bash
semgrep --config p/owasp-top-ten --json . | tee semgrep_results.json | jq '.results | length'
```
- `semgrep ... --json .` → scan, output JSON
- `|` → pipe to tee
- `tee semgrep_results.json` → "T-junction" — writes the piped data to `semgrep_results.json` AND passes it through to stdout for the next command
- `|` → pipe to jq
- `jq '.results | length'` → count how many results are in the JSON
- **What happens:** In one pipeline: Semgrep scans → output saved to file → count printed to screen. You get both the saved file and the count without running Semgrep twice.

---

### `&&` — Run second command only if first succeeded
```bash
npm run build && npm run start
```
- `npm run build` → build the Next.js app
- `&&` → "AND" — only execute the next command if the previous one exited with code 0 (success)
- `npm run start` → start the production server
- **What happens:** If build fails (TypeScript errors, etc.), `start` is NOT run. If build succeeds, `start` runs immediately. This prevents starting a broken build.

---

### `||` — Run second command only if first FAILED
```bash
uvicorn main:app --port 8002 || echo "Runner failed to start — check main.py for errors"
```
- `||` → "OR" — only run the second command if the first one failed (non-zero exit code)
- **What happens:** If uvicorn starts successfully, the echo never runs. If uvicorn crashes immediately, the message prints.

---

### `;` — Run commands sequentially regardless of success/failure
```bash
docker stop aisec-runner ; docker rm aisec-runner ; docker run -d -p 8002:8002 --name aisec-runner pursh-backend:latest
```
- `;` → run commands one after another, regardless of whether each succeeded or failed
- **What happens:** Stops the old container (may fail if not running — that's ok), removes it (may fail if already removed — that's ok), then starts a fresh one. The `;` ensures the restart always runs even if the stop/remove steps fail.

---

### `&` — Run in background
```bash
uvicorn main:app --reload --port 8002 &
```
- `&` → run the command in the background — returns terminal control to you immediately
- **What happens:** uvicorn starts but you get your command prompt back. You can run more commands while the server runs. Combine with `jobs` to see background processes and `kill %1` to stop them.

---

## 19. Environment Variables

### What are environment variables?
Environment variables are key-value pairs stored in your shell session (or OS). Applications read them at startup to get configuration (database URLs, API keys, ports) without hardcoding sensitive values in source code.

### Set an environment variable (session only)
```powershell
# PowerShell:
$env:SUPABASE_URL = "https://abcdefg.supabase.co"
$env:DEEPSEEK_API_KEY = "sk-..."
$env:NEXT_PUBLIC_RUNNER_URL = "http://localhost:8002"

# Bash/Linux/Mac:
export SUPABASE_URL="https://abcdefg.supabase.co"
export DEEPSEEK_API_KEY="sk-..."
export NEXT_PUBLIC_RUNNER_URL="http://localhost:8002"
```
- `$env:NAME = "value"` → PowerShell syntax for setting environment variable
- `export NAME="value"` → Bash syntax
- **What happens:** The variable exists only for this terminal session. Closing the terminal loses it. The application reads it via `os.getenv("SUPABASE_URL")` in Python or `process.env.SUPABASE_URL` in Node.js.

---

### Load from `.env` file
```bash
# Manually export from .env file (Bash):
export $(cat .env | grep -v '#' | xargs)
```
- `cat .env` → print the `.env` file
- `| grep -v '#'` → pipe to grep, `-v` = "invert" — exclude lines starting with `#` (comments)
- `| xargs` → converts remaining lines into command arguments
- `export $(...)` → evaluates the result and exports each as an environment variable
- **What happens:** Every line in `.env` (like `SUPABASE_URL=https://...`) becomes an environment variable in your session.

---

### View all environment variables
```bash
# See all:
env         # Linux/Mac
Get-ChildItem Env:  # PowerShell

# See one specific variable:
echo $SUPABASE_URL        # Bash
echo $env:SUPABASE_URL    # PowerShell
```

---

## 20. Process Management

### `lsof -i` / `netstat` — Find What's Using a Port
```bash
# Linux/Mac — find what's running on port 8002:
lsof -i :8002

# Windows PowerShell:
netstat -ano | findstr :8002
```
- `lsof` → "list open files" (on Linux/Mac, everything including sockets is a "file")
- `-i :8002` → filter to just port 8002
- `netstat -ano` → display active network connections with process IDs
- `| findstr :8002` → filter output to lines containing `:8002`
- **What happens:** Shows the process ID (PID) of whatever is using port 8002. Use this when you get "address already in use" error.

---

### `kill` — Stop a Process
```bash
# Linux/Mac:
kill -9 12345
# where 12345 is the PID from lsof

# Windows PowerShell:
Stop-Process -Id 12345 -Force
# OR: taskkill /PID 12345 /F
```
- `kill` → send a signal to a process
- `-9` → signal number 9 = SIGKILL — force-terminate immediately (no cleanup). Use `-15` (SIGTERM) first for graceful shutdown.
- `12345` → the process ID
- **What happens:** Immediately terminates the process. The port is freed. You can now start a new process on that port.

---

### `Ctrl+C` — Stop Foreground Process
When a command (like uvicorn or `npm run dev`) is running in your terminal and you want to stop it:
```
Press: Ctrl + C
```
- Sends SIGINT (interrupt signal) to the running process
- **What happens:** The process gets a chance to clean up and exit gracefully. For uvicorn, it logs "Shutting down" and releases the port.

---

## 21. Log Viewing & Filtering

### `tail -f` — Follow a Log File
```bash
tail -f ./runner.log
```
- `tail` → show the end of a file
- `-f` → "follow" — keep the file open and print new lines as they are written
- `./runner.log` → the log file to follow
- **What happens:** Shows the last 10 lines of the file, then keeps printing new lines in real-time. Use this to monitor a running service. Press Ctrl+C to stop.

---

### `tail -f` with grep filter
```bash
tail -f ./runner.log | grep -i "error\|critical\|exception"
```
- `tail -f ./runner.log` → stream log file
- `|` → pipe to grep
- `grep -i "error\|critical\|exception"` → case-insensitively filter to only lines containing error/critical/exception
- **What happens:** You only see error lines in real-time — not the hundreds of normal INFO log lines cluttering the output.

---

## 22. Network & API Testing (curl)

### What is curl?
curl is a command-line tool for making HTTP requests. Use it to test your runner's API endpoints directly from the terminal without opening a browser.

### Test runner health
```bash
curl http://localhost:8002/health
```
- `curl` → the HTTP client program
- `http://localhost:8002/health` → the URL to request
- **What happens:** Sends a GET request to the runner's health endpoint. Prints the JSON response to your terminal. Useful for verifying the runner is alive.

---

### Get scanner status
```bash
curl http://localhost:8002/scanners-status | jq .
```
- `curl http://localhost:8002/scanners-status` → GET request to the batch status endpoint
- `|` → pipe the JSON response to jq
- `jq .` → `.` in jq means "print the whole JSON, formatted" (pretty-print with indentation and colors)
- **What happens:** Fetches all 28 scanner statuses and prints them formatted. Fast way to see all scanner states at once.

---

### POST request with JSON body
```bash
curl -X POST http://localhost:8002/run/semgrep \
  -H "Content-Type: application/json" \
  -d '{"target": "./pursh/backend"}'
```
- `-X POST` → "request method" — send a POST request instead of the default GET
- `-H "Content-Type: application/json"` → "header" — tell the server this request body is JSON
- `-d '{"target": "..."}'` → "data" — the request body (JSON string)
- `\` → line continuation — the command continues on the next line (cosmetic only)
- **What happens:** Sends a POST request to trigger a semgrep scan. The runner receives the JSON body and starts the scan.

---

### GET with authentication header
```bash
curl -H "Authorization: Bearer your-api-token-here" http://localhost:8002/api/results/semgrep
```
- `-H "Authorization: Bearer ..."` → "header" — send an Authorization header with a Bearer token (JWT or API key)
- **What happens:** Authenticated API call. The server validates the token and returns results only if valid.

---

### Save response to file
```bash
curl -o scan_output.json http://localhost:8002/api/results/semgrep
```
- `-o scan_output.json` → "output" — write response body to this file instead of printing to screen
- **What happens:** Downloads the scanner result JSON and saves it locally.

---

## 23. Full Startup Sequence — Everything at Once

### Complete startup from scratch (first time)

```powershell
# ── Step 1: Navigate to project root ────────────────────────────────────────
cd C:\Users\prabh\Downloads\ci_cd_seclab

# ── Step 2: Set up Python environment for runner ─────────────────────────────
cd internal\aisec\runner
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# ── Step 3: Verify runner syntax before starting ─────────────────────────────
python -m py_compile main.py storage.py
# Silence = good. Any output = syntax error, fix before continuing.

# ── Step 4: Start the runner (keep this terminal open) ───────────────────────
uvicorn main:app --reload --port 8002

# ── Open a NEW terminal for the next steps ───────────────────────────────────

# ── Step 5: Verify runner is alive ───────────────────────────────────────────
curl http://localhost:8002/health

# ── Step 6: Set up dashboard ─────────────────────────────────────────────────
cd C:\Users\prabh\Downloads\ci_cd_seclab\internal\aisec\dashboard
npm install

# ── Step 7: Start dashboard ──────────────────────────────────────────────────
npm run dev
# Dashboard now at: http://localhost:3000
```

---

### Daily startup (already set up)
```powershell
# Terminal 1 — Runner:
cd C:\Users\prabh\Downloads\ci_cd_seclab\internal\aisec\runner
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8002

# Terminal 2 — Dashboard:
cd C:\Users\prabh\Downloads\ci_cd_seclab\internal\aisec\dashboard
npm run dev
```

---

### Run all scanners manually (one by one)
```powershell
# Navigate to project root:
cd C:\Users\prabh\Downloads\ci_cd_seclab

# 1. SAST — Semgrep:
semgrep --config p/owasp-top-ten --config p/security-audit --json --exclude-dir venv --exclude-dir node_modules ./internal/aisec > internal/aisec/runner/scan_results/semgrep_results.json

# 2. Filesystem vulnerabilities — Trivy:
trivy fs --format json --output internal/aisec/runner/scan_results/trivy_fs_results.json .

# 3. SBOM generation — Syft:
syft dir:. --output cyclonedx-json=internal/aisec/runner/scan_results/sbom.cdx.json

# 4. SBOM vulnerability scan — Grype:
grype sbom:internal/aisec/runner/scan_results/sbom.cdx.json --output json > internal/aisec/runner/scan_results/grype_results.json

# 5. Secrets — Gitleaks:
gitleaks detect --source . --report-format json --report-path internal/aisec/runner/scan_results/gitleaks_results.json

# 6. IaC — Checkov:
checkov -d . --output json > internal/aisec/runner/scan_results/checkov_results.json

# 7. Container image — Trivy (build image first):
docker build -t pursh-backend:latest ./internal/aisec
trivy image --format json --output internal/aisec/runner/scan_results/trivy_image_results.json pursh-backend:latest

# 8. DAST — ZAP baseline (runner must be running first):
docker run --rm -v ${PWD}/internal/aisec/runner/scan_results:/zap/wrk ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://host.docker.internal:8002 -J zap_baseline.json
```

---

### Verify all scan results were created
```powershell
ls internal\aisec\runner\scan_results\
# Should show: semgrep_results.json, trivy_fs_results.json, sbom.cdx.json,
#              grype_results.json, gitleaks_results.json, checkov_results.json,
#              trivy_image_results.json, zap_baseline.json
```

---

### Check runner sees all results
```bash
curl http://localhost:8002/scanners-status | jq '.scanners | to_entries[] | {scanner: .key, status: .value.status}'
```
- `to_entries[]` → converts the object into an array of `{key, value}` pairs
- `{scanner: .key, status: .value.status}` → reshape each to just show scanner name + status
- **What happens:** Prints a clean list of all 28 scanners and their current status (pass/fail/no_data) from the runner's perspective.

---

## Quick Reference Card

```
START RUNNER:     uvicorn main:app --reload --port 8002
START DASHBOARD:  npm run dev
CHECK RUNNER:     curl http://localhost:8002/health
ALL STATUSES:     curl http://localhost:8002/scanners-status | jq .

SAST:             semgrep --config p/owasp-top-ten --json . > semgrep_results.json
DAST:             docker run --rm ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t <url>
SCA (fs):         trivy fs --format json . > trivy_fs.json
SCA (image):      trivy image --format json <image:tag> > trivy_image.json
SBOM:             syft dir:. --output cyclonedx-json=sbom.cdx.json
SBOM scan:        grype sbom:sbom.cdx.json --output json > grype.json
SECRETS:          gitleaks detect --source . --report-format json --report-path gitleaks.json
IAC:              checkov -d . --output json > checkov.json
CLOUD:            prowler aws --output-formats json --output-directory ./prowler_results

SSH CONNECT:      ssh -i ~/.ssh/key.pem ubuntu@<ip>
COPY TO SERVER:   scp ./file ubuntu@<ip>:/home/ubuntu/
TUNNEL:           ssh -L 8002:localhost:8002 ubuntu@<ip>

KILL PORT:        lsof -i :8002   → kill -9 <PID>
PIPE + FILTER:    command | jq .
PIPE + GREP:      command 2>&1 | grep -i "error"
SAVE + SHOW:      command | tee output.json | jq '.results | length'
```

---

*File: `internal/Learning/Commands.md` | Role: Application Security Engineer | Coverage: All commands to run AISec platform + 9 scanners, word-by-word breakdown, piping, SSH, process management*
