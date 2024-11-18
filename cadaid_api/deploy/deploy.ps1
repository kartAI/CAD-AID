# Define path to YAML file
$yamlPath = ".\aci_deploy.yaml"

# Read the YAML file
$yamlContent = Get-Content -Path $yamlPath -Raw

# Debug: Print the environment variables (mask sensitive data for security)
Write-Host "Checking environment variables:"
if ($env:AZURE_STORAGE_CONNECTION_STRING) {
    Write-Host "AZURE_STORAGE_CONNECTION_STRING is present"
} else {
    Write-Host "AZURE_STORAGE_CONNECTION_STRING is missing!"
}

if ($env:STATIC_API_KEY) {
    Write-Host "STATIC_API_KEY is present"
} else {
    Write-Host "STATIC_API_KEY is missing!"
}

# Ensure USE_AZURE_STORAGE is set to true
$env:USE_AZURE_STORAGE = "true"
Write-Host "Setting USE_AZURE_STORAGE to true"

# Create replacements hashtable
$replacements = @{
    '{{AZURE_STORAGE_CONNECTION_STRING}}' = $env:AZURE_STORAGE_CONNECTION_STRING
    '{{STATIC_API_KEY}}'                  = $env:STATIC_API_KEY
    '{{USE_AZURE_STORAGE}}'               = $env:USE_AZURE_STORAGE
}

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
    $value = Escape-SingleQuotes($value)
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
