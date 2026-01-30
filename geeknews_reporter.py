#!/usr/bin/env python3
"""
GeekNews RSS를 Claude Opus 4.5로 요약하여 Slack에 전송하는 스크립트
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import feedparser
    import anthropic
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("필요한 패키지를 설치합니다...")
    subprocess.run([sys.executable, "-m", "pip", "install", "feedparser", "anthropic", "requests", "python-dotenv"], check=True)
    import feedparser
    import anthropic
    import requests
    from dotenv import load_dotenv

# .env 파일 로드 (파일이 없어도 환경 변수에서 읽음)
load_dotenv()

# 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "010-agent-news")
RSS_FEED_URL = "https://feeds.feedburner.com/geeknews-feed"
NUM_ARTICLES = 10

# 디버깅: 환경 변수 확인
print(f"🔍 디버깅: ANTHROPIC_API_KEY 길이 = {len(ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else 0}")
print(f"🔍 디버깅: SLACK_BOT_TOKEN 길이 = {len(SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else 0}")
print(f"🔍 디버깅: SLACK_CHANNEL = {SLACK_CHANNEL}")

# API 키 검증
if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    print("   환경 변수 또는 .env 파일을 확인하세요.")
    sys.exit(1)

if not SLACK_BOT_TOKEN:
    print("❌ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
    print("   환경 변수 또는 .env 파일을 확인하세요.")
    sys.exit(1)

def get_slack_config():
    """Slack 설정 반환"""
    return {
        "bot_token": SLACK_BOT_TOKEN,
        "default_channel": SLACK_CHANNEL
    }

def fetch_rss_feed():
    """RSS 피드 가져오기"""
    print("📡 RSS 피드를 가져오는 중...")

    # requests로 RSS 피드 다운로드
    try:
        response = requests.get(RSS_FEED_URL, timeout=30)
        response.raise_for_status()
        feed_content = response.content
    except requests.RequestException as e:
        print(f"❌ RSS 피드를 다운로드할 수 없습니다: {e}")
        sys.exit(1)

    # feedparser로 파싱
    feed = feedparser.parse(feed_content)

    # 디버깅 정보
    print(f"   피드 상태: {feed.get('status', 'unknown')}")
    print(f"   엔트리 수: {len(feed.entries)}")

    if not feed.entries:
        print("❌ RSS 피드를 파싱할 수 없습니다.")
        if hasattr(feed, 'bozo_exception'):
            print(f"   오류: {feed.bozo_exception}")
        sys.exit(1)

    articles = []
    for entry in feed.entries[:NUM_ARTICLES]:
        # description 또는 summary 사용
        content = entry.get("summary", "") or entry.get("description", "")

        articles.append({
            "title": entry.get("title", "제목 없음"),
            "link": entry.get("link", ""),
            "summary": content,
            "published": entry.get("published", "")
        })

    print(f"✅ {len(articles)}개의 기사를 가져왔습니다.")
    return articles

def summarize_with_claude(articles):
    """Claude Opus 4.5로 기사 요약"""
    print("🤖 Claude Opus 4.5로 요약 생성 중...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # 기사 정보를 텍스트로 변환
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"\n## 기사 {i}\n"
        articles_text += f"제목: {article['title']}\n"
        articles_text += f"링크: {article['link']}\n"
        articles_text += f"내용: {article['summary']}\n"
        articles_text += "---\n"

    prompt = f"""다음은 GeekNews의 최신 기사 {NUM_ARTICLES}개입니다.

{articles_text}

각 기사를 춘식이 캐릭터의 말투로 리포팅 스크립트를 작성해주세요.

요구사항:
1. 춘식이 말투 사용 ("~이에요", "~대요", "~네요", "~래요" 등)
2. 각 기사마다 구두로 말하는 것처럼 자연스럽게 작성
3. 이모티콘 사용 금지
4. 기사의 핵심 내용을 포함하되 친근하고 이해하기 쉽게 설명

다음 JSON 형식으로 응답해주세요:
{{
  "articles": [
    {{
      "number": 1,
      "title": "기사 제목",
      "link": "기사 링크",
      "script": "춘식이 말투로 작성된 리포팅 스크립트"
    }}
  ]
}}

JSON만 반환하고 다른 설명은 포함하지 마세요."""

    message = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # JSON 파싱
    try:
        # JSON 코드 블록에서 추출
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        print(f"✅ 요약 생성 완료")
        return result["articles"]
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        print(f"응답: {response_text}")
        sys.exit(1)

def create_slack_blocks(articles):
    """Slack Block Kit 형식으로 변환"""
    today = datetime.now().strftime("%Y.%m.%d")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"GeekNews 최신 기사 요약({today})"
            }
        },
        {
            "type": "divider"
        }
    ]

    for article in articles:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{article['number']}. <{article['link']}|{article['title']}>*\n{article['script']}"
            }
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"출처: <{RSS_FEED_URL}|GeekNews RSS Feed> | 리포터: 춘식이"
            }
        ]
    })

    return blocks

def send_to_slack(blocks):
    """Slack에 메시지 전송"""
    print("📤 Slack에 전송 중...")

    config = get_slack_config()
    token = config.get("bot_token")
    channel = config.get("default_channel")

    payload = json.dumps({
        "channel": channel,
        "blocks": blocks
    })

    result = subprocess.run([
        'curl', '-X', 'POST', 'https://slack.com/api/chat.postMessage',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        '-d', payload,
        '-s'
    ], capture_output=True, text=True, check=True)

    response = json.loads(result.stdout)

    if response.get('ok'):
        print(f"✅ 메시지가 전송되었습니다.")
        print(f"   채널: {channel}")
        print(f"   타임스탬프: {response.get('ts')}")
    else:
        print(f"❌ 메시지 전송 실패: {response.get('error')}")
        sys.exit(1)

def main():
    """메인 함수"""
    print("=" * 50)
    print("GeekNews RSS Reporter (Powered by Claude Opus 4.5)")
    print("=" * 50)
    print()

    # 1. RSS 피드 가져오기
    articles = fetch_rss_feed()

    # 2. Claude로 요약
    summaries = summarize_with_claude(articles)

    # 3. Slack Block Kit 생성
    blocks = create_slack_blocks(summaries)

    # 4. Slack에 전송
    send_to_slack(blocks)

    print()
    print("=" * 50)
    print("✅ 모든 작업이 완료되었습니다!")
    print("=" * 50)

if __name__ == "__main__":
    main()
