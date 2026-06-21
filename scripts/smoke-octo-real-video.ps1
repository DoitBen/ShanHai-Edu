param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$ProjectName = "T053 real octo one-shot smoke",
    [string]$EvidenceRoot = "",
    [int]$PollSeconds = 10,
    [int]$MaxPolls = 12
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

function Write-Step {
    param([string]$Message)
    Write-Host "[octo-real-smoke] $Message"
}

function Mask-Text {
    param([string]$Text)
    if ($null -eq $Text) {
        return ""
    }
    return ($Text -replace '(DEEPSEEK_API_KEY|OCTO_API_KEY)\s*=\s*[^;\s]+', '$1=<redacted>' `
                  -replace '(Authorization\s*[:=]\s*Bearer\s+)[A-Za-z0-9._~+\-/=]+', '$1<redacted>' `
                  -replace '(Bearer\s+)[A-Za-z0-9._~+\-/=]+', '$1<redacted>' `
                  -replace '(?i)((api[_-]?key|token|secret|key)\s*["'']?\s*[:=]\s*["'']?)[^"'',}\s]+', '$1<redacted>')
}

function Invoke-ApiJson {
    param(
        [ValidateSet("GET", "POST")]
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )
    $uri = "$script:ApiBase$Path"
    $client = [System.Net.Http.HttpClient]::new()
    $request = $null
    try {
        $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::$Method, $uri)
        if ($null -ne $Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 50
            $request.Content = [System.Net.Http.StringContent]::new($jsonBody, [System.Text.Encoding]::UTF8, "application/json")
        }
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        $bodyText = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        $summary = [ordered]@{
            method = $Method
            path = $Path
            http_status = [int]$response.StatusCode
            body_excerpt = (Mask-Text $bodyText).Substring(0, [Math]::Min(700, (Mask-Text $bodyText).Length))
        }
        $script:Evidence.calls += $summary
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
        $script:Evidence.calls += [ordered]@{
            method = "GET"
            path = $Path
            http_status = [int]$response.StatusCode
            body_excerpt = "<binary:$($bytes.Length)>"
        }
        if (-not $response.IsSuccessStatusCode) {
            $body = [System.Text.Encoding]::UTF8.GetString($bytes)
            throw "HTTP $([int]$response.StatusCode): $(Mask-Text $body)"
        }
        [System.IO.File]::WriteAllBytes($OutFile, $bytes)
        return [ordered]@{
            StatusCode = [int]$response.StatusCode
            ContentType = [string]$response.Content.Headers.ContentType
            Bytes = $bytes.Length
        }
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
        $json = Mask-Text ($Response | ConvertTo-Json -Depth 30 -Compress)
        throw "$Label returned non-ok response: $json"
    }
    return $Response.data
}

function Set-ApprovedNode {
    param(
        [string]$ProjectId,
        [string]$NodeId,
        [hashtable]$Content
    )
    Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$ProjectId/nodes/$NodeId/edit" -Body @{ content = $Content }) "$NodeId edit" | Out-Null
    $approved = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$ProjectId/nodes/$NodeId/approve" -Body @{}) "$NodeId approve"
    if ($approved.status -ne "approved") {
        throw "$NodeId approve expected approved, got $($approved.status)"
    }
    Write-Step "$NodeId approved"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
    $EvidenceRoot = Join-Path $repoRoot "docs\qa-audits\octo-real-video-smoke"
}
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path $EvidenceRoot $timestamp
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

$script:ApiBase = $ApiBaseUrl.TrimEnd("/")
$script:Evidence = [ordered]@{
    ok = $false
    api_base_url = $script:ApiBase
    project_id = $null
    provider_task_id = $null
    task_status = $null
    error_code = $null
    http_status = $null
    retryable = $null
    downloaded_clip = $null
    calls = @()
}

try {
    Write-Step "api=$script:ApiBase"
    Write-Step "project=$ProjectName"
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
    $script:Evidence.project_id = $projectId
    Write-Step "project_id=$projectId"

    Set-ApprovedNode -ProjectId $projectId -NodeId "textbook_parse" -Content @{
        subject = "math"
        grade = "1"
        textbook_version = "renjiao"
        volume = "shang"
        lesson_title = "Numbers 1 to 5"
        core_knowledge_points = @("numbers 1 to 5")
        teaching_goal_summary = "Recognize quantities from 1 to 5."
        key_points = @("object-number matching")
        difficulties = @("quantity abstraction")
    }
    Set-ApprovedNode -ProjectId $projectId -NodeId "lesson_plan" -Content @{
        lesson_plan_markdown = "# Lesson: Numbers 1 to 5`n`n## Objective`nRecognize quantities from 1 to 5."
        textbook_anchor = "fixed smoke textbook anchor"
        teaching_objectives = "Recognize quantities from 1 to 5."
        key_difficulty = "Build object-number matching."
        teaching_flow = "Observe, count, and explain."
        blackboard_design = "1 2 3 4 5"
        intro_designs = @(@{
            design_id = "design_application_01"
            type = "application"
            title = "Count desktop objects"
            hook = "Use cartoon objects to introduce 1 to 5."
            anchor_to_lesson = "Anchor to numbers 1 to 5."
            recommend_score = 5
            risk_note = "Use non-realistic cartoon objects only."
        })
    }
    Set-ApprovedNode -ProjectId $projectId -NodeId "intro_selection" -Content @{
        selection_mode = "single_best"
        selected_design_ids = @("design_application_01")
        primary_design_id = "design_application_01"
        selected_anchor = "Use cartoon desktop objects to introduce 1 to 5."
        downstream_generation_mode = "one_shot_smoke"
        selection_reason = "Fixed smoke only verifies real provider submit."
    }
    Set-ApprovedNode -ProjectId $projectId -NodeId "intro_video_script" -Content @{
        total_duration_sec = 10
        video_type = "application"
        anchor_to_lesson = "Use cartoon desktop objects to introduce 1 to 5."
        narration_full_text = "A cartoon apple and the number 1 appear on the desk."
        narration_word_count = 24
        banned_elements = @("real_minor", "real_classroom", "teacher_questioning", "student_group_activity")
    }
    Set-ApprovedNode -ProjectId $projectId -NodeId "intro_video_screenplay" -Content @{
        scenes = @(@{
            scene_id = "scene_01"
            duration_sec = 10
            scene_description = "Non-realistic cartoon desk with one apple and the number 1."
            character_refs = @()
            narration_segment = "A cartoon apple and the number 1 appear on the desk."
        })
    }
    Set-ApprovedNode -ProjectId $projectId -NodeId "intro_video_asset" -Content @{
        assets = @(@{
            asset_id = "asset_ref_01"
            source_prompt_id = "shot_01"
            storage_path = "assets/ref_01.png"
            status = "approved"
        })
    }
    Set-ApprovedNode -ProjectId $projectId -NodeId "storyboard" -Content @{
        shots = @(@{
            shot_id = "shot_01"
            duration_sec = 10
            main_subject = "Non-realistic cartoon desk with one apple and the number 1"
            character_refs = @()
            reference_image_ids = @("asset_ref_01")
            narration_slice = "A cartoon apple and the number 1 appear on the desk."
            subtitle = "Number 1"
            model_prompt = "Chinese male narration: A cartoon apple and the number 1 appear on the desk.`nVisual: non-realistic cartoon desk with one apple and the number 1.`nNo English audio."
            first_frame_test_status = "passed"
            first_frame_asset_id = "asset_ref_01"
        })
    }

    $video = Assert-Ok (Invoke-ApiJson -Method POST -Path "/projects/$projectId/nodes/final_video/generate" -Body @{
        model = "omni_flash-10s"
        size = "1280x720"
        mode = "reference"
    }) "final_video generate"
    if ($video.tasks.Count -ne 1) {
        throw "real smoke expected exactly 1 submitted task, got $($video.tasks.Count)"
    }
    $task = $video.tasks[0]
    $script:Evidence.provider_task_id = $task.provider_task_id
    $script:Evidence.task_status = $task.status
    $script:Evidence.error_code = $task.error_code
    if ([string]::IsNullOrWhiteSpace($task.provider_task_id)) {
        throw "VIDEO_PROVIDER_MODE=real expected provider_task_id; current task did not expose one"
    }
    Write-Step "submitted task_id=$($task.task_id) provider_task_id=$($task.provider_task_id) status=$($task.status)"

    $latestTask = $task
    for ($i = 1; $i -le $MaxPolls; $i++) {
        Start-Sleep -Seconds $PollSeconds
        $latestTask = Assert-Ok (Invoke-ApiJson -Method GET -Path "/projects/$projectId/tasks/$($task.task_id)") "task query"
        $script:Evidence.task_status = $latestTask.status
        $script:Evidence.error_code = $latestTask.error_code
        Write-Step "poll=$i status=$($latestTask.status) provider_task_id=$($latestTask.provider_task_id) video_url_present=$($latestTask.video_url_present)"
        if ($latestTask.status -in @("completed", "failed")) {
            break
        }
    }

    if ($latestTask.status -eq "completed" -and $latestTask.result.download_status -eq "downloaded") {
        $clipPath = Join-Path $evidenceDir "shot_01.mp4"
        $relPath = $latestTask.download_path
        $download = Invoke-DownloadFile -Path "/projects/$projectId/$relPath" -OutFile $clipPath
        $script:Evidence.downloaded_clip = [ordered]@{
            path = $clipPath
            bytes = $download.Bytes
            content_type = $download.ContentType
        }
        Write-Step "clip downloaded bytes=$($download.Bytes)"
    }

    $script:Evidence.ok = $true
    Write-Step "PASS status=$($script:Evidence.task_status)"
} catch {
    $message = Mask-Text $_.Exception.Message
    $script:Evidence.ok = $false
    $script:Evidence.failure = $message
    Write-Step "FAIL $message"
    throw
} finally {
    $summaryPath = Join-Path $evidenceDir "summary.json"
    ($script:Evidence | ConvertTo-Json -Depth 50) | Set-Content -LiteralPath $summaryPath -Encoding UTF8
    Write-Step "summary=$summaryPath"
}
