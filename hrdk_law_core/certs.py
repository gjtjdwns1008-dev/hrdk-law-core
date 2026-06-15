"""
hrdk_law_core.certs
-------------------
국가기술자격 종목 단일 출처(Single Source of Truth).

종목 CSV는 이 패키지 안(data/qnet_certs_2026.csv)에 한 부만 존재하며,
law-monitor와 HRDK-LAW-RADAR가 모두 이 모듈을 통해 종목을 읽습니다.
종목이 매년 바뀌면 코어의 CSV 한 개만 교체하면 양쪽에 동시 반영됩니다.

사용법:
    from hrdk_law_core.certs import get_qnet_certs_text, get_qnet_certs_list

    # RADAR 스타일: 종목 전체를 텍스트로 (프롬프트에 통째로 주입)
    text = get_qnet_certs_text()

    # law-monitor 스타일: 직무분야별로 묶은 텍스트 ([건설] 종목a, 종목b ...)
    text = get_qnet_certs_text(group_by_field=True)

    # 리스트로 받기
    certs = get_qnet_certs_list()   # ['공공조달관리사', '공장관리기술사', ...]
"""

import csv
from functools import lru_cache
from importlib import resources

# 패키지에 동봉된 종목 CSV 파일명. 연도 갱신 시 이 상수만 바꾸면 됩니다.
_CSV_FILENAME = "qnet_certs_2026.csv"


@lru_cache(maxsize=4)
def _load_rows() -> tuple:
    """
    패키지에 동봉된 종목 CSV를 읽어 (직무분야, 종목명) 튜플 목록을 반환합니다.
    pip로 설치된 패키지 안에서도 안전하게 파일을 읽기 위해 importlib.resources 사용.
    결과는 캐시되어 매번 파일을 다시 읽지 않습니다.
    """
    rows = []
    data_pkg = resources.files("hrdk_law_core").joinpath("data", _CSV_FILENAME)
    with data_pkg.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            field = (r.get("직무분야") or "").strip()
            name = (r.get("종목명") or "").strip()
            if name:
                rows.append((field, name))
    return tuple(rows)


def get_qnet_certs_list() -> list:
    """종목명만 담은 리스트를 반환합니다."""
    return [name for _field, name in _load_rows()]


def get_qnet_certs_count() -> int:
    """등록된 종목 개수를 반환합니다."""
    return len(_load_rows())


def get_qnet_certs_text(group_by_field: bool = False) -> str:
    """
    종목을 프롬프트 주입용 텍스트로 반환합니다.

    Parameters
    ----------
    group_by_field : False(기본) → 종목명을 줄바꿈으로 나열 (RADAR 스타일)
                     True        → 직무분야별로 묶어서 "[분야] 종목a, 종목b" (law-monitor 스타일)
    """
    rows = _load_rows()

    if not group_by_field:
        # RADAR 스타일: CSV 헤더 + 종목 나열 (기존 load_qualification_list 출력과 호환)
        lines = ["직무분야,종목명"]
        lines += [f"{field},{name}" for field, name in rows]
        return "\n".join(lines)

    # law-monitor 스타일: 직무분야별 그룹핑
    grouped: dict[str, list[str]] = {}
    for field, name in rows:
        grouped.setdefault(field or "기타", []).append(name)

    blocks = []
    for field, names in grouped.items():
        blocks.append(f"[{field}] " + ", ".join(names))
    return "\n".join(blocks)
