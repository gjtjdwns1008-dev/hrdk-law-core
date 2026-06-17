"""
hrdk_law_core.sheets
--------------------
Google Sheets 인증 및 총괄현황표 로깅 공통 헬퍼.

두 레포에서 중복으로 작성하던 gspread 인증 로직과
총괄현황표 로깅을 하나로 통합합니다.

사용법:
    from hrdk_law_core.sheets import get_sheet_client, log_to_summary_sheet
"""

import json
from datetime import datetime, timezone, timedelta

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_sheet_client(gcp_service_account_json: str, sheet_url: str):
    """
    Google Sheets 클라이언트와 스프레드시트 객체를 반환합니다.

    Parameters
    ----------
    gcp_service_account_json : GCP 서비스 계정 JSON 문자열
    sheet_url                : 구글 시트 KEY(URL의 /d/ 뒤 부분)

    Returns
    -------
    (gspread.Client, gspread.Spreadsheet) 튜플
    설정이 없으면 (None, None) 반환
    """
    if not gcp_service_account_json or not sheet_url:
        print("  ⚠️ 구글 시트 설정 정보가 없어 건너뜁니다.")
        return None, None

    creds_dict = json.loads(gcp_service_account_json.strip(), strict=False)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_url)
    return client, spreadsheet


def log_to_summary_sheet(
    spreadsheet,
    total_len: int,
    matched_len: int,
    status: str = "🟢 정상 작동",
    log: str = "특이사항 없음",
) -> None:
    """
    총괄현황표 탭에 실행 결과를 한 줄 추가합니다.

    5개 컬럼: 수집일자(KST) | 총 검토건수 | 연관 법령건수 | 모니터링 상태 | 실행 로그
    """
    try:
        summary_sheet = spreadsheet.worksheet("총괄현황표")
        kst_now = datetime.now(timezone(timedelta(hours=9)))
        summary_row = [
            kst_now.strftime("%Y-%m-%d %H:%M:%S"),
            total_len,
            matched_len,
            status,
            log,
        ]
        summary_sheet.append_row(summary_row)
        print(f"  📊 [총괄현황표 기록] 상태: {status}")
    except Exception as e:
        print(f"  ⚠️ 총괄현황표 기록 실패: {e}")


def get_column_letter(n: int) -> str:
    """숫자를 엑셀 열 문자로 변환합니다. (1→A, 17→Q)"""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def upsert_daily_summary_row(
    spreadsheet,
    sheet_name: str,
    target_date_display: str,
    cols_before_status: list,
    status_symbol: str,
    log: str = "",
    status_col_name: str = "상태",
    log_col_name: str = "로그",
) -> None:
    """
    [옵션 B] 총괄현황표에서 같은 날짜 행을 찾아 상태 칸에 시도 이력을 누적합니다.
    - 그날 행이 없으면: 새 줄 추가 (상태 = "HH:MM{심볼}")
    - 그날 행이 있으면: 상태 칸에 " → HH:MM{심볼}" 이어붙이고, 로그/건수도 갱신

    예) 상태 칸: "04:13🔴 → 08:47🔴 → 12:31🟢"  (한 줄로 그날 시도 이력이 다 보임)

    target_date_display: 행을 식별할 날짜 문자열 (예: "2026년_06월_17일")
    cols_before_status: 상태 칸 앞에 올 값들 (예: [날짜, 총건수, ...])
    status_symbol: 이번 시도 결과 심볼 (예: "🟢", "🔴")
    """
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception as e:
        print(f"  ⚠️ '{sheet_name}' 시트를 찾을 수 없음: {e}")
        return

    kst_now = datetime.now(timezone(timedelta(hours=9)))
    hhmm = kst_now.strftime("%H:%M")
    this_attempt = f"{hhmm}{status_symbol}"

    try:
        all_values = ws.get_all_values()
        header = all_values[0] if all_values else []
        # 상태/로그 컬럼 인덱스 (없으면 끝에 가정)
        try:
            status_idx = header.index(status_col_name)
        except ValueError:
            status_idx = len(cols_before_status)
        try:
            log_idx = header.index(log_col_name)
        except ValueError:
            log_idx = status_idx + 1

        # 같은 날짜 행 찾기 (A열 = 날짜)
        target_row_num = None
        for i, row in enumerate(all_values[1:], start=2):
            if row and row[0] == target_date_display:
                target_row_num = i
                existing_status = row[status_idx] if status_idx < len(row) else ""
                break

        if target_row_num is None:
            # 그날 첫 실행 → 새 줄
            new_row = list(cols_before_status)
            # status_idx 위치까지 채우고 상태/로그 추가
            while len(new_row) < status_idx:
                new_row.append("")
            new_row.append(this_attempt)
            new_row.append(log)
            ws.append_row(new_row, value_input_option="RAW")
            print(f"  📊 [총괄현황표] {target_date_display} 새 줄 ({this_attempt})")
        else:
            # 그날 재실행 → 상태 칸에 누적
            new_status = (existing_status + " → " + this_attempt) if existing_status else this_attempt
            col_letter = get_column_letter(status_idx + 1)
            log_letter = get_column_letter(log_idx + 1)
            ws.update(f"{col_letter}{target_row_num}", [[new_status]], value_input_option="RAW")
            if log:
                ws.update(f"{log_letter}{target_row_num}", [[log]], value_input_option="RAW")
            # 건수 칸들도 최신값으로 갱신 (성공 시 의미 있음)
            for ci, val in enumerate(cols_before_status[1:], start=2):
                ws.update(f"{get_column_letter(ci)}{target_row_num}", [[val]], value_input_option="RAW")
            print(f"  📊 [총괄현황표] {target_date_display} 누적 ({new_status})")
    except Exception as e:
        print(f"  ⚠️ 총괄현황표 누적 기록 실패: {e}")
