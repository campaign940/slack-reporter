# Slack Reporter

GeekNews RSS 피드를 Claude Opus 4.5로 요약하여 Slack에 자동으로 전송하는 시스템입니다.

## 구성 요소

### 1. GeekNews Reporter (`geeknews_reporter.py`)
- GeekNews RSS 피드에서 최신 기사를 가져와 Claude Opus 4.5로 요약
- 춘식이 캐릭터 말투로 자연스러운 리포팅 스크립트 생성
- Slack Block Kit 형식으로 메시지 전송

### 2. Slack Sender Skill (`slack-sender.skill`)
- Slack 메시지 전송을 위한 재사용 가능한 스킬 패키지
- 텍스트 메시지, Block Kit 메시지, 파일 업로드, 스레드 답장 지원

## 설치

### 필수 요구사항
- Python 3.7+
- Anthropic API 키
- Slack Bot Token

### Python 패키지 설치
```bash
pip install feedparser anthropic requests python-dotenv
```

### Slack 설정
1. Slack App 생성 및 Bot Token 발급
2. Bot에 필요한 권한 부여:
   - `chat:write`
   - `files:write`
   - `channels:read`

3. 스킬 설치 (선택사항):
```bash
# slack-sender.skill을 Claude Code에 설치
```

## 사용 방법

### 1. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 실제 값을 입력:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```bash
# Anthropic API Key
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Slack Bot Token
SLACK_BOT_TOKEN=your-slack-bot-token-here

# Slack Channel (default channel to send messages)
SLACK_CHANNEL=010-agent-news
```

### 2. 수동 실행
```bash
python3 geeknews_reporter.py
```

### 3. 자동화 (Cron)
매일 오전 9시에 자동 실행:
```bash
crontab -e

# 다음 줄 추가
0 9 * * * /usr/bin/python3 /path/to/geeknews_reporter.py
```

매 6시간마다 실행:
```bash
0 */6 * * * /usr/bin/python3 /path/to/geeknews_reporter.py
```

## 기능

### GeekNews Reporter
- ✅ RSS 피드에서 최신 10개 기사 자동 수집
- ✅ Claude Opus 4.5를 사용한 고품질 요약
- ✅ 춘식이 말투로 친근한 리포팅
- ✅ 제목에 원문 링크 자동 추가
- ✅ Slack Block Kit을 활용한 가독성 높은 포맷

### Slack Sender Skill
- ✅ 간단한 텍스트 메시지 전송
- ✅ Block Kit 형식화된 메시지
- ✅ 파일 업로드
- ✅ 스레드 답장
- ✅ 설정 파일 기반 토큰 관리

## 출력 예시

```
GeekNews 최신 기사 요약(2026.01.30)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Waymo 로보택시 어린이 충돌 사고
여러분 안녕하세요! 춘식이에요~ 오늘 첫 번째 소식은...

2. Mac Studio를 Ollama 호스트로 사용하기
두 번째 소식이에요! 요즘 Mac Studio를...
...
```

## 라이선스

MIT License

## 기여

이슈 및 Pull Request를 환영합니다!
