# Define path to YAML file
$yamlPath = ".\aci_deploy.yaml"

# Read the YAML file
$yamlContent = Get-Content -Path $yamlPath -Raw

# Prepare a hash table with placeholders and their replacement values
$replacements = @{
    '{{STATIC_API_KEY}}' = $env:STATIC_API_KEY
}

# Function to escape single quotes in values
function Escape-SingleQuotes($value) {
    return $value -replace "'", "''"
}

# Replace placeholders with actual values
foreach ($placeholder in $replacements.Keys) {
    $value = $replacements[$placeholder]
    $value = Escape-SingleQuotes $value
    $yamlContent = $yamlContent.Replace($placeholder, $value)
}

# Write the processed YAML content to a known file for inspection
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