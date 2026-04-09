# MAYA SOC Enterprise - Domain & DNS Verification Script for Windows
# Run this script locally to verify DNS and domain configuration
# Requires PowerShell 5.1+ (built into Windows 10+)

# Configuration
$IP = "64.227.137.81"
$DOMAIN = "vaultrap.com"
$SUBDOMAIN = "maya.vaultrap.com"
$APPSUBDOMAIN = "app.vaultrap.com"

# Colors (approximated for Windows Terminal/PowerShell)
function Write-Info { Write-Host "[INFO]  $args" -ForegroundColor Blue }
function Write-Success { Write-Host "[✓]    $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[!]    $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[✗]    $args" -ForegroundColor Red }

# Header
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  MAYA SOC Enterprise - Domain & DNS Verification (Windows)    ║" -ForegroundColor Blue
Write-Host "║  IP: $IP                                         ║" -ForegroundColor Blue
Write-Host "║  Domain: $DOMAIN                                               ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Test 1: DNS Resolution
Write-Info "Testing DNS Resolution..."
Write-Host ""

# Test root domain
Write-Info "Root Domain: $DOMAIN"
try {
    $result = [System.Net.Dns]::GetHostAddresses($DOMAIN) | Select-Object -ExpandProperty IPAddressToString
    if ($result -contains $IP) {
        Write-Success "DNS resolves to $IP"
    } else {
        Write-Warning "DNS resolves to: $result (expected $IP)"
    }
} catch {
    Write-Error "DNS does not resolve for $DOMAIN"
    Write-Host "  Wait 30 minutes for DNS propagation" -ForegroundColor Yellow
}

Write-Host ""

# Test MAYA subdomain
Write-Info "Subdomain: $SUBDOMAIN"
try {
    $result = [System.Net.Dns]::GetHostAddresses($SUBDOMAIN) | Select-Object -ExpandProperty IPAddressToString
    if ($result -contains $IP) {
        Write-Success "DNS resolves to $IP"
    } else {
        Write-Warning "DNS resolves to: $result (expected $IP)"
    }
} catch {
    Write-Error "DNS does not resolve for $SUBDOMAIN"
    Write-Host "  Wait 30 minutes for DNS propagation" -ForegroundColor Yellow
}

Write-Host ""

# Test APP subdomain
Write-Info "Subdomain: $APPSUBDOMAIN"
try {
    $result = [System.Net.Dns]::GetHostAddresses($APPSUBDOMAIN) | Select-Object -ExpandProperty IPAddressToString
    if ($result -contains $IP) {
        Write-Success "DNS resolves to $IP"
    } else {
        Write-Warning "DNS resolves to: $result"
    }
} catch {
    Write-Warning "DNS does not resolve for $APPSUBDOMAIN (Optional subdomain)"
}

Write-Host ""

# Test 2: HTTP/HTTPS Connectivity
Write-Info "Testing HTTP/HTTPS Connectivity..."
Write-Host ""

# Test HTTP redirect
Write-Info "HTTP Redirect: http://$DOMAIN"
try {
    $response = Invoke-WebRequest -Uri "http://$DOMAIN" -MaximumRedirection 0 -ErrorAction Stop -TimeoutSec 5
    Write-Success "HTTP connection working"
} catch {
    if ($_.Exception.Response.StatusCode -in @(301, 302, 303, 307, 308)) {
        Write-Success "HTTP redirects to HTTPS (expected)"
    } else {
        Write-Warning "HTTP connection: $($_.Exception.Response.StatusCode)"
    }
}

Write-Host ""

# Test HTTPS (with certificate skip for testing)
Write-Info "HTTPS: https://$SUBDOMAIN"

# Create WebRequest that ignores certificate errors
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

try {
    $response = Invoke-WebRequest -Uri "https://$SUBDOMAIN" -TimeoutSec 5
    Write-Success "HTTPS connection successful"
} catch {
    if ($_.Exception.Message -like "*403*" -or $_.Exception.Message -like "*503*") {
        Write-Warning "HTTPS connection established but service returned: $($_.Exception.Message)"
    } else {
        Write-Warning "HTTPS connection issue: $($_.Exception.Message)"
    }
}

Write-Host ""

# Test 3: Health Check Endpoints
Write-Info "Testing Application Health Endpoints..."
Write-Host ""

# Health check
Write-Info "Health Check: https://$SUBDOMAIN/health"
try {
    $response = Invoke-WebRequest -Uri "https://$SUBDOMAIN/health" -TimeoutSec 5 -SkipCertificateCheck
    if ($response.Content -like "*healthy*" -or $response.StatusCode -eq 200) {
        Write-Success "Health check endpoint responding"
    } else {
        Write-Warning "Health check returned: $($response.StatusCode)"
    }
} catch {
    Write-Warning "Health check not responding: $($_.Exception.Message)"
}

Write-Host ""

# API health
Write-Info "API Health: https://$SUBDOMAIN/api/v1/health"
try {
    $response = Invoke-WebRequest -Uri "https://$SUBDOMAIN/api/v1/health" -TimeoutSec 5 -SkipCertificateCheck
    if ($response.StatusCode -eq 200) {
        Write-Success "API health endpoint responding"
    } else {
        Write-Warning "API returned status: $($response.StatusCode)"
    }
} catch {
    Write-Warning "API not responding: $($_.Exception.Message)"
}

Write-Host ""

# Test 4: Frontend Check
Write-Info "Testing Frontend..."
Write-Host ""

Write-Info "Frontend: https://$SUBDOMAIN"
try {
    $response = Invoke-WebRequest -Uri "https://$SUBDOMAIN" -TimeoutSec 5 -SkipCertificateCheck
    if ($response.Content -like "*React*" -or $response.Content -like "*html*" -or $response.StatusCode -eq 200) {
        Write-Success "Frontend is responding"
    } else {
        Write-Warning "Frontend response code: $($response.StatusCode)"
    }
} catch {
    Write-Warning "Frontend access issue: $($_.Exception.Message)"
}

Write-Host ""

# Test 5: Connectivity to IP directly
Write-Info "Testing Direct IP Connection..."
Write-Host ""

Write-Info "IP Address: $IP:443"
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $async = $tcpClient.BeginConnect($IP, 443, $null, $null)
    $wait = $async.AsyncWaitHandle.WaitOne(5000, $false)
    
    if ($wait) {
        $tcpClient.EndConnect($async)
        Write-Success "TCP connection to $IP:443 successful"
        $tcpClient.Close()
    } else {
        Write-Error "TCP connection timeout to $IP:443"
    }
} catch {
    Write-Error "Cannot connect to $IP:443"
}

Write-Host ""

# Summary
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  VERIFICATION COMPLETE                                        ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

Write-Info "Verification Checklist:"
Write-Host "  [ ] DNS resolves for $DOMAIN"
Write-Host "  [ ] DNS resolves for $SUBDOMAIN"
Write-Host "  [ ] HTTP redirects to HTTPS"
Write-Host "  [ ] HTTPS connection successful"
Write-Host "  [ ] Health check responding"
Write-Host "  [ ] API responding"
Write-Host "  [ ] Frontend loading"
Write-Host "  [ ] TCP connection to IP:443"
Write-Host ""

Write-Info "Next Steps:"
Write-Host "  1. If DNS not resolving: Wait 30 minutes and re-run this script"
Write-Host "  2. If DNS resolves: Continue with deployment checklist"
Write-Host "  3. If health checks fail: Services may not be running yet"
Write-Host "  4. Once all tests pass: Your domain is ready!"
Write-Host ""

Write-Success "Domain verification script complete! ✓"
Write-Host ""
