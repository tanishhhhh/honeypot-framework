Write-Host "🎯 Starting Safe SSH Attack Simulation..." -ForegroundColor Green

$targets = @("root", "admin", "ubuntu", "test")
$passwords = @("password", "123456", "admin123", "rootroot")

# Check if sshpass exists, if not inform the user
if (!(Get-Command sshpass -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  sshpass is not installed! You can install it using winget:" -ForegroundColor Yellow
    Write-Host "   winget install sshpass" -ForegroundColor Cyan
    Write-Host "Proceeding with native ssh (may prompt for password)..." -ForegroundColor Yellow
}

foreach ($user in $targets) {
    foreach ($pass in $passwords) {
        Write-Host "  Trying: ${user}:${pass}" -ForegroundColor Yellow
        
        if (Get-Command sshpass -ErrorAction SilentlyContinue) {
            sshpass -p $pass ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 -p 2222 ${user}@localhost "whoami" 2>&1 | Out-Null
        }
        else {
            # Native SSH without sshpass (will prompt or timeout)
            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 -p 2222 ${user}@localhost "whoami" 2>&1 | Out-Null
        }
        
        Start-Sleep -Milliseconds 800
    }
}

Write-Host "✅ Simulation complete. Check dashboard & logs." -ForegroundColor Green