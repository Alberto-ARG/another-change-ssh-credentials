"""
gui.py — Interfaz gráfica (customtkinter) del gestor de credenciales.

Se abre cuando app.py no recibe argumentos. Toda la lógica vive en core.py;
esta capa solo dibuja y delega.
"""

from __future__ import annotations

import tkinter.messagebox as mbox

import customtkinter as ctk

import core

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Cambia Credenciales — SSH / Git")
        self.geometry("760x560")
        self.minsize(680, 480)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        self.tab_profiles = self.tabs.add("Perfiles")
        self.tab_git = self.tabs.add("Git Config")

        self.status = ctk.CTkLabel(self, text="", anchor="w", text_color="#9ad")
        self.status.pack(fill="x", padx=16, pady=(0, 10))

        self._build_profiles_tab()
        self._build_git_tab()
        self.refresh()

    # ---- barra de estado ----
    def set_status(self, res_or_text, error: bool = False) -> None:
        if isinstance(res_or_text, core.ActionResult):
            txt = res_or_text.message
            if res_or_text.warnings:
                txt += "  ·  " + "  ·  ".join(res_or_text.warnings)
            error = not res_or_text.ok
        else:
            txt = str(res_or_text)
        self.status.configure(text=txt, text_color="#f88" if error else "#9ad")

    # ---- Tab Perfiles ----
    def _build_profiles_tab(self) -> None:
        self.header = ctk.CTkLabel(
            self.tab_profiles, text="", anchor="w", justify="left",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.header.pack(fill="x", padx=8, pady=(8, 4))

        self.list_frame = ctk.CTkScrollableFrame(self.tab_profiles, label_text="Perfiles disponibles")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=4)

        btns = ctk.CTkFrame(self.tab_profiles, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=(4, 8))
        ctk.CTkButton(btns, text="+ Nuevo perfil", command=self.on_new).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Renombrar", command=self.on_rename).pack(side="left", padx=4)
        ctk.CTkButton(
            btns, text="Borrar", fg_color="#a33", hover_color="#c44", command=self.on_delete
        ).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Refrescar", command=self.refresh).pack(side="right", padx=4)

        self.selected: str | None = None

    def _render_profiles(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        profiles = core.list_profiles()
        if not profiles:
            ctk.CTkLabel(self.list_frame, text="No se encontraron perfiles en ~/.ssh").pack(pady=20)
            return

        for p in profiles:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", padx=4, pady=3)

            radio = ctk.CTkRadioButton(
                row, text="", width=24,
                command=lambda n=p.name: self._select(n),
                variable=self._sel_var, value=p.name,
            )
            radio.pack(side="left", padx=(8, 0))

            tag = "  ● ACTIVO" if p.is_active else ""
            info = (
                f"{p.name}{tag}\n"
                f"{p.key_type}  ·  {p.git_user or 'sin git user'}  ·  "
                f"{p.git_email or 'sin email'}  ·  "
                f"{'con .gitconfig' if p.has_gitconfig else 'sin .gitconfig'}"
            )
            ctk.CTkLabel(
                row, text=info, justify="left", anchor="w",
                text_color="#7e7" if p.is_active else None,
            ).pack(side="left", fill="x", expand=True, padx=8, pady=4)

            ctk.CTkButton(
                row, text="Activar", width=80,
                command=lambda n=p.name: self.on_activate(n),
            ).pack(side="right", padx=8)

    def _select(self, name: str) -> None:
        self.selected = name

    # ---- Tab Git Config ----
    def _build_git_tab(self) -> None:
        top = ctk.CTkFrame(self.tab_git, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 0))
        ctk.CTkLabel(top, text="~/.gitconfig global (editable):",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Guardar", width=90, command=self.on_save_gitconfig).pack(side="right")

        self.global_box = ctk.CTkTextbox(self.tab_git, height=180)
        self.global_box.pack(fill="both", expand=True, padx=8, pady=4)

        sel = ctk.CTkFrame(self.tab_git, fg_color="transparent")
        sel.pack(fill="x", padx=8, pady=(8, 0))
        ctk.CTkLabel(sel, text="Ver .gitconfig del perfil:",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.profile_menu = ctk.CTkOptionMenu(sel, values=["—"], command=self.on_view_profile_git)
        self.profile_menu.pack(side="left", padx=8)

        self.profile_box = ctk.CTkTextbox(self.tab_git, height=160)
        self.profile_box.configure(state="disabled")
        self.profile_box.pack(fill="both", expand=True, padx=8, pady=4)

    def _load_git_tab(self) -> None:
        self.global_box.delete("1.0", "end")
        self.global_box.insert("1.0", core.read_gitconfig())
        names = [p.name for p in core.list_profiles()] or ["—"]
        self.profile_menu.configure(values=names)
        self.profile_menu.set(names[0])
        self.on_view_profile_git(names[0])

    def on_view_profile_git(self, name: str) -> None:
        prof = next((p for p in core.list_profiles() if p.name == name), None)
        text = core.read_gitconfig(prof.path / ".gitconfig") if prof else ""
        if prof and not prof.has_gitconfig:
            text = "(este perfil no tiene .gitconfig propio)"
        self.profile_box.configure(state="normal")
        self.profile_box.delete("1.0", "end")
        self.profile_box.insert("1.0", text)
        self.profile_box.configure(state="disabled")

    def on_save_gitconfig(self) -> None:
        text = self.global_box.get("1.0", "end-1c")
        self.set_status(core.write_global_gitconfig(text))
        self.refresh()

    # ---- acciones ----
    def on_activate(self, name: str) -> None:
        if not mbox.askyesno("Activar perfil",
                             f"¿Activar el perfil '{name}'?\nSe hará un backup automático del estado actual."):
            return
        self.set_status(core.activate(name))
        self.refresh()

    def on_new(self) -> None:
        dlg = ctk.CTkInputDialog(text="Nombre del nuevo perfil (guarda la credencial activa):",
                                 title="Nuevo perfil")
        name = dlg.get_input()
        if name:
            self.set_status(core.save_current_as(name))
            self.refresh()

    def on_rename(self) -> None:
        if not self.selected:
            self.set_status("Seleccioná un perfil (radio button) para renombrar.", error=True)
            return
        dlg = ctk.CTkInputDialog(text=f"Nuevo nombre para '{self.selected}':", title="Renombrar perfil")
        new = dlg.get_input()
        if new:
            self.set_status(core.rename_profile(self.selected, new))
            self.refresh()

    def on_delete(self) -> None:
        if not self.selected:
            self.set_status("Seleccioná un perfil (radio button) para borrar.", error=True)
            return
        if not mbox.askyesno("Borrar perfil", f"¿Borrar el perfil '{self.selected}'? Esta acción no se puede deshacer."):
            return
        self.set_status(core.delete_profile(self.selected))
        self.selected = None
        self.refresh()

    # ---- refresco general ----
    def refresh(self) -> None:
        if not hasattr(self, "_sel_var"):
            self._sel_var = ctk.StringVar(value="")
        st = core.current_root_state()
        active = st["active"]
        self.header.configure(
            text=(
                f"Activo: {active.name if active else '(no identificado)'}   |   "
                f"clave {st['key_type']}   |   "
                f"git: {st['git_user'] or '-'} <{st['git_email'] or '-'}>"
            )
        )
        self._render_profiles()
        self._load_git_tab()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
