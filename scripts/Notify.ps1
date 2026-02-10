# Show a Windows toast notification (for "notify me when done").
# Usage: .\Notify.ps1 "Your message here"
# Or:    .\Notify.ps1 -Title "Done" -Message "Scan finished"

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$MessageParts,
    [string]$Title = "Cursor",
    [string]$Message
)
if (-not $Message -and $MessageParts) { $Message = $MessageParts -join " " }
if (-not $Message) { $Message = "Done." }

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$text = $template.GetElementsByTagName("text")
$text[0].AppendChild($template.CreateTextNode($Title)) | Out-Null
$text[1].AppendChild($template.CreateTextNode($Message)) | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template.GetXml())
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Cursor").Show($toast)
