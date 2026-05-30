# Cambia Credenciales (SSH / Git)

Gestor **portable** de perfiles de credenciales SSH/Git. Permite alternar entre
distintas identidades (claves SSH + `~/.gitconfig`) con un clic, haciendo **backup
automático** de todo lo que reemplaza. Tiene **interfaz gráfica** y **modo consola**,
y funciona en **Windows, macOS y Linux**.

---

## ¿Por qué?

Si usás varias identidades de Git (trabajo, personal, otra cuenta), cada una tiene su
par de claves SSH y, normalmente, su propio `user.name` / `user.email` (y a veces más
configuración de git). Cambiar a mano implica copiar archivos y editar el `.gitconfig`
cada vez. Este programa lo automatiza y, sobre todo, **nunca pisa nada sin antes
hacer una copia de seguridad**.

---

## Cómo funciona (modelo)

- `~/.ssh` es la **credencial activa** (la que usa git/ssh ahora mismo).
- Cada **subcarpeta** de `~/.ssh` (salvo `_backups`) es un **perfil** guardado: tiene
  sus propias claves (`id_rsa`, `id_ed25519`, …), su `known_hosts` y, opcionalmente,
  un `.gitconfig`.
- **Activar** un perfil hace, en orden:
  1. **Backup** de la credencial activa + `~/.gitconfig` en `~/.ssh/_backups/<fecha>_.../`.
  2. **Limpia** las claves anteriores de la raíz (para no mezclar `id_rsa` con `id_ed25519`).
  3. **Copia** las claves y `known_hosts` del perfil a la raíz de `~/.ssh`.
  4. Si el perfil trae `.gitconfig`, **reemplaza** el `~/.gitconfig` global (con backup).
     Si no trae, **deja el actual y avisa**.
  5. En Linux/Mac aplica permisos correctos (`600`/`644`/`700`); en Windows no aplica.

> Un perfil se considera "activo" cuando su clave pública coincide con la que está en
> la raíz de `~/.ssh`. Si tu credencial actual no está guardada como perfil, aparecerá
> como *"no identificado"* — guardala con **+ Nuevo perfil** / `--save`.

---

## Requisitos

- **Python 3.10+**
- Para la GUI: `customtkinter` → `pip install -r requirements.txt`
  (la CLI funciona solo con la librería estándar)

### Instalar Python (Windows, con winget)

```powershell
winget install Python.Python.3.12
```

Luego, en la carpeta del proyecto:

```powershell
pip install -r requirements.txt
```

---

## Uso — Interfaz gráfica (GUI)

Para abrirla **sin ventana de consola de fondo**, usá cualquiera de estos:

| Lanzador | Qué hace |
|---|---|
| **`Cambia Credenciales.vbs`** | Doble clic → abre **solo** la GUI (cero parpadeo). El más limpio. |
| **`ejecutar.bat`** | Doble clic → abre la GUI con `pythonw` (parpadeo brevísimo de cmd). |
| `pythonw app.py` | Manual, sin consola. |
| `python app.py` | Manual, **con** consola (útil para ver errores). |

> 💡 Para un acceso directo con ícono: clic derecho sobre `Cambia Credenciales.vbs`
> → *Crear acceso directo* → movelo al escritorio.

La ventana tiene dos pestañas:

- **Perfiles** — lista todos los perfiles y marca el activo (● ACTIVO). Botones:
  **Activar**, **+ Nuevo perfil** (guarda la credencial activa), **Renombrar**,
  **Borrar**. Seleccioná un perfil con el radio button para renombrar/borrar.
- **Git Config** — muestra y permite **editar y guardar** el `~/.gitconfig` global
  (con backup), y ver el `.gitconfig` de cada perfil para comparar.

---

## Uso — Consola (CLI)

Sin argumentos abre la GUI; con argumentos entra en modo consola:

| Comando | Acción |
|---|---|
| `python app.py --list` | Lista los perfiles y marca el activo (`*`) |
| `python app.py --status` | Perfil activo + `user.name`/`email` del gitconfig |
| `python app.py --use NOMBRE` | Activa un perfil (con backup) |
| `python app.py --save NOMBRE` | Guarda la credencial activa como perfil nuevo |
| `python app.py --rename VIEJO NUEVO` | Renombra un perfil |
| `python app.py --delete NOMBRE` | Borra un perfil |
| `python app.py --show-gitconfig [PERFIL]` | Muestra el gitconfig global o el de un perfil |

Ejemplos:

```powershell
python app.py --list
python app.py --save sanatorio-actual   # guardá tu credencial actual primero
python app.py --use copia               # cambia a la identidad "copia"
python app.py --status
```

---

## Backups y restauración

Cada operación que pisa algo deja una copia en `~/.ssh/_backups/<fecha_hora>_<motivo>/`
(claves + `known_hosts` + `.gitconfig`). Para volver atrás, podés:

- Activar de nuevo el perfil anterior (si lo tenías guardado), o
- Copiar a mano los archivos desde la carpeta de backup correspondiente.

La carpeta `_backups` está **excluida** de la detección de perfiles.

---

## Empaquetar a ejecutable portable (.exe)

Para distribuirlo sin que el destino tenga Python instalado:

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name cambia-credenciales app.py
```

Genera `dist/cambia-credenciales.exe`, que **incluye el intérprete de Python y las
librerías**. `--windowed` arma el binario **sin consola** (ideal para la GUI).

> El binario es **por sistema operativo**: para macOS/Linux hay que correr el mismo
> comando en cada uno. El *código fuente* es el mismo en los tres.
> Si querés usar también la CLI desde el `.exe`, compilá **sin** `--windowed`
> (o generá dos binarios, uno para GUI y otro para consola).

---

## Estructura del proyecto

```
app.py                    Punto de entrada: GUI (sin args) / CLI (con args)
core.py                   Lógica: detección de perfiles, backup, activar, gitconfig (sin UI)
gui.py                    Ventana customtkinter (pestañas Perfiles / Git Config)
cli.py                    Comandos de consola (argparse)
requirements.txt          Dependencias (customtkinter)
Cambia Credenciales.vbs   Lanzador de GUI sin consola (recomendado)
ejecutar.bat              Lanzador de GUI con pythonw
README.md                 Este archivo
```

`core.py` no depende de la UI: tanto la GUI como la CLI llaman a las mismas funciones,
así que el comportamiento es idéntico en ambos modos.

---

## Notas de seguridad

- El programa **solo** lee/escribe dentro de `~/.ssh` y `~/.gitconfig`.
- Nunca muestra el contenido de las **claves privadas** (`id_*` sin `.pub`).
- En Linux/Mac corrige los permisos de las claves automáticamente al activar un perfil.
