[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://files.jrsoftware.org/is/6/innosetup-6.3.3.exe"
$output = "C:\Users\Public\Downloads\innosetup.exe"
Write-Host "Downloading Inno Setup..."
Invoke-WebRequest -Uri $url -OutFile $output
if (Test-Path $output) {
    Write-Host "Installing Inno Setup..."
    Start-Process -FilePath $output -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-" -Wait
    Write-Host "Inno Setup installed successfully."
} else {
    Write-Host "Failed to download Inno Setup."
}
