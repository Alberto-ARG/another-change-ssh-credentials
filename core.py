"""
core.py — Lógica del gestor de perfiles de credenciales SSH/Git.

Sin dependencias de UI: tanto la GUI (gui.py) como la consola (cli.py) usan
estas funciones. Multi-OS: usa pathlib.Path.home() y solo aplica chmod en
sistemas POSIX (Linux/Mac); en Windows se saltea.

Modelo:
- ~/.ssh actúa como "credencial activa".
- Cada subcarpeta de ~/.ssh (salvo _backups) es un PERFIL guardado.
- Activar un perfil = backup del estado actual -> copiar las claves/known_hosts
  del perfil a la raíz de ~/.ssh -> reemplazar ~/.gitconfig si el perfil trae uno.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# --- Rutas base (multi-OS) ---------------------------------------------------
SSH_DIR = Path.home() / ".ssh"
GITCONFIG = Path.home() / ".gitconfig"
BACKUP_DIR = SSH_DIR / "_backups"
RESERVED_NAMES = {"_backups"}

# Patrones de archivos que se consideran "credencial" y se mueven entre perfiles.
# Se excluyen los *.old (backups viejos que no aportan).
CRED_GLOBS = ["id_*", "*.pub", "known_hosts", "config"]

IS_POSIX = os.name == "posix"


# --- Modelo ------------------------------------------------------------------
@dataclass
class Profile:
    name: str
    path: Path
    key_type: str = "?"          # rsa / ed25519 / ecdsa / dsa / ?
    public_key: str | None = None  # contenido de la .pub (sin secreto)
    git_user: str | None = None
    git_email: str | None = None
    has_gitconfig: bool = False
    is_active: bool = False


@dataclass
class ActionResult:
    """Resultado de una operación, para que GUI/CLI lo muestren igual."""
    ok: bool
    message: str
    warnings: list[str] = field(default_factory=list)


# --- Helpers internos --------------------------------------------------------
def _now_tag() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _cred_files(folder: Path) -> list[Path]:
    """Archivos de credencial dentro de una carpeta (sin *.old, sin .gitconfig)."""
    found: list[Path] = []
    for pattern in CRED_GLOBS:
        for p in folder.glob(pattern):
            if p.is_file() and not p.name.endswith(".old"):
                found.append(p)
    # dedup conservando orden
    seen: set[str] = set()
    unique: list[Path] = []
    for p in found:
        if p.name not in seen:
            seen.add(p.name)
            unique.append(p)
    return unique


def _detect_key_type(folder: Path) -> str:
    for name, kind in (
        ("id_ed25519", "ed25519"),
        ("id_rsa", "rsa"),
        ("id_ecdsa", "ecdsa"),
        ("id_dsa", "dsa"),
    ):
        if (folder / name).exists() or (folder / f"{name}.pub").exists():
            return kind
    # fallback: cualquier id_* presente
    for p in folder.glob("id_*"):
        return p.name.replace("id_", "").replace(".pub", "") or "?"
    return "?"


def _read_public_key(folder: Path) -> str | None:
    pubs = sorted(folder.glob("*.pub"))
    if not pubs:
        return None
    try:
        return pubs[0].read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _parse_gitconfig_user(path: Path) -> tuple[str | None, str | None]:
    """Devuelve (name, email) leídos de un .gitconfig estilo INF de git."""
    if not path.exists():
        return None, None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    name = email = None
    in_user = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_user = line.lower().startswith("[user")
            continue
        if not in_user or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip().lower()
        val = val.strip()
        if key == "name":
            name = val
        elif key == "email":
            email = val
    return name, email


def _apply_posix_perms() -> None:
    """En Linux/Mac asegura permisos correctos de SSH; en Windows no aplica."""
    if not IS_POSIX:
        return
    try:
        SSH_DIR.chmod(0o700)
        for p in SSH_DIR.iterdir():
            if not p.is_file():
                continue
            if p.suffix == ".pub" or p.name.startswith("known_hosts") or p.name == "config":
                p.chmod(0o644)
            elif p.name.startswith("id_"):
                p.chmod(0o600)
    except OSError:
        pass


def _is_profile_dir(folder: Path) -> bool:
    if not folder.is_dir() or folder.name in RESERVED_NAMES:
        return False
    has_key = any(folder.glob("id_*"))
    has_hosts = (folder / "known_hosts").exists()
    return has_key or has_hosts


# --- API pública -------------------------------------------------------------
def list_profiles() -> list[Profile]:
    """Lista los perfiles (subcarpetas de ~/.ssh con credenciales)."""
    if not SSH_DIR.exists():
        return []
    active_pub = _read_public_key(SSH_DIR)
    profiles: list[Profile] = []
    for folder in sorted(SSH_DIR.iterdir()):
        if not _is_profile_dir(folder):
            continue
        gitcfg = folder / ".gitconfig"
        name, email = _parse_gitconfig_user(gitcfg)
        pub = _read_public_key(folder)
        profiles.append(
            Profile(
                name=folder.name,
                path=folder,
                key_type=_detect_key_type(folder),
                public_key=pub,
                git_user=name,
                git_email=email,
                has_gitconfig=gitcfg.exists(),
                is_active=(pub is not None and pub == active_pub),
            )
        )
    return profiles


def active_profile() -> Profile | None:
    for p in list_profiles():
        if p.is_active:
            return p
    return None


def current_root_state() -> dict:
    """Estado de la credencial activa en la raíz de ~/.ssh + gitconfig global."""
    name, email = _parse_gitconfig_user(GITCONFIG)
    return {
        "public_key": _read_public_key(SSH_DIR),
        "key_type": _detect_key_type(SSH_DIR),
        "git_user": name,
        "git_email": email,
        "active": active_profile(),
    }


def backup_current(tag: str) -> Path:
    """Copia las credenciales de la raíz + gitconfig global a ~/.ssh/_backups/<ts>_<tag>/."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    safe_tag = re.sub(r"[^\w.-]+", "-", tag).strip("-") or "backup"
    dest = BACKUP_DIR / f"{_now_tag()}_{safe_tag}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in _cred_files(SSH_DIR):
        shutil.copy2(f, dest / f.name)
    if GITCONFIG.exists():
        shutil.copy2(GITCONFIG, dest / ".gitconfig")
    return dest


def activate(name: str) -> ActionResult:
    """Activa el perfil `name`: backup -> limpiar claves viejas -> copiar -> gitconfig."""
    profile = next((p for p in list_profiles() if p.name == name), None)
    if profile is None:
        return ActionResult(False, f"No existe el perfil '{name}'.")

    warnings: list[str] = []
    backup = backup_current(f"antes-de-{name}")

    # Limpiar de la raíz los archivos de credencial del perfil activo anterior,
    # para no dejar claves mezcladas (los perfiles usan nombres distintos:
    # id_rsa vs id_ed25519).
    for f in _cred_files(SSH_DIR):
        try:
            f.unlink()
        except OSError as exc:
            warnings.append(f"No se pudo borrar {f.name}: {exc}")

    # Copiar las credenciales del perfil a la raíz.
    copied: list[str] = []
    for f in _cred_files(profile.path):
        shutil.copy2(f, SSH_DIR / f.name)
        copied.append(f.name)

    # gitconfig: reemplazo completo si el perfil trae uno; si no, avisar.
    profile_gitconfig = profile.path / ".gitconfig"
    if profile_gitconfig.exists():
        shutil.copy2(profile_gitconfig, GITCONFIG)
    else:
        warnings.append(
            f"El perfil '{name}' no trae .gitconfig: se mantiene el ~/.gitconfig actual."
        )

    _apply_posix_perms()

    return ActionResult(
        True,
        f"Perfil '{name}' activado. Copiado: {', '.join(copied) or '(nada)'}. "
        f"Backup en: {backup}",
        warnings,
    )


def save_current_as(name: str) -> ActionResult:
    """Guarda la credencial activa de la raíz como un perfil nuevo."""
    clean = name.strip()
    if not clean:
        return ActionResult(False, "El nombre no puede estar vacío.")
    if clean in RESERVED_NAMES:
        return ActionResult(False, f"'{clean}' es un nombre reservado.")
    dest = SSH_DIR / clean
    if dest.exists():
        return ActionResult(False, f"Ya existe un perfil llamado '{clean}'.")
    dest.mkdir(parents=True)
    copied: list[str] = []
    for f in _cred_files(SSH_DIR):
        shutil.copy2(f, dest / f.name)
        copied.append(f.name)
    if GITCONFIG.exists():
        shutil.copy2(GITCONFIG, dest / ".gitconfig")
        copied.append(".gitconfig")
    return ActionResult(True, f"Perfil '{clean}' creado con: {', '.join(copied) or '(nada)'}.")


def rename_profile(old: str, new: str) -> ActionResult:
    clean = new.strip()
    if not clean or clean in RESERVED_NAMES:
        return ActionResult(False, "Nombre nuevo inválido.")
    src = SSH_DIR / old
    dst = SSH_DIR / clean
    if not _is_profile_dir(src):
        return ActionResult(False, f"No existe el perfil '{old}'.")
    if dst.exists():
        return ActionResult(False, f"Ya existe un perfil llamado '{clean}'.")
    src.rename(dst)
    return ActionResult(True, f"Perfil '{old}' renombrado a '{clean}'.")


def delete_profile(name: str) -> ActionResult:
    """Borra una subcarpeta de perfil. La confirmación la maneja la UI."""
    target = SSH_DIR / name
    if not _is_profile_dir(target):
        return ActionResult(False, f"No existe el perfil '{name}'.")
    warnings: list[str] = []
    prof = next((p for p in list_profiles() if p.name == name), None)
    if prof and prof.is_active:
        warnings.append("Era el perfil activo; la credencial en la raíz de ~/.ssh sigue intacta.")
    shutil.rmtree(target)
    return ActionResult(True, f"Perfil '{name}' borrado.", warnings)


def read_gitconfig(path: Path | None = None) -> str:
    """Devuelve el texto del gitconfig global (o de un perfil si se pasa path)."""
    target = path if path is not None else GITCONFIG
    if not target.exists():
        return ""
    try:
        return target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"(no se pudo leer {target}: {exc})"


def write_global_gitconfig(text: str) -> ActionResult:
    """Escribe el ~/.gitconfig global haciendo backup del anterior."""
    if GITCONFIG.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(GITCONFIG, BACKUP_DIR / f"{_now_tag()}_gitconfig.bak")
    try:
        GITCONFIG.write_text(text, encoding="utf-8")
    except OSError as exc:
        return ActionResult(False, f"No se pudo guardar el gitconfig: {exc}")
    return ActionResult(True, "~/.gitconfig guardado (backup del anterior creado).")
