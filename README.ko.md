# AdMob Skills

[English](README.md)

Codex, Claude Code와 기타 호환 에이전트에서 Google AdMob을 연동할 수 있는 [Agent Skill](https://agentskills.io/specification)입니다.

| 작업 | 지원 범위 |
| --- | --- |
| **리포트 API** | Google OAuth 설정, 게시자 계정·앱·광고 단위 조회, AdMob Network 및 미디에이션 리포트. Python 3.9 이상에서 실행되는 CLI를 제공합니다. |
| **모바일 SDK** | Android와 iOS 네이티브 앱의 SDK 설정, UMP 동의 처리, 테스트 광고, 오류 진단. Android GMA Next-Gen과 Legacy 프로젝트를 모두 안내합니다. |

## 설치

스킬을 사용할 프로젝트 디렉터리에서 터미널을 열고 아래 명령을 실행합니다. npm이 포함된 Node.js 22.20 이상이 필요합니다. [Node.js 다운로드](https://nodejs.org/)

```sh
npx skills add kmshack/AdmobSkills
```

설치 화면이 표시되면 사용할 에이전트를 선택하고, 현재 프로젝트에만 설치하려면 **Project**, 사용자 계정의 모든 프로젝트에서 쓰려면 **Global**을 고릅니다. 설치 도구가 감지한 에이전트를 자동으로 선택하거나, 선택 화면에서 Codex처럼 `.agents/skills` 경로를 공유하는 에이전트를 기본으로 포함할 수 있습니다. 설치 대상을 직접 지정하려면 `-a`를 사용하세요. [Skills CLI 옵션](https://github.com/vercel-labs/skills/blob/main/docs/commands.md#skills-add)

### 옵션으로 설치 대상과 범위 지정

```sh
# 현재 프로젝트에 Codex용으로 설치
npx skills add kmshack/AdmobSkills --skill google-admob -a codex -y

# Claude Code에 글로벌 설치
npx skills add kmshack/AdmobSkills --skill google-admob -a claude-code -g -y

# Codex와 Claude Code 모두에 글로벌 설치
npx skills add kmshack/AdmobSkills --skill google-admob -a codex -a claude-code -g -y
```

`-y`는 설치 질문을 건너뜁니다. `-y`를 사용하면서 `-g`를 생략하면 현재 프로젝트에 설치됩니다.

### 수동 설치

저장소를 클론한 뒤 `skills/google-admob/` 폴더 전체를 사용하는 에이전트의 스킬 경로로 복사합니다. 프로젝트 경로는 스킬을 사용할 프로젝트를 기준으로 합니다.

```sh
git clone https://github.com/kmshack/AdmobSkills.git
```

| 에이전트 | 프로젝트 경로 | 개인 경로 | 호출 |
| --- | --- | --- | --- |
| Codex | `.agents/skills/` | `~/.agents/skills/` | `$google-admob` 또는 `/skills`에서 선택 |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | `/google-admob` |

macOS 또는 Linux에서 개인용으로 설치하려면 클론을 만든 상위 디렉터리에서 실행합니다.

```sh
# Codex
mkdir -p "$HOME/.agents/skills"
cp -R AdmobSkills/skills/google-admob "$HOME/.agents/skills/"

# Claude Code
mkdir -p "$HOME/.claude/skills"
cp -R AdmobSkills/skills/google-admob "$HOME/.claude/skills/"
```

작업할 프로젝트에서 세션을 엽니다. 다른 Agent Skills 호환 에이전트에서는 해당 제품의 스킬 경로에 같은 폴더를 복사합니다. API 조회를 실행하려면 셸, Python 3.9 이상, Google에 대한 HTTPS 접근, 실행 프로세스에 제공된 인증 정보가 필요합니다. [Codex 공식 설치 문서](https://learn.chatgpt.com/docs/build-skills), [Claude Code 공식 설치 문서](https://code.claude.com/docs/en/skills)

## 사용 예시

Codex에서는 `$google-admob`, Claude Code에서는 `/google-admob` 뒤에 요청을 입력합니다.

- “게시자 계정 시간대를 기준으로 어제의 앱별 AdMob Network 예상 수익과 노출수를 조회해줘. 누락된 데이터는 표시해줘.”
- “이 Android 화면에 고정형 적응형 테스트 배너를 추가해줘. 기존 Google Mobile Ads SDK와 UMP 동의 흐름을 재사용해줘.”

## 터미널에서 리포트 조회

1. [로컬 OAuth 설정](skills/google-admob/references/oauth-setup.md)을 따라 Google Cloud에서 AdMob API를 활성화하고 브라우저에서 권한을 승인합니다. 이미 인증을 마쳤다면 [API 가이드](skills/google-admob/references/reporting-api.md)의 액세스 토큰 또는 갱신 환경변수를 사용할 수 있습니다.
2. 클론한 저장소의 루트에서 계정을 확인한 뒤 리포트를 조회합니다. 예제의 게시자 ID와 기간은 실제 조회할 값으로 바꿉니다. 시작일과 종료일을 모두 포함합니다.

```sh
ADMOB_CLI=skills/google-admob/scripts/admob.py
python3 "$ADMOB_CLI" accounts

PUB_ID=pub-1234567890123456
python3 "$ADMOB_CLI" report --publisher-id "$PUB_ID" \
  --type network --start-date 2026-01-01 --end-date 2026-01-07 \
  --dimension DATE --dimension APP \
  --metric IMPRESSIONS --metric ESTIMATED_EARNINGS
```

미디에이션 광고 소스까지 조회하려면 `--type mediation`을 사용합니다. 전체 명령은 `python3 "$ADMOB_CLI" --help`에서 확인할 수 있습니다. 앱과 광고 단위 목록에는 `admob.readonly` 권한이 필요합니다. 응답의 헤더에서 통화와 시간대를 확인하고, 푸터에서 데이터 경고와 행 제한을 점검합니다. OAuth 인증 정보와 실제 계정 데이터는 저장소 밖에 보관합니다.

## 구성

- [스킬 시작 파일](skills/google-admob/SKILL.md)
- [OAuth 설정](skills/google-admob/references/oauth-setup.md) 및 [리포트 API 가이드](skills/google-admob/references/reporting-api.md)
- [네이티브 모바일 SDK 가이드](skills/google-admob/references/mobile-sdk.md)
- [리포트 CLI](skills/google-admob/scripts/admob.py)

## 라이선스

[MIT](LICENSE)
