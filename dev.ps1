<#
  사주당 개발 명령 모음 (Windows).  사용:  .\dev.ps1 <명령>

  == 파이썬 ==
    setup          Python 3.11 venv 생성 + 의존성 설치
    test           pytest 전량
    engine-check   ★ 2주차 관문 — 테스트 + 분포 + 중복률
    dist           분포 검증 (3,000명)
    dup            훅 중복률
    fixtures       회귀 케이스 50건 생성
    sheet          대조표(대조표.md) 뽑기
    plan           ★ 회귀 50건 — 무엇부터 볼지
    fill <파일>     받아적은 기대값을 대조 (--write 로 fixtures 에 써넣음)
    funnel         ★ 퍼널 — 어디서 나가는가 (FUNNEL_KEY 필요)
    migrate-sqlite 로컬 SQLite 로 마이그레이션 왕복 시험
    screens        화면 연결 그래프 — 고아·막다른·죽은 버튼
    flow           전체 플로우 훑기 — 32화면을 실제 브라우저로 열어 확인
    api            API 서버 (http://localhost:8000/docs)
    infra          postgres + redis 컨테이너
    migrate        알렘빅 upgrade head
    seed           마스터 시드 적재
    notify         알림 예약 (--dry 로 미리보기)

  == 프론트 ==
    web-pull       G: 소스 → 로컬 작업본으로 복사 + npm install
    web            로컬 작업본에서 next dev (http://localhost:3000)
    web-build      로컬 작업본에서 타입체크 + 프로덕션 빌드
    web-push       로컬 작업본 → G: 로 되돌려 넣기

  ★ 왜 프론트만 따로 도는가
    이 저장소는 구글 드라이브에 있습니다. 드라이브 마운트는 파일 쓰기가
    로컬 대비 약 170배 느리고, NTFS 가 아니라 정션(mklink /J)도 안 됩니다.
    node_modules 3만 개를 여기 풀면 동기화가 끝나지 않습니다.

    그래서 **소스만** 로컬로 미러링해 개발하고(web-pull → web),
    끝나면 되돌려 넣습니다(web-push). node_modules 는 로컬에만 남습니다.
#>
param([Parameter(Position = 0)][string]$Task = "help",
      [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)

$Root    = $PSScriptRoot
$VenvDir = "$env:USERPROFILE\.venvs\sajudang"
$Py      = "$VenvDir\Scripts\python.exe"
$WebWork = "$env:LOCALAPPDATA\sajudang-web"

# web-pull 이 로컬로 옮기는 것 — 소스만. node_modules/.next 는 로컬에만 산다.
$WebSources = @(
  @{ From = "apps\web";              To = "apps\web" },
  @{ From = "packages\shared-types"; To = "packages\shared-types" }
)
$WebExclude = @("node_modules", ".next", "out")

function Need-Venv {
  if (-not (Test-Path $Py)) {
    Write-Host "venv 가 없습니다. 먼저:  .\dev.ps1 setup" -ForegroundColor Yellow
    exit 1
  }
}

function Mirror($src, $dst) {
  if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Force $dst | Out-Null }
  $args = @($src, $dst, "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP")
  foreach ($x in $WebExclude) { $args += @("/XD", $x) }
  robocopy @args | Out-Null
  # robocopy 는 0~7 이 정상
  if ($LASTEXITCODE -ge 8) { Write-Host "복사 실패: $src" -ForegroundColor Red; exit 1 }
}

function Web-Pull {
  foreach ($m in $WebSources) {
    Mirror "$Root\$($m.From)" "$WebWork\$($m.To)"
  }
  Write-Host "소스를 로컬로 옮겼습니다: $WebWork" -ForegroundColor Green
  Push-Location "$WebWork\apps\web"
  npm install --no-audit --no-fund
  Pop-Location
}

function Need-Web {
  if (-not (Test-Path "$WebWork\apps\web\node_modules")) {
    Write-Host "먼저:  .\dev.ps1 web-pull" -ForegroundColor Yellow
    exit 1
  }
}

switch ($Task) {

  # ── 파이썬 ────────────────────────────────────────────────
  "setup" {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
      Write-Host "uv 가 필요합니다:  pip install uv" -ForegroundColor Yellow; exit 1
    }
    uv python install 3.11
    uv venv $VenvDir --python 3.11
    uv pip install --python $Py -r "$Root\requirements.txt"
    & $Py -c "import sxtwl, zoneinfo; zoneinfo.ZoneInfo('Asia/Seoul'); print('OK: sxtwl + tzdata')"
  }

  "test"    { Need-Venv; Push-Location $Root; & $Py -m pytest tests -q; Pop-Location }
  "dist"    { Need-Venv; Push-Location $Root; & $Py tools\distribution.py; Pop-Location }
  "dup"     { Need-Venv; Push-Location $Root; & $Py tools\dup_rate.py; Pop-Location }
  "screens" { Need-Venv; Push-Location $Root; & $Py tools\screen_graph.py; Pop-Location }
  "flow" {
    Need-Venv
    $target = if ($Rest) { $Rest[0] } else { "http://localhost:3000" }
    Push-Location $Root; & $Py toolslow_check.py $target; Pop-Location
  }
  "fixtures"{ Need-Venv; Push-Location $Root; & $Py tools\make_fixtures.py @Rest; Pop-Location }
  "sheet"   { Need-Venv; Push-Location $Root; & $Py tools\fixture_sheet.py 대조표.md; Pop-Location }

  "engine-check" {
    Need-Venv; Push-Location $Root
    & $Py -m pytest tests -q;          if ($LASTEXITCODE) { Pop-Location; exit 1 }
    & $Py tools\distribution.py;       if ($LASTEXITCODE) { Pop-Location; exit 1 }
    & $Py tools\dup_rate.py;           if ($LASTEXITCODE) { Pop-Location; exit 1 }
    Pop-Location
    Write-Host "engine-check 통과" -ForegroundColor Green
    Write-Host "※ 회귀 50건이 skip 이면 아직 관문을 통과한 게 아닙니다. .\dev.ps1 sheet" -ForegroundColor Yellow
  }

  "api" {
    Need-Venv; Push-Location "$Root\services\api"
    & $Py -m uvicorn main:app --reload --port 8000
    Pop-Location
  }

  "infra"   { docker compose up -d postgres redis }

  "migrate" {
    Need-Venv
    if (-not $env:DATABASE_URL) {
      Write-Host "DATABASE_URL 을 먼저 설정하세요." -ForegroundColor Yellow; exit 1
    }
    Push-Location $Root; & $Py -m alembic upgrade head; Pop-Location
  }

  "seed" {
    Need-Venv; Push-Location "$Root\services\api"; & $Py -m scripts.seed; Pop-Location
  }

  "notify" {
    Need-Venv; Push-Location "$Root\services\api"; & $Py -m scripts.notify @Rest; Pop-Location
  }

  # ── 프론트 ────────────────────────────────────────────────
  "plan" { Need-Venv; & $Py "$Root	oolsill_expected.py" --plan }
  "fill" {
    Need-Venv
    if (-not $Rest) { Write-Host "받아적은 파일을 주세요:  .\dev.ps1 fill 받아적음.txt" -ForegroundColor Yellow; exit 1 }
    & $Py "$Root	oolsill_expected.py" @Rest
  }
  "funnel" { Need-Venv; & $Py "$Root	oolsunnel.py" @Rest }
  "migrate-sqlite" {
    Need-Venv
    # ★ 마이그레이션을 실제로 돌려 본다. 안 하면 영영 미검증으로 남는다.
    $tmp = Join-Path $env:TEMP ("sajudang-mig-" + [guid]::NewGuid().ToString("N").Substring(0,8))
    New-Item -ItemType Directory -Force $tmp | Out-Null
    # 역슬래시를 슬래시로. 정규식이라 '\\' 두 자로 적어야 합니다.
    $env:DATABASE_URL = "sqlite:///" + ($tmp -replace '\\', '/') + "/m.sqlite"
    Write-Host "DATABASE_URL = $env:DATABASE_URL" -ForegroundColor Cyan
    $ok = $true
    foreach ($step in @("upgrade head", "downgrade base", "upgrade head")) {
      Write-Host "  alembic $step" -ForegroundColor DarkGray
      & $Py -m alembic $step.Split(" ")
      if ($LASTEXITCODE -ne 0) { $ok = $false; break }
    }
    Remove-Item -Recurse -Force $tmp -EA SilentlyContinue
    Remove-Item Env:DATABASE_URL -EA SilentlyContinue
    if ($ok) { Write-Host "마이그레이션 왕복 OK" -ForegroundColor Green }
    else { Write-Host "마이그레이션 실패" -ForegroundColor Red; exit 1 }
  }
  "web-pull" { Web-Pull }

  "web" {
    Need-Web
    Push-Location "$WebWork\apps\web"
    Write-Host "작업본: $WebWork\apps\web  (편집도 여기서 하고, 끝나면 web-push)" -ForegroundColor Cyan
    npm run dev
    Pop-Location
  }

  "web-build" {
    Need-Web
    Push-Location "$WebWork\apps\web"
    npx tsc --noEmit; if ($LASTEXITCODE) { Pop-Location; exit 1 }
    npm run build
    Pop-Location
  }

  "web-push" {
    if (-not (Test-Path "$WebWork\apps\web")) {
      Write-Host "로컬 작업본이 없습니다." -ForegroundColor Yellow; exit 1
    }
    foreach ($m in $WebSources) {
      Mirror "$WebWork\$($m.To)" "$Root\$($m.From)"
    }
    Write-Host "로컬 작업본을 G: 로 되돌렸습니다." -ForegroundColor Green
  }

  default { Get-Help $PSCommandPath -Detailed }
}
