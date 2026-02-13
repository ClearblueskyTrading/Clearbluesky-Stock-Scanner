# GetTimeAndMarket.ps1 - Output current time (ET) and market open status
$now = [System.TimeZoneInfo]::ConvertTimeFromUtc((Get-Date).ToUniversalTime(), [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time"))
$et = $now.ToString("yyyy-MM-dd HH:mm:ss ET")
$dow = $now.DayOfWeek
$hour = $now.Hour
$min = $now.Minute
$minute = $hour * 60 + $min
$open = 9 * 60 + 30
$close = 16 * 60
$marketOpen = ($dow -ne "Saturday" -and $dow -ne "Sunday") -and ($minute -ge $open -and $minute -lt $close)
$status = if ($marketOpen) { "OPEN" } else { "CLOSED" }
"$et | Market: $status"
