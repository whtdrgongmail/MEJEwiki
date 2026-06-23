#!/usr/bin/env python3
"""
FEWK 3판 편집본 → 독자용 샘플 변환기

입력:
  [3판 FEWK Core Rulebook]/   — 106 본문 + 15 부 README
  [3판 FEWK World Book]/      — 170 본문 + 부 README들

출력:
  content/corerulebook/**.md
  content/worldbook/**.md

제거 대상:
  1. <!-- 편집 메모 -->...--> HTML 주석 블록 (전체)
  2. **중점**: ... (한 줄)
  3. **소스**: ... (한 줄, 여러 줄 포함)
  4. **상태**: ... (한 줄)
  5. 상단 "예상 분량"·"정식 명칭" 같은 메타 필드 (선택적)

유지:
  - 제목, 본문 산문, 예시 상자, 표, 내부 링크, 관련 링크 섹션
"""

import re
import shutil
from pathlib import Path

# ─── 경로 ───
BASE = Path("/Users/whtdrgon/Library/CloudStorage/GoogleDrive-whtdrgon@gmail.com/내 드라이브/_Code/_FEWK 룰북 계획")
CORE_SRC = BASE / "[3판 FEWK Core Rulebook]"
WORLD_SRC = BASE / "[3판 FEWK World Book]"
OUT = BASE / "_ClaudeCode_Git_FEWK" / "FEWKbooks" / "content"
CORE_OUT = OUT / "corerulebook"
WORLD_OUT = OUT / "worldbook"

# ─── 제거 패턴 ───
# HTML 편집 메모 주석 블록 전체
EDIT_MEMO = re.compile(r'<!--\s*편집 메모[^>]*?-->', re.DOTALL)
EDIT_MEMO_LOOSE = re.compile(r'<!--[\s\S]*?편집 메모[\s\S]*?-->', re.DOTALL)

# 상단 메타 필드 (한 줄 단위)
META_LINE = re.compile(r'^\*\*(중점|소스|상태|참조 명세|원고 매핑|AI 참조 태그|파일 ID|버전|분야|선행|후속)\*\*:.*$', re.MULTILINE)

# 여러 줄에 걸친 소스 (예: **소스**: Core 1\n· Pack 2)
MULTILINE_SOURCE = re.compile(r'^\*\*소스\*\*:.*?(?=\n\*\*|\n---|\n##|\n$)', re.MULTILINE | re.DOTALL)


def clean_markdown(text: str) -> str:
    """편집 메타 제거."""
    # 1. HTML 편집 메모 주석 블록 제거
    text = EDIT_MEMO_LOOSE.sub('', text)

    # 2. 상단 메타 필드 라인 제거
    text = META_LINE.sub('', text)

    # 3. 연속된 빈 줄 정리
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 4. 문서 시작부의 연속 빈 줄 제거
    text = text.lstrip('\n')

    # 5. 헤더 직후 불필요한 `---` 중복 제거 (메타 제거 후 남을 수 있음)
    # 첫 `---` 바로 뒤에 `---`이 또 나오면 하나 제거
    text = re.sub(r'---\n\n+---\n', '---\n', text)

    # 6. 제목 직후 `---\n\n## 예정 섹션` 같은 남은 구조 정리 (Phase 2 스텁이 남긴 흔적)
    # "## 예정 섹션" 같은 스텁 전용 섹션 제거
    text = re.sub(r'\n## 예정 섹션\n(.*?)(?=\n## |\n---|\Z)', '', text, flags=re.DOTALL)

    return text.strip() + '\n'


def convert_tree(src_root: Path, out_root: Path, src_label: str):
    """한 책의 전체 디렉토리 트리를 변환."""
    out_root.mkdir(parents=True, exist_ok=True)
    count = 0
    skipped = 0

    for md_path in src_root.rglob("*.md"):
        # 루트 메타 문서는 제외 (_Spec, _작업계획, _진척상태)
        if md_path.name.startswith('_'):
            skipped += 1
            continue

        # 상대 경로 계산 → 출력 경로
        rel = md_path.relative_to(src_root)
        out_path = out_root / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # 읽고 변환하고 쓰기
        try:
            text = md_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            print(f"  SKIP (encoding): {rel}")
            skipped += 1
            continue

        cleaned = clean_markdown(text)
        out_path.write_text(cleaned, encoding='utf-8')
        count += 1

    print(f"[{src_label}] 변환 완료: {count} 파일 (스킵 {skipped})")
    return count


def main():
    print("=== FEWK 3판 편집본 → 독자용 샘플 변환 ===\n")

    # Core Rulebook 변환
    print("Core Rulebook 변환 중...")
    core_count = convert_tree(CORE_SRC, CORE_OUT, "Core Rulebook")

    # World Book 변환
    print("\nWorld Book 변환 중...")
    world_count = convert_tree(WORLD_SRC, WORLD_OUT, "World Book")

    print(f"\n총 {core_count + world_count} 파일 변환 완료.")
    print(f"출력 위치:\n  {CORE_OUT}\n  {WORLD_OUT}")


if __name__ == "__main__":
    main()
