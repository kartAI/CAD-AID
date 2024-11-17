# Define path to YAML file
$yamlPath = ".\aci_deploy.yaml"

# Read the YAML file
$yamlContent = Get-Content -Path $yamlPath -Raw

# Debug: Print the environment variable (mask the key for security)
Write-Host "Checking if AZURE_STORAGE_CONNECTION_STRING is set:"
if ($env:AZURE_STORAGE_CONNECTION_STRING) {
    Write-Host "Storage connection string is present"
} else {
    Write-Host "Storage connection string is missing!"
}

# Create replacements hashtable
$replacements = @{}
$replacements['{{AZURE_STORAGE_CONNECTION_STRING}}'] = $env:AZURE_STORAGE_CONNECTION_STRING
$replacements['{{STATIC_API_KEY}}'] = $env:STATIC_API_KEY

# Function to escape single quotes in values
function Escape-SingleQuotes($value) {
    return $value -replace "'", "''"
}

# Replace placeholders with actual values
foreach ($placeholder in $replacements.Keys) {
    $value = $replacements[$placeholder]
    if ($null -eq $value -or $value -eq '') {
        Write-Host "Warning: No value found for $placeholder"
        continue
    }
    $value = Escape-SingleQuotes $value
    $yamlContent = $yamlContent.Replace($placeholder, $value)
}

# Optional: Check if any placeholders remain (for debugging)
if ($yamlContent -match '{{.}}') {
    Write-Host "Warning: Some placeholders were not replaced:"
    $yamlContent | Select-String -Pattern '{{.}}' -AllMatches
}

# Write the processed YAML
$yamlContent | Set-Content -Path ".\aci_deploy_processed.yaml" -NoNewline

# Write the processed YAML content to a temporary file
$tempFile = [System.IO.Path]::GetTempFileName() + ".yaml"
$yamlContent | Set-Content -Path $tempFile -NoNewline

try {
    # Deploy the application to Azure Container Instances
    az container create --resource-group $env:RESOURCE_GROUP --file $tempFile
} finally {
    # Clean up the temporary file
    Remove-Item $tempFile -Force
}