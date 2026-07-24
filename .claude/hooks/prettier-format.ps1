# PostToolUse formatter: run Prettier on frontend web files after Write/Edit.
# Scope: files under frontend/ with extensions js, jsx, ts, tsx, json, css, md.
# Non-blocking: swallows all errors and always exits 0 so the tool call is never disturbed.

$ErrorActionPreference = 'Stop'
$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

try {
    $hook = $raw | ConvertFrom-Json
} catch {
    exit 0
}

# Write/Edit put the path in tool_input.file_path; fall back to tool_response.filePath.
$filePath = $hook.tool_input.file_path
if (-not $filePath) { $filePath = $hook.tool_response.filePath }
if (-not $filePath) { exit 0 }

# Normalize separators to forward slashes for matching.
$norm = ($filePath -replace '\\', '/').ToLower()

# Only format files inside the frontend/ subtree.
if ($norm -notmatch '(^|/)frontend/') { exit 0 }

# Only format web file extensions.
if ($norm -notmatch '\.(js|jsx|ts|tsx|json|css|md)$') { exit 0 }

$prettier = 'C:\Dev\ClaudeTodo\frontend\node_modules\.bin\prettier.cmd'
if (-not (Test-Path $prettier)) { exit 0 }

try {
    & $prettier --write --log-level warn $filePath 2>$null | Out-Null
} catch {}
exit 0