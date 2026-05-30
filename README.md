# Credential Switcher (SSH / Git)

A **portable** SSH/Git credential profile manager. It lets you switch between
different identities (SSH keys + `~/.gitconfig`) in one click, with **automatic
backups** before anything is replaced. It includes a **GUI** and **CLI**, and runs on
**Windows, macOS, and Linux**.

---

## Why?

If you use multiple Git identities (work, personal, another account), each one
has its own SSH key pair and usually its own `user.name` / `user.email` (and sometimes
more Git config). Doing this manually means copying files and editing `.gitconfig`
every time. This tool automates it and, most importantly, **never overwrites anything
without creating a backup first**.

---

## How it works (model)

- `~/.ssh` is the **active credential** (what Git/SSH uses right now).
- Each **subfolder** inside `~/.ssh` (except `_backups`) is a saved **profile** with
  its own keys (`id_rsa`, `id_ed25519`, etc.), `known_hosts`, and optional `.gitconfig`.
- **Activating** a profile does, in order:
  1. **Backs up** the current active credential + `~/.gitconfig` into
     `~/.ssh/_backups/<timestamp>_.../`.
  2. **Cleans** old keys from `~/.ssh` root (to avoid mixing `id_rsa` with `id_ed25519`).
  3. **Copies** keys and `known_hosts` from the selected profile into `~/.ssh`.
  4. If the profile has a `.gitconfig`, it **replaces** global `~/.gitconfig`
     (with backup). If not, it **keeps current** and shows a warning.
  5. On Linux/macOS it applies SSH permissions (`600` / `644` / `700`); on Windows
     this step is skipped.

> A profile is considered "active" when its public key matches the one currently in
> `~/.ssh`. If your current credential is not saved as a profile, it appears as
> *"(not identified)"*. Save it first with **+ New profile** / `--save`.

---

## Requirements

- **Python 3.10+**
- For GUI: `customtkinter` -> `pip install -r requirements.txt`
  (CLI works with standard library only)

### Install Python (Windows, with winget)

```powershell
winget install Python.Python.3.12
```

Then in the project folder:

```powershell
pip install -r requirements.txt
```

---

## Usage - Graphical Interface (GUI)

To open it **without a console window in the background**, use any of these:

| Launcher | What it does |
|---|---|
| **`Cambia Credenciales.vbs`** | Double click -> opens **only** the GUI (no flicker). Best option. |
| **`ejecutar.bat`** | Double click -> opens GUI with `pythonw` (brief cmd flicker). |
| `pythonw app.py` | Manual, no console. |
| `python app.py` | Manual, **with** console (useful for debugging). |

For a desktop shortcut with icon: right click `Cambia Credenciales.vbs` ->
*Create shortcut* -> move it to Desktop.

The window has two tabs:

- **Profiles**: lists all profiles and marks the active one (`ACTIVE`). Buttons:
  **Activate**, **+ New profile** (save current active credential), **Rename**,
  **Delete**. Select a profile with the radio button for rename/delete.
- **Git Config**: shows and allows editing/saving global `~/.gitconfig`
  (with backup), and viewing each profile `.gitconfig` for comparison.

---

## Usage - Command Line (CLI)

Without arguments it opens GUI; with arguments it runs in CLI mode:

| Command | Action |
|---|---|
| `python app.py --list` | List profiles and mark active one (`*`) |
| `python app.py --status` | Active profile + `user.name` / `user.email` from gitconfig |
| `python app.py --use NAME` | Activate a profile (with backup) |
| `python app.py --save NAME` | Save current active credential as a new profile |
| `python app.py --rename OLD NEW` | Rename a profile |
| `python app.py --delete NAME` | Delete a profile |
| `python app.py --show-gitconfig [PROFILE]` | Show global gitconfig or profile gitconfig |

Examples:

```powershell
python app.py --list
python app.py --save current-sanatorio   # save your current credential first
python app.py --use backup               # switch to identity "backup"
python app.py --status
```

---

## Backups and restore

Every operation that overwrites files creates a copy in
`~/.ssh/_backups/<timestamp>_<reason>/`
(keys + `known_hosts` + `.gitconfig`). To roll back, you can:

- Re-activate the previous profile (if saved), or
- Manually copy files from the corresponding backup folder.

The `_backups` folder is **excluded** from profile detection.

---

## Package as portable executable (.exe)

To distribute it without requiring Python on target machines:

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name credential-switcher app.py
```

This creates `dist/credential-switcher.exe`, which includes Python runtime and
libraries. `--windowed` builds it **without console** (ideal for GUI).

The binary is **OS-specific**: build on each target OS (Windows/macOS/Linux).
Source code stays the same across all three.
If you also want CLI from `.exe`, build **without** `--windowed`
(or build two binaries: GUI and console).

---

## Project structure

```text
app.py                    Entry point: GUI (no args) / CLI (with args)
core.py                   Logic: profiles, backup, activate, gitconfig (no UI)
gui.py                    customtkinter UI (Profiles / Git Config tabs)
cli.py                    Console commands (argparse)
requirements.txt          Dependencies (customtkinter)
Cambia Credenciales.vbs   GUI launcher without console (recommended)
ejecutar.bat              GUI launcher with pythonw
README.md                 This file
```

`core.py` is UI-independent: both GUI and CLI call the same functions, so behavior
is consistent in both modes.

---

## Security notes

- The program only reads/writes inside `~/.ssh` and `~/.gitconfig`.
- It never prints private key contents (`id_*` without `.pub`).
- On Linux/macOS it automatically fixes SSH file permissions when activating a profile.
