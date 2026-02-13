# GetActiveWindow.ps1 - Output active window Title|ProcessName (for agent or GUI)
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class Win32 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder t, int n);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
}
"@
$h = [Win32]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[Win32]::GetWindowText($h, $sb, 256) | Out-Null
$title = $sb.ToString().Trim()
$procId = 0
[Win32]::GetWindowThreadProcessId($h, [ref]$procId) | Out-Null
$proc = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
if (-not $proc) { $proc = "?" }
"$title|$proc"
