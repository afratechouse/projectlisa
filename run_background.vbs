Set WshShell = CreateObject("WScript.Shell")
' Run start_lisa.bat silently in the background (0 = hidden window)
WshShell.Run "cmd /c """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\start_lisa.bat""", 0, False
