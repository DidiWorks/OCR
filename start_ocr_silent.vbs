Set WshShell = CreateObject("WScript.Shell")
scriptPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
WshShell.CurrentDirectory = scriptPath

' Set environment variables
Set objEnv = WshShell.Environment("Process")
objEnv("PYTHONHOME") = scriptPath & "python-3.9.0-embed-amd64"
objEnv("PYTHONPATH") = scriptPath & "python-3.9.0-embed-amd64\Lib;" & scriptPath & "python-3.9.0-embed-amd64\DLLs;" & scriptPath
objEnv("PATH") = scriptPath & "python-3.9.0-embed-amd64;" & scriptPath & "python-3.9.0-embed-amd64\DLLs;" & scriptPath & "python-3.9.0-embed-amd64\Lib\site-packages\paddle\libs;" & objEnv("PATH")
objEnv("TCL_LIBRARY") = scriptPath & "python-3.9.0-embed-amd64\tcl\tcl8.6"
objEnv("TK_LIBRARY") = scriptPath & "python-3.9.0-embed-amd64\tcl\tk8.6"
objEnv("PYTHONIOENCODING") = "utf-8"
objEnv("PYTHONLEGACYWINDOWSSTDIO") = "utf-8"

' Launch OCR tool silently
WshShell.Run Chr(34) & scriptPath & "python-3.9.0-embed-amd64\python.exe" & Chr(34) & " " & Chr(34) & scriptPath & "main.py" & Chr(34), 0, False
