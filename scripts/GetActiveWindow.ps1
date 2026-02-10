# Output active window title and process name (for "what am I looking at").
# Usage: .\GetActiveWindow.ps1
# Output: Title|ProcessName (one line)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", SetLastError=true)] public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int lpdwProcessId);
}
"@
$hwnd = [Win32]::GetForegroundWindow()
$procId = 0
[Win32]::GetWindowThreadProcessId($hwnd, [ref]$procId) | Out-Null
try {
    $p = Get-Process -Id $procId -ErrorAction Stop
    $title = if ($p.MainWindowTitle) { $p.MainWindowTitle } else { "(no title)" }
    Write-Output "${title}|$($p.ProcessName)"
} catch {
    Write-Output "(unknown)|(unknown)"
}
