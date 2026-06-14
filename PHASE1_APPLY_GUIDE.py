# ══════════════════════════════════════════════════════════════
# Phase 1 적용 가이드
# ══════════════════════════════════════════════════════════════
#
# 1) 신규 레포 생성
#    GitHub에서 "hrdk-law-core" 이름으로 private 레포 생성 후
#    이 폴더 전체를 push합니다.
#
# 2) 두 레포의 requirements.txt 맨 아래에 한 줄 추가
#    (YOUR_GITHUB_ACCOUNT를 실제 계정명으로 교체)
#
#    hrdk-law-core @ git+https://github.com/YOUR_GITHUB_ACCOUNT/hrdk-law-core.git
#
# 3) GitHub Actions 워크플로우(.github/workflows/main.yml)에
#    아래 step을 "pip install -r requirements.txt" 앞에 삽입
#
# ──────────────────────────────────────────────────────────────
# YAML에 추가할 step (LAW-RADAR, law-monitor 양쪽 모두):
# ──────────────────────────────────────────────────────────────
#
#      - name: Install shared core library
#        run: |
#          pip install \
#            "hrdk-law-core @ git+https://github.com/${{ secrets.GITHUB_ACCOUNT }}/hrdk-law-core.git"
#
# ──────────────────────────────────────────────────────────────
# 또는, PAT(Personal Access Token) 없이 같은 계정 private 레포에
# 접근하려면 GITHUB_TOKEN을 사용하는 방식:
#
#      - name: Install shared core library
#        run: |
#          pip install \
#            "hrdk-law-core @ git+https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/YOUR_ACCOUNT/hrdk-law-core.git"
#
# ══════════════════════════════════════════════════════════════
# 4) LAW-RADAR의 config.py에 두 줄 추가
# ══════════════════════════════════════════════════════════════

# config.py 추가분 (HRDK-LAW-RADAR/config.py 하단에 붙여넣기)
import os

# 공유 코어 라이브러리 설정
WORKNET_API_KEY = os.environ.get("WORKNET_API_KEY", "")   # GitHub Secrets에 등록

# SQLite 지식베이스 경로 (레포 루트에 hrdk_law.db 파일 포함 또는 Actions Artifact로 배포)
DB_PATH = os.environ.get("DB_PATH", "hrdk_law.db")

# ══════════════════════════════════════════════════════════════
# 5) LAW-RADAR의 main.py를 RADAR_main_updated.py로 교체
# ══════════════════════════════════════════════════════════════
#    RADAR_main_updated.py → main.py 로 이름 변경하여 교체

# ══════════════════════════════════════════════════════════════
# 6) law-monitor의 law_scrapper.py를 2줄로 교체 (선택)
# ══════════════════════════════════════════════════════════════
#
# 기존 law_scrapper.py 내용을 전부 지우고 아래 2줄로 대체:
#
#   from hrdk_law_core.scraper import get_base_laws   # noqa: F401
#   # 끝. config에서 LAW_API_KEY, TARGET_DATE를 읽도록 main.py에서 인자로 전달하세요.
#
# ══════════════════════════════════════════════════════════════
# 7) hrdk_law.db 배포 방법 (두 가지 옵션)
# ══════════════════════════════════════════════════════════════
#
# [옵션 A] 레포에 직접 커밋 (DB 파일이 작을 때 권장, 현재 ~2MB)
#   git add hrdk_law.db
#   git commit -m "chore: SQLite 지식베이스 업데이트 (직능연 22,772행)"
#
# [옵션 B] GitHub Actions Artifact로 배포 (나중에 용량이 커지면)
#   - build_sqlite.py를 별도 workflow로 실행 후 Artifact 업로드
#   - LAW-RADAR workflow에서 Artifact 다운로드 후 사용
