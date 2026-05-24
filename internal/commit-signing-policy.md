# Commit Signing Policy

All commits merged to `main` **must be GPG-signed**. This is enforced by branch
protection rules (see [`.github/branch-protection.md`](.github/branch-protection.md)).
Unsigned commits are rejected at merge time.

## Why signed commits?

Signed commits cryptographically bind a commit to your GPG key, preventing
impersonation. An unsigned commit with your name and email can be forged by
anyone with push access. Signing closes that gap and is required by our SCM
hardening posture (CLAUDE.md §5).

---

## Setup (one-time)

### 1. Generate a GPG key (skip if you already have one)

```bash
gpg --full-generate-key
# Choose: RSA and RSA (default), 4096 bits, no expiry (or 2y), real name + email
```

### 2. List your key and copy the key ID

```bash
gpg --list-secret-keys --keyid-format=long
# Output example:
# sec   rsa4096/3AA5C34371567BD2 2024-01-01 [SC]
#       key fingerprint here
# uid   Your Name <you@example.com>
```

Copy the key ID after the `/` on the `sec` line (e.g., `3AA5C34371567BD2`).

### 3. Tell Git to use your key

```bash
git config --global user.signingkey 3AA5C34371567BD2
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

### 4. Export your public key and add it to GitHub

```bash
gpg --armor --export 3AA5C34371567BD2
# Copy the output, then:
# GitHub → Settings → SSH and GPG keys → New GPG key → paste
```

### 5. Verify a signed commit

```bash
git log --show-signature -1
# Should show: "Good signature from <your name>"
```

---

## SSH signing (alternative to GPG)

GitHub also supports SSH commit signing. If you prefer SSH keys:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

Add the same SSH key to GitHub under **Settings → SSH and GPG keys → Signing keys**
(distinct from authentication keys).

---

## CI / GitHub Actions

GitHub Actions commits (bot commits) use the `github-actions[bot]` identity
which GitHub signs automatically. No additional configuration is required for
the CI runner.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `error: gpg failed to sign the data` | Run `export GPG_TTY=$(tty)` in your shell profile |
| Commits show "Unverified" on GitHub | Ensure the email on the GPG key matches your GitHub verified email |
| `pre-commit` fails on signing | Pre-commit hooks run before signing — this is expected behavior |
