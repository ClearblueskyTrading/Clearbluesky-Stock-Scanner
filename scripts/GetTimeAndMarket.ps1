# Output current time (ET) and whether US market is open (9:30-4 ET, Mon-Fri).
# Usage: .\GetTimeAndMarket.ps1
# Output: Time (ET) | Market: Open|Closed

$et = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date), "Eastern Standard Time")
$timeStr = $et.ToString("yyyy-MM-dd h:mm tt") + " ET"
$dow = $et.DayOfWeek
$t = $et.TimeOfDay.TotalMinutes
$open = 9 * 60 + 30
$close = 16 * 60
$isWeekday = $dow -ge [DayOfWeek]::Monday -and $dow -le [DayOfWeek]::Friday
$isOpen = $isWeekday -and $t -ge $open -and $t -lt $close
$market = if ($isOpen) { "Open" } else { "Closed" }
Write-Output "${timeStr} | Market: ${market}"
