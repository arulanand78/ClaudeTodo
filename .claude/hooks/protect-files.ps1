# PreToolUse guard: block edits/writes to protected files.
# Protected: .env (and .env.* variants), package-lock.json, todos.db,
# and anything under .git/ (or the .git dir itself).
# Reads the hook JSON from stdin; emits a PreToolUse deny decision on stdout if blocked.

$ErrorActionPreference = 'Stop'
$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

try {
    $hook = $raw | ConvertFrom-Json
} catch {
    exit 0
}

$filePath = $hook.tool_input.file_path
if (-not $filePath) { exit 0 }

# Normalize separators to forward slashes for consistent matching on Windows.
$norm = ($filePath -replace '\\', '/').ToLower()

$isProtected = $false
$reason = ''

if ($norm -match '(^|/)\.env(\.|$)') {
    $isProtected = $true
    $reason = '.env files hold secrets - do not hand-edit them; if a change is needed, ask the user.'
} elseif ($norm -match 'package-lock\.json$') {
    $isProtected = $true
    $reason = 'package-lock.json is managed by npm - regenerate it with npm install, do not hand-edit it.'
} elseif ($norm -match 'todos\.db$') {
    $isProtected = $true
    $reason = 'todos.db is the SQLite database - modify its contents via the API/backend, not by editing the file.'
} elseif ($norm -match '(^|/)\.git(/|$)') {
    $isProtected = $true
    $reason = 'the .git directory is version-control internals - do not edit it directly.'
}

if ($isProtected) {
    $fullReason = "Blocked: '$filePath' is a protected path. $reason"
    $output = @{
        hookSpecificOutput = @{
            hookEventName             = 'PreToolUse'
            permissionDecision        = 'deny'
            permissionDecisionReason  = $fullReason
        }
    }
    $output | ConvertTo-Json -Compress -Depth 10
}