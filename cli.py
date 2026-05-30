"""
cli.py — Modo consola del gestor de credenciales.

Se usa cuando app.py recibe argumentos. Toda la lógica vive en core.py.
"""

from __future__ import annotations

import argparse
import sys

import core


def _print_result(res: core.ActionResult) -> int:
    icon = "OK" if res.ok else "ERROR"
    print(f"[{icon}] {res.message}")
    for w in res.warnings:
        print(f"  ! {w}")
    return 0 if res.ok else 1


def cmd_list() -> int:
    profiles = core.list_profiles()
    if not profiles:
        print("No se encontraron perfiles en ~/.ssh.")
        return 0
    print(f"{'':2} {'PERFIL':<22} {'CLAVE':<9} {'GIT USER':<14} EMAIL")
    print("-" * 70)
    for p in profiles:
        mark = "*" if p.is_active else " "
        print(
            f"{mark:<2} {p.name:<22} {p.key_type:<9} "
            f"{(p.git_user or '-'):<14} {p.git_email or '-'}"
        )
    print("\n(*) = perfil activo actualmente")
    return 0


def cmd_status() -> int:
    st = core.current_root_state()
    active = st["active"]
    print("== Estado actual ==")
    print(f"  Perfil activo : {active.name if active else '(no identificado)'}")
    print(f"  Tipo de clave : {st['key_type']}")
    print(f"  Git user      : {st['git_user'] or '-'}")
    print(f"  Git email     : {st['git_email'] or '-'}")
    if st["public_key"]:
        print(f"  Clave pública : {st['public_key'][:50]}...")
    return 0


def cmd_show_gitconfig(name: str | None) -> int:
    if name:
        prof = next((p for p in core.list_profiles() if p.name == name), None)
        if prof is None:
            print(f"No existe el perfil '{name}'.")
            return 1
        print(f"== .gitconfig del perfil '{name}' ==")
        print(core.read_gitconfig(prof.path / ".gitconfig") or "(el perfil no tiene .gitconfig)")
    else:
        print("== ~/.gitconfig global ==")
        print(core.read_gitconfig() or "(vacío)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cambia-credenciales",
        description="Gestor de perfiles de credenciales SSH/Git. Sin argumentos abre la GUI.",
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("-l", "--list", action="store_true", help="lista los perfiles disponibles")
    g.add_argument("-s", "--status", action="store_true", help="muestra el perfil activo y el gitconfig")
    g.add_argument("-u", "--use", metavar="NOMBRE", help="activa el perfil indicado")
    g.add_argument("--save", metavar="NOMBRE", help="guarda la credencial activa como perfil nuevo")
    g.add_argument("--rename", nargs=2, metavar=("VIEJO", "NUEVO"), help="renombra un perfil")
    g.add_argument("--delete", metavar="NOMBRE", help="borra un perfil")
    g.add_argument(
        "--show-gitconfig",
        nargs="?",
        const=None,
        default="__omit__",
        metavar="PERFIL",
        help="muestra el gitconfig global, o el de un perfil si se indica",
    )

    args = parser.parse_args(argv)

    if args.list:
        return cmd_list()
    if args.status:
        return cmd_status()
    if args.use:
        return _print_result(core.activate(args.use))
    if args.save:
        return _print_result(core.save_current_as(args.save))
    if args.rename:
        return _print_result(core.rename_profile(args.rename[0], args.rename[1]))
    if args.delete:
        return _print_result(core.delete_profile(args.delete))
    if args.show_gitconfig != "__omit__":
        return cmd_show_gitconfig(args.show_gitconfig)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
