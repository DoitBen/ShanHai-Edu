param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$ProjectName = "T050 fullchain smoke",
    [string]$FixturePath = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

function Write-Step {
    param([string]$Message)
    Write-Host "[fullchain-smoke] $Message"
}

function Mask-Text {
    param([string]$Text)
    if ($null -eq $Text) {
        return ""
    }
    return ($Text -replace '(DEEPSEEK_API_KEY|OCTO_API_KEY)\s*=\s*[^;\s]+', '$1=<redacted>' `
                  -replace '(Bearer\s+)[A-Za-z0-9._~+\-/=]+', '$1<redacted>')
}

function Invoke-ApiJson {
    param(
        [ValidateSet("GET", "POST")]
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )
    $uri = "$script:ApiBase$Path"
    try {
        $jsonBody = $null
        if ($null -ne $Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 30
        }
        $client = [System.Net.Http.HttpClient]::new()
        $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::$Method, $uri)
        if ($null -ne $jsonBody) {
            $request.Content = [System.Net.Http.StringContent]::new($jsonBody, [System.Text.Encoding]::UTF8, "application/json")
        }
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        $bodyText = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "HTTP $([int]$response.StatusCode): $(Mask-Text $bodyText)"
        }
        return $bodyText | ConvertFrom-Json
    } catch {
        $message = Mask-Text $_.Exception.Message
        throw "HTTP $Method $Path failed: $message"
    } finally {
        if ($null -ne $request) {
            $request.Dispose()
        }
        if ($null -ne $client) {
            $client.Dispose()
        }
    }
}

function Invoke-UploadFile {
    param(
        [string]$Path,
        [string]$FilePath
    )
    $client = [System.Net.Http.HttpClient]::new()
    $content = [System.Net.Http.MultipartFormDataContent]::new()
    $stream = $null
    try {
        $stream = [System.IO.File]::OpenRead($FilePath)
        $fileContent = [System.Net.Http.StreamContent]::new($stream)
        $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/octet-stream")
        $content.Add($fileContent, "file", [System.IO.Path]::GetFileName($FilePath))
        $response = $client.PostAsync("$script:ApiBase$Path", $content).GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "HTTP $([int]$response.StatusCode): $(Mask-Text $body)"
        }
        return $body | ConvertFrom-Json
    } catch {
        $message = Mask-Text $_.Exception.Message
        throw "HTTP POST $Path failed: $message"
    } finally {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
        $content.Dispose()
        $client.Dispose()
    }
}

function Invoke-DownloadFile {
    param(
        [string]$Path,
        [string]$OutFile
    )
    $client = [System.Net.Http.HttpClient]::new()
    try {
        $response = $client.GetAsync("$script:ApiBase$Path").GetAwaiter().GetResult()
        $bytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            $body = [System.Text.Encoding]::UTF8.GetString($bytes)
            throw "HTTP $([int]$response.StatusCode): $(Mask-Text $body)"
        }
        [System.IO.File]::WriteAllBytes($OutFile, $bytes)
        return [ordered]@{
            StatusCode = [int]$response.StatusCode
            ContentType = [string]$response.Content.Headers.ContentType
        }
    } catch {
        $message = Mask-Text $_.Exception.Message
        throw "HTTP GET $Path failed: $message"
    } finally {
        $client.Dispose()
    }
}

function Assert-Ok {
    param(
        [object]$Response,
        [string]$Label
    )
    if ($Response.ok -ne $true) {
        $json = Mask-Text ($Response | ConvertTo-Json -Depth 20 -Compress)
        throw "$Label returned non-ok response: $json"
    }
    return $Response.data
}

function Invoke-GenerateAndApprove {
    param(
        [string]$ProjectId,
        [string]$NodeId
    )
    $generated = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$ProjectId/nodes/$NodeId/generate" -Body @{}) "$NodeId generate"
    Write-Step "$NodeId generated status=$($generated.status)"
    $approved = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$ProjectId/nodes/$NodeId/approve" -Body @{}) "$NodeId approve"
    if ($approved.status -ne "approved") {
        throw "$NodeId approve expected approved, got $($approved.status)"
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$evidenceRoot = Join-Path $repoRoot "docs\qa-audits\fullchain-smoke-evidence"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path $evidenceRoot $timestamp
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

$fixture = if ([string]::IsNullOrWhiteSpace($FixturePath)) {
    $generatedFixture = Join-Path $evidenceDir "textbook-fixture.txt"
    @(
        "Grade 1 math lesson: numbers 1 to 5."
        "Students count apples, pencils, blocks, flowers, and stars to build number sense."
        "The lesson goal is object-number matching, comparing quantities, and naming counts with digits."
    ) | Set-Content -LiteralPath $generatedFixture -Encoding UTF8
    $generatedFixture
} elseif ([System.IO.Path]::IsPathRooted($FixturePath)) {
    (Resolve-Path -LiteralPath $FixturePath).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $repoRoot $FixturePath)).Path
}
$script:ApiBase = $ApiBaseUrl.TrimEnd("/")

Write-Step "api=$script:ApiBase"
Write-Step "project=$ProjectName"
Write-Step "fixture=$fixture"
Write-Step "evidence=$evidenceDir"

$health = Assert-Ok (Invoke-ApiJson -Method GET -Path "/health") "health"
Write-Step "health status=$($health.status) workflow=$($health.workflow_version)"

$project = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects" -Body @{
    name = $ProjectName
    subject = "math"
    grade = "1"
    textbook_version = "renjiao"
    volume = "shang"
    lesson_type = "public"
}) "create project"
$projectId = $project.project_id
Write-Step "project_id=$projectId"

$upload = Invoke-UploadFile -Path "/projects/$projectId/textbook" -FilePath $fixture
Assert-Ok $upload "upload textbook" | Out-Null
Write-Step "textbook uploaded"

$chainNodes = @(
    "textbook_parse",
    "lesson_plan",
    "intro_selection",
    "intro_video_script",
    "intro_video_screenplay",
    "intro_video_asset",
    "storyboard"
)
foreach ($nodeId in $chainNodes) {
    Invoke-GenerateAndApprove -ProjectId $projectId -NodeId $nodeId
}

$storyboard = Assert-Ok (Invoke-ApiJson -Method GET -Path "/projects/$projectId/nodes/storyboard") "get storyboard"
if ($storyboard.status -ne "approved") {
    throw "storyboard expected approved, got $($storyboard.status)"
}
Write-Step "storyboard approved shots=$($storyboard.content.shots.Count)"

$video = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$projectId/nodes/final_video/generate" -Body @{
    model = "veo_3_1-fast"
    size = "1280x720"
    mode = "reference"
    full_run = $true
}) "final_video generate"
if ($video.video_path -ne "outputs/final_video.mp4") {
    throw "final_video expected outputs/final_video.mp4, got $($video.video_path)"
}
Write-Step "final_video status=$($video.status) tasks=$($video.tasks.Count) video_path=$($video.video_path)"

$mp4Path = Join-Path $evidenceDir "final_video.mp4"
$mp4Response = Invoke-DownloadFile -Path "/projects/$projectId/outputs/final_video.mp4" -OutFile $mp4Path
$mp4Size = (Get-Item $mp4Path).Length
if ($mp4Size -le 0) {
    throw "Downloaded MP4 is empty"
}
Write-Step "mp4 downloaded status=$($mp4Response.StatusCode) bytes=$mp4Size"

$export = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$projectId/export/ppt" -Body @{}) "export ppt"
if (-not ($export.filename -like "*.pptx")) {
    throw "PPT filename must end with .pptx, got $($export.filename)"
}
Write-Step "ppt exported filename=$($export.filename) video_path=$($export.video_path)"

$pptPath = Join-Path $evidenceDir $export.filename
$pptResponse = Invoke-DownloadFile -Path $export.download_url -OutFile $pptPath
$pptSize = (Get-Item $pptPath).Length
if ($pptSize -le 0) {
    throw "Downloaded PPT is empty"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($pptPath)
try {
    $mp4Entries = @($zip.Entries | Where-Object { $_.FullName -like "ppt/media/*.mp4" })
} finally {
    $zip.Dispose()
}
if ($mp4Entries.Count -lt 1) {
    throw "PPT does not contain ppt/media/*.mp4"
}
Write-Step "ppt downloaded status=$($pptResponse.StatusCode) bytes=$pptSize embedded_mp4=$($mp4Entries.Count)"

$summary = [ordered]@{
    ok = $true
    api_base_url = $script:ApiBase
    project_id = $projectId
    storyboard_status = $storyboard.status
    final_video_path = $video.video_path
    mp4_bytes = $mp4Size
    ppt_filename = $export.filename
    ppt_bytes = $pptSize
    ppt_embedded_mp4_count = $mp4Entries.Count
    evidence_dir = $evidenceDir
}
$summaryPath = Join-Path $evidenceDir "summary.json"
($summary | ConvertTo-Json -Depth 10) | Set-Content -Encoding UTF8 $summaryPath
Write-Step "PASS summary=$summaryPath"
