$ErrorActionPreference = "Stop"

( Enable-PSRemoting -Force -SkipNetworkProfileCheck ) | out-null
(winrm set winrm/config/service '@{AllowUnencrypted="true"}' ) | out-null
(winrm set winrm/config/service/auth '@{Basic="true"}' ) | out-null
(winrm set winrm/config/client '@{AllowUnencrypted="true"}' ) | out-null

# create credentials with no password
( $Credentials = [System.Management.Automation.PSCredential]::new("test user",[System.Security.SecureString]::new()) ) | out-null

# Set session options with NoEncryption
( $opt = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck -NoEncryption ) | out-null

# Create a new session (login)
$session = New-PSSession -ComputerName localhost -SessionOption $opt -Authentication Basic -Credential $Credentials

# Run the bash command as 'test user'
Write-Output "Starting run-travis-windows.sh as user 'test user'..."
try {
    Invoke-Command -Session $session -ScriptBlock {
        $script:run_script="/c/users/$env:UserName/hnn/scripts/run-travis-windows.sh"
        try {
            & "C:\Program Files\Git\bin\bash.exe" "$script:run_script"
            if (!$?) {
                Write-Output "run-travis-windows.sh returned $LastExitCode"
                $host.SetShouldExit($LastExitCode)
                exit $LastExitCode
            }
        }
        catch {
            Write-Output "Failed to run run-travis-windows.sh"
            Write-Output $_
            $host.SetShouldExit(-1)
            throw
        }
    }
}
catch {
    Write-Output "Failed to start session:"
    Write-Output $_
    $host.SetShouldExit(-1)
    exit -1
}

Remove-PSSession -Session $session