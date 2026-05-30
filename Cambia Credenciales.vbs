' Lanzador sin NINGUNA ventana de consola (ni siquiera un parpadeo).
' Doble clic acá para abrir solo la GUI. Equivale a:  pythonw app.py
Dim fso, sh, dir
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
' 0 = ventana oculta ; False = no esperar a que termine
sh.Run "pythonw """ & dir & "\app.py""", 0, False
