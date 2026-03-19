# -*- coding: utf-8 -*-
"""
DOCX -> HWPX 변환기 (유니코드 수식 -> HWP 수식 편집기)

입력: 제곱근_서논술_수행평가.docx
출력: 제곱근_서논술_수행평가.hwpx

수식은 hp:equation > hp:script 로 변환
텍스트는 hp:t 로 변환
표, 페이지 브레이크, 서식(색상/굵기/크기) 보존
"""

import os
import sys
import re
import io
import zipfile
import xml.etree.ElementTree as ET
from copy import deepcopy

# ============================================================
# 네임스페이스 등록
# ============================================================
NS = {
    'ha':  'http://www.hancom.co.kr/hwpml/2011/app',
    'hp':  'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hp10':'http://www.hancom.co.kr/hwpml/2016/paragraph',
    'hs':  'http://www.hancom.co.kr/hwpml/2011/section',
    'hc':  'http://www.hancom.co.kr/hwpml/2011/core',
    'hh':  'http://www.hancom.co.kr/hwpml/2011/head',
    'hhs': 'http://www.hancom.co.kr/hwpml/2011/history',
    'hm':  'http://www.hancom.co.kr/hwpml/2011/master-page',
    'hpf': 'http://www.hancom.co.kr/schema/2011/hpf',
    'dc':  'http://purl.org/dc/elements/1.1/',
    'opf': 'http://www.idpf.org/2007/opf/',
    'ooxmlchart': 'http://www.hancom.co.kr/hwpml/2016/ooxmlchart',
    'hwpunitchar': 'http://www.hancom.co.kr/hwpml/2016/HwpUnitChar',
    'epub': 'http://www.idpf.org/2007/ops',
    'config': 'urn:oasis:names:tc:opendocument:xmlns:config:1.0',
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

# DOCX 네임스페이스
WNS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# HWPX 네임스페이스 단축
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HS = '{http://www.hancom.co.kr/hwpml/2011/section}'
HH = '{http://www.hancom.co.kr/hwpml/2011/head}'
HC = '{http://www.hancom.co.kr/hwpml/2011/core}'

# ============================================================
# 수식 변환: 유니코드 -> HWP 수식 스크립트
# ============================================================

# 위첨자 매핑
SUPERSCRIPT_MAP = {
    '\u00B2': '2', '\u00B3': '3', '\u2074': '4', '\u2075': '5',
    '\u2076': '6', '\u2077': '7', '\u2078': '8', '\u2079': '9',
    '\u00B9': '1', '\u2070': '0',
}

def unicode_to_hwp_equation(text):
    """유니코드 수식 문자열을 HWP 수식 스크립트로 변환.

    변환 순서:
    1. sqrt(...) 를 먼저 처리 (원본 괄호 구조 유지)
    2. 위첨자 변환
    3. |a| 절댓값 변환
    """
    # --- Phase 1: sqrt 처리 (원본 텍스트에서 괄호 구조를 직접 탐색) ---
    def convert_sqrt(s):
        out = []
        i = 0
        while i < len(s):
            if s[i] == '\u221A' and i + 1 < len(s) and s[i + 1] == '(':
                # 매칭하는 닫는 괄호 찾기 (중첩 지원)
                depth = 0
                j = i + 1
                while j < len(s):
                    if s[j] == '(':
                        depth += 1
                    elif s[j] == ')':
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if depth == 0 and j < len(s):
                    inner = s[i + 2:j]  # 바깥 괄호 제외
                    inner = convert_sqrt(inner)  # 재귀
                    out.append('sqrt {' + inner + '}')
                    i = j + 1
                else:
                    out.append('sqrt{~}')
                    i += 1
            elif s[i] == '\u221A':
                # 뒤에 괄호 없는 독립 sqrt — 연속 숫자/문자/소수점을 모두 캡처
                j = i + 1
                if j < len(s) and s[j] == '-':
                    j += 1  # 음수 부호 포함
                if j < len(s) and (s[j].isalnum() or s[j] == '.'):
                    while j < len(s) and (s[j].isalnum() or s[j] == '.'):
                        j += 1
                    token = s[i + 1:j]
                    out.append('sqrt {' + token + '}')
                    i = j
                elif i + 1 < len(s) and s[i + 1] == ' ':
                    out.append('sqrt{~}')
                    i += 1
                else:
                    out.append('sqrt{~}')
                    i += 1
            else:
                out.append(s[i])
                i += 1
        return ''.join(out)

    result = convert_sqrt(text)

    # --- Phase 2: 위첨자 변환 ---
    for sup_char, digit in SUPERSCRIPT_MAP.items():
        result = result.replace(sup_char, '^{' + digit + '}')

    # --- Phase 3: |a| -> LEFT | a RIGHT | 변환 ---
    def convert_abs(s):
        out = []
        i = 0
        while i < len(s):
            if s[i] == '|':
                j = i + 1
                while j < len(s) and s[j] != '|':
                    j += 1
                if j < len(s) and (j - i) <= 10:  # 짧은 절댓값만
                    inner = s[i + 1:j]
                    out.append('LEFT | ' + inner + ' RIGHT |')
                    i = j + 1
                else:
                    out.append('|')
                    i += 1
            else:
                out.append(s[i])
                i += 1
        return ''.join(out)

    result = convert_abs(result)

    # --- Phase 4: ± -> +- ---
    result = result.replace('\u00B1', '+-')

    return result


def has_math_chars(text):
    """텍스트에 수식 문자가 포함되어 있는지 확인"""
    math_chars = set('\u221A\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079\u00B9\u2070\u00B1')
    # 파이프 문자로 둘러싸인 변수 패턴 (|a| 등)
    if re.search(r'\|[a-zA-Z]\|', text):
        return True
    for ch in text:
        if ch in math_chars:
            return True
    return False


def split_text_and_math(text):
    """텍스트를 일반 텍스트와 수식 부분으로 분리.

    문자 단위로 탐색하여 수식 토큰을 정확히 추출합니다.
    Returns: list of (type, content) where type is 'text' or 'math'
    """
    if not has_math_chars(text):
        return [('text', text)]

    SUPERSCRIPTS = set('\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079\u00B9\u2070')
    SQRT = '\u221A'

    segments = []
    i = 0
    text_buf = []

    def flush_text():
        if text_buf:
            segments.append(('text', ''.join(text_buf)))
            text_buf.clear()

    while i < len(text):
        ch = text[i]

        # --- sqrt(...) 패턴 ---
        if ch == SQRT and i + 1 < len(text) and text[i + 1] == '(':
            flush_text()
            # 매칭 괄호 찾기
            depth = 0
            j = i + 1
            while j < len(text):
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth == 0 and j < len(text):
                math_str = text[i:j + 1]
                # 뒤에 등호+값이 이어지면 수식에 포함
                # 단, 값 뒤에 한글이 바로 이어지면 수식이 아님 (예: "= 49의")
                k = j + 1
                rest = text[k:]
                eq_match = re.match(r'^(\s*=\s*-?\d+\.?\d*(?:/\d+\.?\d*)?)', rest)
                if eq_match:
                    after_pos = k + eq_match.end()
                    # 값 뒤에 한글(가-힣)이 바로 이어지면 포함하지 않음
                    if after_pos < len(text) and '\uAC00' <= text[after_pos] <= '\uD7A3':
                        pass  # 수식에 포함하지 않음
                    else:
                        math_str += eq_match.group(1)
                        k += eq_match.end()
                segments.append(('math', math_str))
                i = k
            else:
                segments.append(('math', SQRT))
                i += 1
            continue

        # --- 독립 sqrt (괄호 없이 숫자/변수가 바로 이어지는 경우) ---
        if ch == SQRT:
            flush_text()
            j = i + 1
            # 음수 부호
            if j < len(text) and text[j] == '-':
                j += 1
            # 연속 숫자/알파벳/소수점 캡처
            if j < len(text) and (text[j].isalnum() or text[j] == '.'):
                while j < len(text) and (text[j].isalnum() or text[j] == '.'):
                    j += 1
                math_str = text[i:j]
                # 뒤에 등호+값이 이어지면 수식에 포함
                # 단, 값 뒤에 한글이 바로 이어지면 포함하지 않음
                rest = text[j:]
                eq_match = re.match(r'^(\s*=\s*-?\d+\.?\d*(?:/\d+\.?\d*)?)', rest)
                if eq_match:
                    after_pos = j + eq_match.end()
                    if after_pos < len(text) and '\uAC00' <= text[after_pos] <= '\uD7A3':
                        pass  # 한글이 바로 이어지면 수식이 아님
                    else:
                        math_str += eq_match.group(1)
                        j += eq_match.end()
                segments.append(('math', math_str))
                i = j
            else:
                segments.append(('math', SQRT))
                i += 1
            continue

        # --- (expr)^N 패턴: ( 로 시작하고 ) 뒤에 위첨자 ---
        if ch == '(' and i > 0:
            # 앞 문자가 한글이면 수식이 아님 (예: "구하고,")
            prev_ch = text[i - 1] if i > 0 else ' '
            # ( 다음 내용이 숫자/연산자/변수인지 확인
            depth = 0
            j = i
            while j < len(text):
                if text[j] == '(':
                    depth += 1
                elif text[j] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth == 0 and j < len(text) and j + 1 < len(text) and text[j + 1] in SUPERSCRIPTS:
                flush_text()
                # 괄호 + 위첨자 전체 추출
                k = j + 1
                while k < len(text) and text[k] in SUPERSCRIPTS:
                    k += 1
                math_str = text[i:k]
                # 뒤에 등호+수식 이어지면 포함
                rest = text[k:]
                eq_match = re.match(r'^(\s*=\s*)', rest)
                if eq_match:
                    # = 뒤의 수식도 포함하지 않음 (별도 처리)
                    pass
                segments.append(('math', math_str))
                i = k
                continue

        # --- var^N / num^N 패턴: 알파벳 또는 숫자 뒤에 위첨자 ---
        if (ch.isalpha() or ch.isdigit()) and i + 1 < len(text) and text[i + 1] in SUPERSCRIPTS:
            flush_text()
            k = i + 1
            while k < len(text) and text[k] in SUPERSCRIPTS:
                k += 1
            segments.append(('math', text[i:k]))
            i = k
            continue

        # --- |a| 절댓값 패턴 ---
        if ch == '|' and i + 2 < len(text) and text[i + 1].isalpha() and text[i + 2] == '|':
            flush_text()
            segments.append(('math', text[i:i + 3]))
            i += 3
            continue

        # --- ± 패턴: ±숫자 또는 ±변수 ---
        if ch == '\u00B1':
            flush_text()
            j = i + 1
            while j < len(text) and (text[j].isalnum() or text[j] == '.' or text[j] == '/'):
                j += 1
            segments.append(('math', text[i:j]))
            i = j
            continue

        # --- 일반 문자 ---
        text_buf.append(ch)
        i += 1

    flush_text()

    # 인접한 수식 세그먼트 병합
    # 수식 - 짧은 연결자(= 등) - 수식 => 하나의 수식으로
    merged = []
    idx = 0
    while idx < len(segments):
        seg_type, seg_text = segments[idx]
        if seg_type == 'math' and idx + 2 < len(segments):
            next_type, next_text = segments[idx + 1]
            next2_type, next2_text = segments[idx + 2]
            if (next_type == 'text' and next2_type == 'math'
                    and len(next_text.strip()) <= 5
                    and re.match(r'^\s*[=<>+\-]\s*', next_text.strip())):
                merged_text = seg_text + next_text + next2_text
                merged.append(('math', merged_text))
                idx += 3
                continue
        merged.append((seg_type, seg_text))
        idx += 1

    return merged if merged else [('text', text)]


# ============================================================
# DOCX 파싱
# ============================================================

def parse_docx(docx_path):
    """DOCX 파일을 파싱하여 구조화된 콘텐츠 목록을 반환"""
    content_items = []

    with zipfile.ZipFile(docx_path) as z:
        with z.open('word/document.xml') as f:
            raw = f.read()
            root = ET.fromstring(raw)

    body = root.find(f'{W}body')
    if body is None:
        print("ERROR: body not found in DOCX")
        return content_items

    for child in body:
        tag = child.tag.split('}')[-1]

        if tag == 'tbl':
            content_items.append(parse_docx_table(child))
        elif tag == 'p':
            content_items.append(parse_docx_paragraph(child))
        # sectPr 은 무시

    return content_items


def parse_docx_paragraph(p_elem):
    """DOCX 단락 요소를 파싱"""
    result = {
        'type': 'paragraph',
        'runs': [],
        'has_page_break': False,
        'has_dotted_border': False,
        'has_single_border': False,
        'spacing_after': None,
        'spacing_before': None,
        'alignment': None,
    }

    # 단락 속성
    ppr = p_elem.find(f'{W}pPr')
    if ppr is not None:
        spacing = ppr.find(f'{W}spacing')
        if spacing is not None:
            result['spacing_after'] = spacing.get(f'{W}after')
            result['spacing_before'] = spacing.get(f'{W}before')

        jc = ppr.find(f'{W}jc')
        if jc is not None:
            result['alignment'] = jc.get(f'{W}val')

        # 하단 테두리 (점선/실선)
        pbdr = ppr.find(f'{W}pBdr')
        if pbdr is not None:
            bottom = pbdr.find(f'{W}bottom')
            if bottom is not None:
                bdr_val = bottom.get(f'{W}val', '')
                bdr_color = bottom.get(f'{W}color', '')
                if bdr_val == 'dotted':
                    result['has_dotted_border'] = True
                elif bdr_val == 'single':
                    result['has_single_border'] = True
                    result['border_color'] = bdr_color

    # 런(runs) 파싱
    for r in p_elem.findall(f'{W}r'):
        # 페이지 브레이크 확인
        br = r.find(f'{W}br')
        if br is not None and br.get(f'{W}type') == 'page':
            result['has_page_break'] = True
            continue

        t_el = r.find(f'{W}t')
        if t_el is None or t_el.text is None:
            continue

        run_data = {
            'text': t_el.text,
            'bold': False,
            'color': None,
            'size': None,  # 반값 (20 = 10pt)
            'font': None,
            'highlight': None,
        }

        rpr = r.find(f'{W}rPr')
        if rpr is not None:
            b = rpr.find(f'{W}b')
            if b is not None:
                val = b.get(f'{W}val', 'true')
                run_data['bold'] = val != 'false'

            bcs = rpr.find(f'{W}bCs')
            if bcs is not None and b is None:
                val = bcs.get(f'{W}val', 'true')
                run_data['bold'] = val != 'false'

            color = rpr.find(f'{W}color')
            if color is not None:
                run_data['color'] = color.get(f'{W}val')

            sz = rpr.find(f'{W}sz')
            if sz is not None:
                run_data['size'] = int(sz.get(f'{W}val', '20'))

            font = rpr.find(f'{W}rFonts')
            if font is not None:
                run_data['font'] = font.get(f'{W}ascii') or font.get(f'{W}eastAsia')

            shd = rpr.find(f'{W}shd')
            if shd is not None:
                run_data['highlight'] = shd.get(f'{W}fill')

        result['runs'].append(run_data)

    return result


def parse_docx_table(tbl_elem):
    """DOCX 표 요소를 파싱"""
    result = {
        'type': 'table',
        'rows': [],
        'col_widths': [],
    }

    # 열 너비
    grid = tbl_elem.find(f'{W}tblGrid')
    if grid is not None:
        for col in grid.findall(f'{W}gridCol'):
            w = col.get(f'{W}w', '0')
            result['col_widths'].append(int(w))

    # 행
    for tr in tbl_elem.findall(f'{W}tr'):
        row = []
        for tc in tr.findall(f'{W}tc'):
            cell = parse_docx_cell(tc)
            row.append(cell)
        result['rows'].append(row)

    return result


def parse_docx_cell(tc_elem):
    """DOCX 셀 요소를 파싱"""
    cell = {
        'paragraphs': [],
        'bg_color': None,
        'borders': {},
        'width': None,
        'valign': None,
    }

    tcpr = tc_elem.find(f'{W}tcPr')
    if tcpr is not None:
        # 배경색
        shd = tcpr.find(f'{W}shd')
        if shd is not None:
            cell['bg_color'] = shd.get(f'{W}fill')

        # 너비
        tcw = tcpr.find(f'{W}tcW')
        if tcw is not None:
            cell['width'] = int(tcw.get(f'{W}w', '0'))

        # 수직 정렬
        valign = tcpr.find(f'{W}vAlign')
        if valign is not None:
            cell['valign'] = valign.get(f'{W}val')

        # 테두리
        tcborders = tcpr.find(f'{W}tcBorders')
        if tcborders is not None:
            for side in ['top', 'left', 'bottom', 'right']:
                border = tcborders.find(f'{W}{side}')
                if border is not None:
                    cell['borders'][side] = {
                        'val': border.get(f'{W}val', 'none'),
                        'color': border.get(f'{W}color', '000000'),
                        'sz': border.get(f'{W}sz', '0'),
                    }

    # 단락들
    for p in tc_elem.findall(f'{W}p'):
        cell['paragraphs'].append(parse_docx_paragraph(p))

    return cell


# ============================================================
# HWPX 빌더
# ============================================================

class HwpxBuilder:
    """HWPX 문서를 빌드하는 클래스"""

    # 페이지 설정 (A4, 좁은 여백)
    PAGE_WIDTH = 59528
    PAGE_HEIGHT = 84186
    MARGIN_LEFT = 5669
    MARGIN_RIGHT = 5669
    MARGIN_TOP = 5669
    MARGIN_BOTTOM = 4252
    CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # 48190

    def __init__(self):
        self.equation_id_counter = 1000000001
        self.char_pr_list = []  # CharPr 정의 목록
        self.border_fill_list = []  # BorderFill 정의 목록
        self.para_pr_list = []  # ParaPr 정의 목록
        self.style_list = []  # Style 정의 목록

        # 기본 CharPr 등록 (id=0: 기본)
        self._register_default_styles()

    def _register_default_styles(self):
        """기본 스타일 등록"""
        # CharPr 0: 기본 (맑은 고딕 10pt)
        self.char_pr_list.append({
            'id': 0, 'font': 'Malgun Gothic', 'size': 1000,
            'bold': False, 'color': '#000000',
        })
        # CharPr 1: 제목 (맑은 고딕 15pt 흰색 굵게)
        self.char_pr_list.append({
            'id': 1, 'font': 'Malgun Gothic', 'size': 1500,
            'bold': True, 'color': '#FFFFFF',
        })
        # CharPr 2: 부제 (맑은 고딕 9pt 회색)
        self.char_pr_list.append({
            'id': 2, 'font': 'Malgun Gothic', 'size': 900,
            'bold': False, 'color': '#7F8C8D',
        })
        # CharPr 3: 부제 작은 (맑은 고딕 8pt 회색)
        self.char_pr_list.append({
            'id': 3, 'font': 'Malgun Gothic', 'size': 800,
            'bold': False, 'color': '#7F8C8D',
        })
        # CharPr 4: 안내 제목 (맑은 고딕 10pt 진한파랑 굵게)
        self.char_pr_list.append({
            'id': 4, 'font': 'Malgun Gothic', 'size': 1000,
            'bold': True, 'color': '#1A5276',
        })
        # CharPr 5: 안내 내용 (맑은 고딕 9pt 파랑)
        self.char_pr_list.append({
            'id': 5, 'font': 'Malgun Gothic', 'size': 900,
            'bold': False, 'color': '#2E86C1',
        })
        # CharPr 6: 문제 헤더 (맑은 고딕 10pt 흰색 굵게)
        self.char_pr_list.append({
            'id': 6, 'font': 'Malgun Gothic', 'size': 1000,
            'bold': True, 'color': '#FFFFFF',
        })
        # CharPr 7: 문제 본문 (맑은 고딕 10pt 어두운색)
        self.char_pr_list.append({
            'id': 7, 'font': 'Malgun Gothic', 'size': 1000,
            'bold': False, 'color': '#2C3E50',
        })
        # CharPr 8: 서술조건 (맑은 고딕 8pt 회색)
        self.char_pr_list.append({
            'id': 8, 'font': 'Malgun Gothic', 'size': 800,
            'bold': False, 'color': '#7F8C8D',
        })
        # CharPr 9: 풀이 레이블 (맑은 고딕 8pt 회색)
        self.char_pr_list.append({
            'id': 9, 'font': 'Malgun Gothic', 'size': 800,
            'bold': False, 'color': '#7F8C8D',
        })
        # CharPr 10: 답안란 공백 (맑은 고딕 10pt)
        self.char_pr_list.append({
            'id': 10, 'font': 'Malgun Gothic', 'size': 1000,
            'bold': False, 'color': '#000000',
        })
        # CharPr 11: 아주 작은 (4pt)
        self.char_pr_list.append({
            'id': 11, 'font': 'Malgun Gothic', 'size': 400,
            'bold': False, 'color': '#000000',
        })
        # CharPr 12: 작은 (8pt)
        self.char_pr_list.append({
            'id': 12, 'font': 'Malgun Gothic', 'size': 800,
            'bold': False, 'color': '#000000',
        })
        # CharPr 13: 채점기준표 제목 (12pt 진한색 굵게)
        self.char_pr_list.append({
            'id': 13, 'font': 'Malgun Gothic', 'size': 1200,
            'bold': True, 'color': '#2C3E50',
        })
        # CharPr 14: 채점기준표 제목 배지 (11pt 흰색 굵게)
        self.char_pr_list.append({
            'id': 14, 'font': 'Malgun Gothic', 'size': 1100,
            'bold': True, 'color': '#FFFFFF',
        })
        # CharPr 15: 채점기준표 헤더 (8pt 흰색 굵게)
        self.char_pr_list.append({
            'id': 15, 'font': 'Malgun Gothic', 'size': 800,
            'bold': True, 'color': '#FFFFFF',
        })
        # CharPr 16: 채점기준표 행제목 (7.5pt 진한색 굵게)
        self.char_pr_list.append({
            'id': 16, 'font': 'Malgun Gothic', 'size': 750,
            'bold': True, 'color': '#2C3E50',
        })
        # CharPr 17: 채점기준표 본문 (7.5pt 진한색)
        self.char_pr_list.append({
            'id': 17, 'font': 'Malgun Gothic', 'size': 750,
            'bold': False, 'color': '#2C3E50',
        })
        # CharPr 18: 큰 공백 (14pt)
        self.char_pr_list.append({
            'id': 18, 'font': 'Malgun Gothic', 'size': 1400,
            'bold': False, 'color': '#000000',
        })

        # ParaPr 0: 기본 (spacing 0)
        self.para_pr_list.append({
            'id': 0, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 0,
        })
        # ParaPr 1: 간격 200 after
        self.para_pr_list.append({
            'id': 1, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 200,
        })
        # ParaPr 2: 간격 60 after
        self.para_pr_list.append({
            'id': 2, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 60,
        })
        # ParaPr 3: 간격 40 after
        self.para_pr_list.append({
            'id': 3, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 40,
        })
        # ParaPr 4: 간격 20 after
        self.para_pr_list.append({
            'id': 4, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 20,
        })
        # ParaPr 5: 간격 80 after
        self.para_pr_list.append({
            'id': 5, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 80,
        })
        # ParaPr 6: 가운데 정렬
        self.para_pr_list.append({
            'id': 6, 'alignment': 'CENTER', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 0, 'spacing_after': 0,
        })
        # ParaPr 7: 채점기준표 제목 (간격 120 after, 280 before)
        self.para_pr_list.append({
            'id': 7, 'alignment': 'JUSTIFY', 'line_spacing_type': 'PERCENT',
            'line_spacing': 160, 'spacing_before': 280, 'spacing_after': 120,
        })

        # BorderFill 1: 기본 (테두리 없음)
        self.border_fill_list.append({
            'id': 1, 'borders': {s: {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': None,
        })
        # BorderFill 2: 빨간 배경 (E74C3C) 테두리 없음
        self.border_fill_list.append({
            'id': 2, 'borders': {s: {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': '#E74C3C',
        })
        # BorderFill 3: 연분홍 배경 (FDEDEC) 빨간 테두리
        self.border_fill_list.append({
            'id': 3, 'borders': {s: {'type': 'SOLID', 'width': '0.1 mm', 'color': '#E74C3C'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': '#FDEDEC',
        })
        # BorderFill 4: 진파랑 배경 (1A5276) 테두리 없음
        self.border_fill_list.append({
            'id': 4, 'borders': {s: {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': '#1A5276',
        })
        # BorderFill 5: 점선 하단 테두리
        self.border_fill_list.append({
            'id': 5, 'borders': {
                'left': {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'},
                'right': {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'},
                'top': {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'},
                'bottom': {'type': 'DASH', 'width': '0.12 mm', 'color': '#BDC3C7'},
            },
            'bg_color': None,
        })
        # BorderFill 6: 표 기본 테두리
        self.border_fill_list.append({
            'id': 6, 'borders': {s: {'type': 'SOLID', 'width': '0.1 mm', 'color': '#000000'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': None,
        })
        # BorderFill 7: 채점표 헤더 셀 (1A5276 배경, 얇은 회색 테두리)
        self.border_fill_list.append({
            'id': 7, 'borders': {s: {'type': 'SOLID', 'width': '0.1 mm', 'color': '#BDC3C7'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': '#1A5276',
        })
        # BorderFill 8: 채점표 행제목 셀 (EAF2F8 배경, 얇은 회색 테두리)
        self.border_fill_list.append({
            'id': 8, 'borders': {s: {'type': 'SOLID', 'width': '0.1 mm', 'color': '#BDC3C7'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': '#EAF2F8',
        })
        # BorderFill 9: 채점표 일반 셀 (흰색 배경, 얇은 회색 테두리)
        self.border_fill_list.append({
            'id': 9, 'borders': {s: {'type': 'SOLID', 'width': '0.1 mm', 'color': '#BDC3C7'} for s in ['left', 'right', 'top', 'bottom']},
            'bg_color': '#FFFFFF',
        })
        # BorderFill 10: 실선 하단 테두리 (파랑)
        self.border_fill_list.append({
            'id': 10, 'borders': {
                'left': {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'},
                'right': {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'},
                'top': {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'},
                'bottom': {'type': 'SOLID', 'width': '0.12 mm', 'color': '#2E86C1'},
            },
            'bg_color': None,
        })

        # Style 0: 기본
        self.style_list.append({
            'id': 0, 'name': 'Normal', 'type': 'PARA',
            'paraPrIDRef': 0, 'charPrIDRef': 0,
        })

    def _next_equation_id(self):
        eid = self.equation_id_counter
        self.equation_id_counter += 1
        return str(eid)

    def get_char_pr_for_run(self, run_data):
        """DOCX 런 데이터에 가장 적합한 charPrIDRef를 반환"""
        size = run_data.get('size', 20)
        color = run_data.get('color', '000000')
        bold = run_data.get('bold', False)

        if color:
            color = color.upper()

        # 매칭 시도
        for cpr in self.char_pr_list:
            cpr_size = cpr['size']
            cpr_color = cpr['color'].replace('#', '').upper()
            cpr_bold = cpr['bold']

            # 크기 비교 (DOCX는 반값, HWPX는 HWPUNIT: 10pt=1000)
            docx_hwp_size = (size * 100) // 2  # DOCX size/2 * 100

            if (abs(docx_hwp_size - cpr_size) <= 100
                    and cpr_color == color
                    and cpr_bold == bold):
                return cpr['id']

        # 매칭 실패 시 기본
        return 0

    # --------------------------------------------------------
    # section0.xml 생성
    # --------------------------------------------------------
    def build_section0(self, content_items):
        """section0.xml 루트 요소 생성"""
        sec = ET.Element(f'{HS}sec')

        # 첫 번째 단락에 secPr 포함
        first_p = True

        for item in content_items:
            if item['type'] == 'paragraph':
                p = self._build_paragraph(item, include_sec_pr=first_p)
                sec.append(p)
                first_p = False
            elif item['type'] == 'table':
                # 테이블 앞에 빈 단락이 필요할 수 있음
                if first_p:
                    # secPr이 포함된 빈 단락 + 테이블
                    p = self._build_empty_paragraph(include_sec_pr=True)
                    sec.append(p)
                    first_p = False
                tbl_p = self._build_table_paragraph(item)
                sec.append(tbl_p)

        return sec

    def _build_empty_paragraph(self, include_sec_pr=False, char_pr_id=0, para_pr_id=0):
        """빈 단락 생성"""
        p = ET.SubElement(ET.Element('dummy'), f'{HP}p')
        p = ET.Element(f'{HP}p')
        p.set('paraPrIDRef', str(para_pr_id))
        p.set('styleIDRef', '0')
        p.set('pageBreak', '0')
        p.set('columnBreak', '0')
        p.set('merged', '0')

        if include_sec_pr:
            run = ET.SubElement(p, f'{HP}run')
            run.set('charPrIDRef', str(char_pr_id))
            self._add_sec_pr(run)

            ctrl_run = ET.SubElement(p, f'{HP}run')
            ctrl_run.set('charPrIDRef', str(char_pr_id))
            ctrl = ET.SubElement(ctrl_run, f'{HP}ctrl')
            col_pr = ET.SubElement(ctrl, f'{HP}colPr')
            col_pr.set('id', '')
            col_pr.set('type', 'NEWSPAPER')
            col_pr.set('layout', 'LEFT')
            col_pr.set('colCount', '1')
            col_pr.set('sameSz', '1')
            col_pr.set('sameGap', '0')

        run = ET.SubElement(p, f'{HP}run')
        run.set('charPrIDRef', str(char_pr_id))
        t = ET.SubElement(run, f'{HP}t')
        t.text = ''

        self._add_linesegarray(p)
        return p

    def _add_sec_pr(self, run):
        """섹션 속성 추가"""
        sec_pr = ET.SubElement(run, f'{HP}secPr')
        sec_pr.set('textDirection', 'HORIZONTAL')
        sec_pr.set('spaceColumns', '1134')
        sec_pr.set('tabStop', '8000')
        sec_pr.set('outlineShapeIDRef', '1')
        sec_pr.set('memoShapeIDRef', '0')
        sec_pr.set('textVerticalWidthHead', '0')
        sec_pr.set('masterPageCnt', '0')

        grid = ET.SubElement(sec_pr, f'{HP}grid')
        grid.set('lineGrid', '0')
        grid.set('charGrid', '0')
        grid.set('wonggojiFormat', '0')

        start_num = ET.SubElement(sec_pr, f'{HP}startNum')
        start_num.set('pageStartsOn', 'BOTH')
        start_num.set('page', '0')
        start_num.set('pic', '0')
        start_num.set('tbl', '0')
        start_num.set('equation', '0')

        visibility = ET.SubElement(sec_pr, f'{HP}visibility')
        visibility.set('hideFirstHeader', '0')
        visibility.set('hideFirstFooter', '0')
        visibility.set('hideFirstMasterPage', '0')
        visibility.set('border', 'SHOW_ALL')
        visibility.set('fill', 'SHOW_ALL')
        visibility.set('hideFirstPageNum', '0')
        visibility.set('hideFirstEmptyLine', '0')
        visibility.set('showLineNumber', '0')

        line_num = ET.SubElement(sec_pr, f'{HP}lineNumberShape')
        line_num.set('restartType', '0')
        line_num.set('countBy', '0')
        line_num.set('distance', '0')
        line_num.set('startNumber', '0')

        page_pr = ET.SubElement(sec_pr, f'{HP}pagePr')
        page_pr.set('landscape', 'WIDELY')
        page_pr.set('width', str(self.PAGE_WIDTH))
        page_pr.set('height', str(self.PAGE_HEIGHT))
        page_pr.set('gutterType', 'LEFT_ONLY')

        margin = ET.SubElement(page_pr, f'{HP}margin')
        margin.set('header', '4252')
        margin.set('footer', '4252')
        margin.set('gutter', '0')
        margin.set('left', str(self.MARGIN_LEFT))
        margin.set('right', str(self.MARGIN_RIGHT))
        margin.set('top', str(self.MARGIN_TOP))
        margin.set('bottom', str(self.MARGIN_BOTTOM))

        # footnote/endnote
        for note_name in ['footNotePr', 'endNotePr']:
            note = ET.SubElement(sec_pr, f'{HP}{note_name}')
            auto_num = ET.SubElement(note, f'{HP}autoNumFormat')
            auto_num.set('type', 'DIGIT')
            auto_num.set('userChar', '')
            auto_num.set('prefixChar', '')
            auto_num.set('suffixChar', ')')
            auto_num.set('supscript', '0')
            note_line = ET.SubElement(note, f'{HP}noteLine')
            note_line.set('length', '-1' if note_name == 'footNotePr' else '14692344')
            note_line.set('type', 'SOLID')
            note_line.set('width', '0.12 mm')
            note_line.set('color', '#000000')
            note_spacing = ET.SubElement(note, f'{HP}noteSpacing')
            note_spacing.set('betweenNotes', '283' if note_name == 'footNotePr' else '0')
            note_spacing.set('belowLine', '567')
            note_spacing.set('aboveLine', '850')
            numbering = ET.SubElement(note, f'{HP}numbering')
            numbering.set('type', 'CONTINUOUS')
            numbering.set('newNum', '1')
            placement = ET.SubElement(note, f'{HP}placement')
            placement.set('place', 'EACH_COLUMN' if note_name == 'footNotePr' else 'END_OF_DOCUMENT')
            placement.set('beneathText', '0')

        for border_type in ['BOTH', 'EVEN', 'ODD']:
            pbf = ET.SubElement(sec_pr, f'{HP}pageBorderFill')
            pbf.set('type', border_type)
            pbf.set('borderFillIDRef', '1')
            pbf.set('textBorder', 'PAPER')
            pbf.set('headerInside', '0')
            pbf.set('footerInside', '0')
            pbf.set('fillArea', 'PAPER')
            offset = ET.SubElement(pbf, f'{HP}offset')
            offset.set('left', '1417')
            offset.set('right', '1417')
            offset.set('top', '1417')
            offset.set('bottom', '1417')

    def _add_linesegarray(self, p):
        """linesegarray 추가"""
        lsa = ET.SubElement(p, f'{HP}linesegarray')
        ls = ET.SubElement(lsa, f'{HP}lineseg')
        ls.set('textpos', '0')
        ls.set('vertpos', '0')
        ls.set('vertsize', '1000')
        ls.set('textheight', '1000')
        ls.set('baseline', '850')
        ls.set('spacing', '600')
        ls.set('horzpos', '0')
        ls.set('horzsize', str(self.CONTENT_WIDTH))
        ls.set('flags', '393216')

    def _build_paragraph(self, para_data, include_sec_pr=False):
        """단락 생성"""
        # 페이지 브레이크
        if para_data.get('has_page_break'):
            p = ET.Element(f'{HP}p')
            p.set('paraPrIDRef', '0')
            p.set('styleIDRef', '0')
            p.set('pageBreak', '1')
            p.set('columnBreak', '0')
            p.set('merged', '0')
            run = ET.SubElement(p, f'{HP}run')
            run.set('charPrIDRef', '0')
            t = ET.SubElement(run, f'{HP}t')
            t.text = ''
            self._add_linesegarray(p)
            return p

        # 적절한 ParaPrIDRef 결정
        para_pr_id = 0
        spacing_after = para_data.get('spacing_after')
        spacing_before = para_data.get('spacing_before')

        if spacing_after == '200':
            para_pr_id = 1
        elif spacing_after == '60':
            para_pr_id = 2
        elif spacing_after == '40':
            para_pr_id = 3
        elif spacing_after == '20':
            para_pr_id = 4
        elif spacing_after == '80':
            para_pr_id = 5
        elif spacing_after == '30':
            para_pr_id = 3  # 30에 가장 가까운 것

        if para_data.get('alignment') == 'center':
            para_pr_id = 6

        if spacing_before and int(spacing_before) >= 200:
            para_pr_id = 7

        p = ET.Element(f'{HP}p')
        p.set('paraPrIDRef', str(para_pr_id))
        p.set('styleIDRef', '0')
        p.set('pageBreak', '0')
        p.set('columnBreak', '0')
        p.set('merged', '0')

        if include_sec_pr:
            run0 = ET.SubElement(p, f'{HP}run')
            run0.set('charPrIDRef', '0')
            self._add_sec_pr(run0)

            ctrl_run = ET.SubElement(p, f'{HP}run')
            ctrl_run.set('charPrIDRef', '0')
            ctrl = ET.SubElement(ctrl_run, f'{HP}ctrl')
            col_pr = ET.SubElement(ctrl, f'{HP}colPr')
            col_pr.set('id', '')
            col_pr.set('type', 'NEWSPAPER')
            col_pr.set('layout', 'LEFT')
            col_pr.set('colCount', '1')
            col_pr.set('sameSz', '1')
            col_pr.set('sameGap', '0')

        # 점선 하단 테두리인 경우: 답안란 줄
        if para_data.get('has_dotted_border'):
            run = ET.SubElement(p, f'{HP}run')
            run.set('charPrIDRef', '10')
            t = ET.SubElement(run, f'{HP}t')
            t.text = ' '

            # 단락에 borderFillIDRef 적용은 ParaPr에서 설정해야 하지만
            # 간소화를 위해 단락 속성을 직접 사용
            p.set('paraPrIDRef', '0')
            # 단락 테두리는 ParaPr의 border에서 설정하는데
            # 현재 구조에서는 직접 처리하기 어려우므로
            # 밑줄 문자로 대체 (길이 맞춤)
            # 실제로는 점선 표현을 위해 별도 처리 필요
            # HWPX에서는 ParaPr의 border 속성으로 설정

            self._add_linesegarray(p)
            return p

        # 실선 하단 테두리 (채점기준표 제목)
        if para_data.get('has_single_border'):
            # 채점기준표 제목 처리
            pass

        # 런이 없는 빈 단락
        if not para_data.get('runs'):
            run = ET.SubElement(p, f'{HP}run')
            run.set('charPrIDRef', '0')
            t = ET.SubElement(run, f'{HP}t')
            t.text = ''
            self._add_linesegarray(p)
            return p

        # 런 처리
        for run_data in para_data['runs']:
            text = run_data['text']
            char_pr_id = self.get_char_pr_for_run(run_data)

            # 수식 포함 여부 확인
            if has_math_chars(text):
                segments = split_text_and_math(text)
                for seg_type, seg_text in segments:
                    if seg_type == 'math':
                        # 수식을 hp:equation으로 변환
                        eq_script = unicode_to_hwp_equation(seg_text)
                        self._add_equation_run(p, eq_script, char_pr_id)
                    else:
                        if seg_text:
                            run = ET.SubElement(p, f'{HP}run')
                            run.set('charPrIDRef', str(char_pr_id))
                            t = ET.SubElement(run, f'{HP}t')
                            t.text = seg_text
            else:
                run = ET.SubElement(p, f'{HP}run')
                run.set('charPrIDRef', str(char_pr_id))
                t = ET.SubElement(run, f'{HP}t')
                t.text = text

        self._add_linesegarray(p)
        return p

    @staticmethod
    def _estimate_equation_size(script):
        """수식 스크립트 내용 기반으로 width/height 추정 (HWPUNIT).

        HWP 수식 폰트(HYhwpEQ) 기준:
        - 일반 문자/숫자: ~250 units
        - sqrt 기호: ~400 units (근호 그리기)
        - over (분수): height 증가, width는 분자/분모 중 긴 쪽
        - ^{} (위첨자): width ~150 (작은 글꼴)
        - LEFT/RIGHT 구분자: ~150
        """
        # 렌더링에 영향을 주는 실제 문자 수 추정
        s = script
        width_units = 0
        has_sqrt = 'sqrt' in s
        has_over = 'over' in s
        has_superscript = '^{' in s

        # sqrt, over, LEFT, RIGHT 등 키워드를 제거하고 실제 글자 수 세기
        display = s
        for kw in ['sqrt', 'over', 'LEFT', 'RIGHT']:
            display = display.replace(kw, '')
        # 중괄호, 공백 제거
        display = display.replace('{', '').replace('}', '').replace(' ', '')

        # 실제 렌더링 글자 수
        char_count = len(display)

        # 기본 너비: 글자당 ~280 units
        width_units = char_count * 280

        # sqrt 기호 추가 너비
        if has_sqrt:
            sqrt_count = s.count('sqrt')
            width_units += sqrt_count * 350

        # 위첨자는 작게 렌더링되므로 약간 줄임
        if has_superscript:
            sup_count = s.count('^{')
            width_units -= sup_count * 80  # 위첨자 글자는 작아서 보정

        # 최소/최대 제한
        width_units = max(800, min(width_units, 20000))

        # 높이 추정
        height = 1000  # 기본
        if has_sqrt:
            height = max(height, 1200)
        if has_over:
            height = max(height, 1600)
        if has_superscript:
            height = max(height, 1100)

        return width_units, height

    def _add_equation_run(self, parent, script, char_pr_id=0):
        """수식 런 추가"""
        run = ET.SubElement(parent, f'{HP}run')
        run.set('charPrIDRef', str(char_pr_id))

        eq = ET.SubElement(run, f'{HP}equation')
        eq.set('id', self._next_equation_id())
        eq.set('zOrder', '0')
        eq.set('numberingType', 'EQUATION')
        eq.set('textWrap', 'TOP_AND_BOTTOM')
        eq.set('textFlow', 'BOTH_SIDES')
        eq.set('lock', '0')
        eq.set('dropcapstyle', 'None')
        eq.set('version', 'Equation Version 60')
        eq.set('baseLine', '85')
        eq.set('textColor', '#000000')
        eq.set('baseUnit', '1000')
        eq.set('lineMode', 'CHAR')
        eq.set('font', 'HYhwpEQ')

        est_w, est_h = self._estimate_equation_size(script)

        sz = ET.SubElement(eq, f'{HP}sz')
        sz.set('width', str(est_w))
        sz.set('widthRelTo', 'ABSOLUTE')
        sz.set('height', str(est_h))
        sz.set('heightRelTo', 'ABSOLUTE')
        sz.set('protect', '0')

        pos = ET.SubElement(eq, f'{HP}pos')
        pos.set('treatAsChar', '1')
        pos.set('affectLSpacing', '0')
        pos.set('flowWithText', '1')
        pos.set('allowOverlap', '0')
        pos.set('holdAnchorAndSO', '0')
        pos.set('vertRelTo', 'PARA')
        pos.set('horzRelTo', 'PARA')
        pos.set('vertAlign', 'TOP')
        pos.set('horzAlign', 'LEFT')
        pos.set('vertOffset', '0')
        pos.set('horzOffset', '0')

        out_margin = ET.SubElement(eq, f'{HP}outMargin')
        out_margin.set('left', '56')
        out_margin.set('right', '56')
        out_margin.set('top', '0')
        out_margin.set('bottom', '0')

        script_el = ET.SubElement(eq, f'{HP}script')
        script_el.text = script

    def _build_table_paragraph(self, table_data):
        """테이블을 포함하는 단락 생성"""
        p = ET.Element(f'{HP}p')
        p.set('paraPrIDRef', '0')
        p.set('styleIDRef', '0')
        p.set('pageBreak', '0')
        p.set('columnBreak', '0')
        p.set('merged', '0')

        run = ET.SubElement(p, f'{HP}run')
        run.set('charPrIDRef', '0')

        rows = table_data['rows']
        row_cnt = len(rows)
        col_cnt = max(len(row) for row in rows) if rows else 1
        col_widths = table_data.get('col_widths', [])

        # 열 너비를 HWPX 단위로 변환 (DXA -> HWPUNIT: 1 dxa = ~5 hwpunit)
        # 전체 콘텐츠 너비에 맞춤
        if col_widths:
            total_dxa = sum(col_widths)
            if total_dxa > 0:
                hwp_widths = [int(w / total_dxa * self.CONTENT_WIDTH) for w in col_widths]
            else:
                hwp_widths = [self.CONTENT_WIDTH // col_cnt] * col_cnt
        else:
            hwp_widths = [self.CONTENT_WIDTH // col_cnt] * col_cnt

        # 너비 합계 보정
        diff = self.CONTENT_WIDTH - sum(hwp_widths)
        if hwp_widths:
            hwp_widths[-1] += diff

        # 테이블에 적합한 BorderFill 결정
        # 첫 번째 셀의 배경색으로 판단
        first_cell = rows[0][0] if rows and rows[0] else None
        if first_cell:
            bg = (first_cell.get('bg_color') or '').upper()
            has_border = any(
                first_cell.get('borders', {}).get(s, {}).get('val', 'none') != 'none'
                for s in ['top', 'left', 'bottom', 'right']
            )
        else:
            bg = ''
            has_border = False

        tbl_border_fill = '6'  # 기본 테두리

        tbl = ET.SubElement(run, f'{HP}tbl')
        tbl.set('rowCnt', str(row_cnt))
        tbl.set('colCnt', str(col_cnt))
        tbl.set('borderFillIDRef', tbl_border_fill)
        tbl.set('cellSpacing', '0')
        tbl.set('pageBreak', 'CELL')
        tbl.set('repeatHeader', '0')

        row_height = 1500  # 기본 행 높이

        sz = ET.SubElement(tbl, f'{HP}sz')
        sz.set('width', str(self.CONTENT_WIDTH))
        sz.set('widthRelTo', 'ABSOLUTE')
        sz.set('height', str(row_height * row_cnt))
        sz.set('heightRelTo', 'ABSOLUTE')
        sz.set('protect', '0')

        pos = ET.SubElement(tbl, f'{HP}pos')
        pos.set('treatAsChar', '1')
        pos.set('affectLSpacing', '0')
        pos.set('flowWithText', '1')
        pos.set('allowOverlap', '0')
        pos.set('holdAnchorAndSO', '0')
        pos.set('vertRelTo', 'PARA')
        pos.set('horzRelTo', 'PARA')
        pos.set('vertAlign', 'TOP')
        pos.set('horzAlign', 'LEFT')
        pos.set('vertOffset', '0')
        pos.set('horzOffset', '0')

        out_margin = ET.SubElement(tbl, f'{HP}outMargin')
        out_margin.set('left', '283')
        out_margin.set('right', '283')
        out_margin.set('top', '0')
        out_margin.set('bottom', '0')

        in_margin = ET.SubElement(tbl, f'{HP}inMargin')
        in_margin.set('left', '510')
        in_margin.set('right', '510')
        in_margin.set('top', '141')
        in_margin.set('bottom', '141')

        # 행 생성
        for row_idx, row in enumerate(rows):
            tr = ET.SubElement(tbl, f'{HP}tr')

            for col_idx, cell in enumerate(row):
                tc = ET.SubElement(tr, f'{HP}tc')

                # 셀 BorderFill 결정
                cell_bg = (cell.get('bg_color') or '').upper()
                cell_borders = cell.get('borders', {})

                cell_bf_id = self._get_cell_border_fill_id(cell_bg, cell_borders)
                tc.set('borderFillIDRef', str(cell_bf_id))

                # 셀 콘텐츠
                sub_list = ET.SubElement(tc, f'{HP}subList')
                valign = cell.get('valign', 'top')
                if valign == 'center':
                    sub_list.set('vertAlign', 'CENTER')
                else:
                    sub_list.set('vertAlign', 'TOP')
                sub_list.set('textDirection', 'HORIZONTAL')
                sub_list.set('linkListIDRef', '0')
                sub_list.set('linkListNextIDRef', '0')
                cell_w = hwp_widths[col_idx] if col_idx < len(hwp_widths) else hwp_widths[-1]
                sub_list.set('textWidth', str(cell_w - 1020))
                sub_list.set('textHeight', '0')

                # 셀 내 단락들
                for para in cell.get('paragraphs', []):
                    cell_p = ET.SubElement(sub_list, f'{HP}p')

                    # 정렬
                    alignment = para.get('alignment', '')
                    if alignment == 'center':
                        cell_p.set('paraPrIDRef', '6')
                    else:
                        # spacing
                        sa = para.get('spacing_after', '0')
                        if sa == '80':
                            cell_p.set('paraPrIDRef', '5')
                        elif sa == '30':
                            cell_p.set('paraPrIDRef', '3')
                        else:
                            cell_p.set('paraPrIDRef', '0')

                    cell_p.set('styleIDRef', '0')

                    if not para.get('runs'):
                        cell_run = ET.SubElement(cell_p, f'{HP}run')
                        cell_run.set('charPrIDRef', '0')
                        cell_t = ET.SubElement(cell_run, f'{HP}t')
                        cell_t.text = ''
                    else:
                        for run_data in para['runs']:
                            text = run_data['text']
                            cpr_id = self.get_char_pr_for_run(run_data)
                            # 수식 포함 여부 확인 (표 셀 내부도 동일 처리)
                            if has_math_chars(text):
                                segments = split_text_and_math(text)
                                for seg_type, seg_text in segments:
                                    if seg_type == 'math':
                                        eq_script = unicode_to_hwp_equation(seg_text)
                                        self._add_equation_run(cell_p, eq_script, cpr_id)
                                    else:
                                        if seg_text:
                                            cell_run = ET.SubElement(cell_p, f'{HP}run')
                                            cell_run.set('charPrIDRef', str(cpr_id))
                                            cell_t = ET.SubElement(cell_run, f'{HP}t')
                                            cell_t.text = seg_text
                            else:
                                cell_run = ET.SubElement(cell_p, f'{HP}run')
                                cell_run.set('charPrIDRef', str(cpr_id))
                                cell_t = ET.SubElement(cell_run, f'{HP}t')
                                cell_t.text = text

                    # linesegarray
                    lsa = ET.SubElement(cell_p, f'{HP}linesegarray')
                    ls = ET.SubElement(lsa, f'{HP}lineseg')
                    ls.set('textpos', '0')
                    ls.set('vertpos', '0')
                    ls.set('vertsize', '1000')
                    ls.set('textheight', '1000')
                    ls.set('baseline', '850')
                    ls.set('spacing', '600')
                    ls.set('horzpos', '0')
                    ls.set('horzsize', str(cell_w - 1020))
                    ls.set('flags', '393216')

                # 셀 주소/범위/크기/마진
                cell_addr = ET.SubElement(tc, f'{HP}cellAddr')
                cell_addr.set('colAddr', str(col_idx))
                cell_addr.set('rowAddr', str(row_idx))

                cell_span = ET.SubElement(tc, f'{HP}cellSpan')
                cell_span.set('colSpan', '1')
                cell_span.set('rowSpan', '1')

                cell_sz = ET.SubElement(tc, f'{HP}cellSz')
                cell_sz.set('width', str(cell_w))
                cell_sz.set('height', str(row_height))

                cell_margin = ET.SubElement(tc, f'{HP}cellMargin')
                cell_margin.set('left', '510')
                cell_margin.set('right', '510')
                cell_margin.set('top', '141')
                cell_margin.set('bottom', '141')

        # 테이블 뒤에 텍스트 런 필요
        run2 = ET.SubElement(p, f'{HP}run')
        run2.set('charPrIDRef', '0')
        t2 = ET.SubElement(run2, f'{HP}t')
        t2.text = ''

        self._add_linesegarray(p)
        return p

    def _get_cell_border_fill_id(self, bg_color, borders):
        """셀 배경색과 테두리로 적합한 BorderFill ID 반환"""
        bg = bg_color.replace('#', '').upper() if bg_color else ''

        if bg == 'E74C3C':
            return 2  # 빨간 배경
        elif bg == 'FDEDEC':
            return 3  # 연분홍 배경
        elif bg == '1A5276':
            return 4  # 진파랑 배경
        elif bg == 'EAF2F8':
            return 8  # 연파랑 배경 (채점표 행제목)
        elif bg == 'FFFFFF' or bg == '':
            # 테두리 유무로 구분
            has_border = any(
                borders.get(s, {}).get('val', 'none') not in ('none', '')
                for s in ['top', 'left', 'bottom', 'right']
            )
            if has_border:
                return 9  # 흰색 배경 + 테두리
            return 1  # 기본 (테두리 없음)
        else:
            return 1

    # --------------------------------------------------------
    # header.xml 생성
    # --------------------------------------------------------
    def build_header(self, template_header_bytes):
        """header.xml을 템플릿 기반으로 수정하여 반환"""
        root = ET.fromstring(template_header_bytes)

        # refList 찾기
        ref_list = root.find(f'{HH}refList')
        if ref_list is None:
            print("WARNING: refList not found in header.xml")
            return ET.tostring(root, encoding='unicode', xml_declaration=True)

        # ---- CharProperties 추가/수정 ----
        char_props = ref_list.find(f'{HH}charProperties')
        if char_props is None:
            char_props = ET.SubElement(ref_list, f'{HH}charProperties')

        # 기존 항목 제거
        for child in list(char_props):
            char_props.remove(child)

        char_props.set('itemCnt', str(len(self.char_pr_list)))

        for cpr in self.char_pr_list:
            cp = ET.SubElement(char_props, f'{HH}charPr')
            cp.set('id', str(cpr['id']))
            cp.set('height', str(cpr['size']))
            cp.set('textColor', cpr['color'])
            cp.set('shadeColor', 'none')
            cp.set('useFontSpace', '0')
            cp.set('useKerning', '0')
            cp.set('symMark', 'NONE')
            cp.set('borderFillIDRef', '1')

            if cpr['bold']:
                cp.set('bold', '1')
            else:
                cp.set('bold', '0')
            cp.set('italic', '0')
            cp.set('underline', 'NONE')
            cp.set('strikeout', 'NONE')
            cp.set('charShadow', 'NONE')
            cp.set('supscript', 'NONE')

            # 글꼴 참조 (모든 언어에 동일한 글꼴)
            font_ref = ET.SubElement(cp, f'{HH}fontRef')
            for lang in ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']:
                font_ref.set(lang, '0')  # fontface id=0

            # 비율/간격
            ratio = ET.SubElement(cp, f'{HH}ratio')
            for lang in ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']:
                ratio.set(lang, '100')

            char_spacing = ET.SubElement(cp, f'{HH}spacing')
            for lang in ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']:
                char_spacing.set(lang, '0')

            rel_size = ET.SubElement(cp, f'{HH}relSz')
            for lang in ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']:
                rel_size.set(lang, '100')

            char_offset = ET.SubElement(cp, f'{HH}offset')
            for lang in ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']:
                char_offset.set(lang, '0')

        # ---- BorderFills 추가/수정 ----
        border_fills = ref_list.find(f'{HH}borderFills')
        if border_fills is None:
            border_fills = ET.SubElement(ref_list, f'{HH}borderFills')

        # 기존 항목 제거
        for child in list(border_fills):
            border_fills.remove(child)

        border_fills.set('itemCnt', str(len(self.border_fill_list)))

        for bf_data in self.border_fill_list:
            bf = ET.SubElement(border_fills, f'{HH}borderFill')
            bf.set('id', str(bf_data['id']))
            bf.set('threeD', '0')
            bf.set('shadow', '0')
            bf.set('centerLine', 'NONE')
            bf.set('breakCellSeparateLine', '0')

            slash = ET.SubElement(bf, f'{HH}slash')
            slash.set('type', 'NONE')
            slash.set('Crooked', '0')
            slash.set('isCounter', '0')

            back_slash = ET.SubElement(bf, f'{HH}backSlash')
            back_slash.set('type', 'NONE')
            back_slash.set('Crooked', '0')
            back_slash.set('isCounter', '0')

            for side in ['left', 'right', 'top', 'bottom']:
                border = ET.SubElement(bf, f'{HH}{side}Border')
                bdata = bf_data['borders'].get(side, {})
                border.set('type', bdata.get('type', 'NONE'))
                border.set('width', bdata.get('width', '0.1 mm'))
                border.set('color', bdata.get('color', '#000000'))

            diag = ET.SubElement(bf, f'{HH}diagonal')
            diag.set('type', 'SOLID')
            diag.set('width', '0.1 mm')
            diag.set('color', '#000000')

            if bf_data.get('bg_color'):
                fill_brush = ET.SubElement(bf, f'{HH}fillBrush')
                win_brush = ET.SubElement(fill_brush, f'{HH}winBrush')
                win_brush.set('faceColor', bf_data['bg_color'])
                win_brush.set('hatchColor', '#000000')
                win_brush.set('alpha', '0')

        # ---- ParaProperties 추가/수정 ----
        para_props = ref_list.find(f'{HH}paraProperties')
        if para_props is None:
            para_props = ET.SubElement(ref_list, f'{HH}paraProperties')

        for child in list(para_props):
            para_props.remove(child)

        para_props.set('itemCnt', str(len(self.para_pr_list)))

        for ppr in self.para_pr_list:
            pp = ET.SubElement(para_props, f'{HH}paraPr')
            pp.set('id', str(ppr['id']))
            pp.set('tabPrIDRef', '0')
            pp.set('condense', '0')
            pp.set('fontLineHeight', '0')
            pp.set('snapToGrid', '1')
            pp.set('suppressLineNumbers', '0')
            pp.set('checked', '0')

            align = ET.SubElement(pp, f'{HH}align')
            align.set('horizontal', ppr.get('alignment', 'JUSTIFY'))
            align.set('vertical', 'BASELINE')

            heading = ET.SubElement(pp, f'{HH}heading')
            heading.set('type', 'NONE')
            heading.set('idRef', '0')
            heading.set('level', '0')

            margin_pp = ET.SubElement(pp, f'{HH}margin')
            margin_pp.set('indent', '0')
            margin_pp.set('left', '0')
            margin_pp.set('right', '0')
            margin_pp.set('prev', str(ppr.get('spacing_before', 0)))
            margin_pp.set('next', str(ppr.get('spacing_after', 0)))

            line_spacing = ET.SubElement(pp, f'{HH}lineSpacing')
            line_spacing.set('type', ppr.get('line_spacing_type', 'PERCENT'))
            line_spacing.set('value', str(ppr.get('line_spacing', 160)))
            line_spacing.set('unit', 'HWPUNIT')

            border = ET.SubElement(pp, f'{HH}border')
            border.set('borderFillIDRef', '1')
            border.set('offsetLeft', '0')
            border.set('offsetRight', '0')
            border.set('offsetTop', '0')
            border.set('offsetBottom', '0')
            border.set('connect', '0')
            border.set('ignoreMargin', '0')

            auto_spacing = ET.SubElement(pp, f'{HH}autoSpacing')
            auto_spacing.set('eAsianEng', '0')
            auto_spacing.set('eAsianNum', '0')

        # ---- Styles 추가/수정 ----
        styles = ref_list.find(f'{HH}styles')
        if styles is None:
            styles = ET.SubElement(ref_list, f'{HH}styles')

        for child in list(styles):
            styles.remove(child)

        styles.set('itemCnt', str(len(self.style_list)))

        for sdata in self.style_list:
            style = ET.SubElement(styles, f'{HH}style')
            style.set('id', str(sdata['id']))
            style.set('type', sdata.get('type', 'PARA'))
            style.set('name', sdata.get('name', 'Normal'))
            style.set('engName', sdata.get('name', 'Normal'))
            style.set('paraPrIDRef', str(sdata.get('paraPrIDRef', 0)))
            style.set('charPrIDRef', str(sdata.get('charPrIDRef', 0)))
            style.set('nextStyleIDRef', str(sdata.get('id', 0)))
            style.set('langIDRef', '0')
            style.set('lockForm', '0')

        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # --------------------------------------------------------
    # HWPX 패키징
    # --------------------------------------------------------
    def package_hwpx(self, output_path, section0_xml, header_xml, template_bytes):
        """HWPX 파일로 패키징"""
        # 템플릿에서 기본 파일들 추출
        template_zip = zipfile.ZipFile(io.BytesIO(template_bytes))
        template_files = {}
        for name in template_zip.namelist():
            template_files[name] = template_zip.read(name)
        template_zip.close()

        # 출력 ZIP 작성
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. mimetype (무압축, 첫 엔트리)
            zf.writestr(
                zipfile.ZipInfo('mimetype', date_time=(2026, 3, 13, 0, 0, 0)),
                template_files.get('mimetype', 'application/hwp+zip'),
                compress_type=zipfile.ZIP_STORED
            )

            # 2. version.xml
            zf.writestr('version.xml', template_files.get('version.xml', b''))

            # 3. Contents/header.xml
            header_bytes = header_xml.encode('utf-8')
            zf.writestr('Contents/header.xml', header_bytes)

            # 4. Contents/section0.xml
            section0_bytes = section0_xml.encode('utf-8')
            zf.writestr('Contents/section0.xml', section0_bytes)

            # 5. 기타 파일들
            for name, data in template_files.items():
                if name not in ('mimetype', 'version.xml', 'Contents/header.xml', 'Contents/section0.xml'):
                    zf.writestr(name, data)

        # 파일로 저장
        with open(output_path, 'wb') as f:
            f.write(buf.getvalue())


# ============================================================
# 메인 변환 로직
# ============================================================

def convert_docx_to_hwpx(docx_path, hwpx_path):
    """DOCX를 HWPX로 변환"""
    print(f"[1/5] DOCX parsing: {os.path.basename(docx_path)}")
    content_items = parse_docx(docx_path)
    print(f"  - {len(content_items)} items parsed")

    # 콘텐츠 요약 출력
    tables = sum(1 for item in content_items if item['type'] == 'table')
    paras = sum(1 for item in content_items if item['type'] == 'paragraph')
    math_paras = 0
    for item in content_items:
        if item['type'] == 'paragraph':
            for run in item.get('runs', []):
                if has_math_chars(run['text']):
                    math_paras += 1
                    break
    print(f"  - tables: {tables}, paragraphs: {paras}, math paragraphs: {math_paras}")

    print(f"[2/5] Building HWPX structure...")
    builder = HwpxBuilder()

    # section0.xml 생성
    sec_root = builder.build_section0(content_items)
    section0_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + ET.tostring(sec_root, encoding='unicode')

    print(f"[3/5] Creating template...")
    # 빈 HWPX 템플릿 생성
    from hwpx.document import blank_document_bytes
    template_bytes = blank_document_bytes()

    # header.xml 수정
    with zipfile.ZipFile(io.BytesIO(template_bytes)) as z:
        header_bytes = z.read('Contents/header.xml')
    header_xml = builder.build_header(header_bytes)

    print(f"[4/5] Packaging HWPX...")
    builder.package_hwpx(hwpx_path, section0_xml, header_xml, template_bytes)

    print(f"[5/5] Verifying...")
    # 검증
    verify_hwpx(hwpx_path)

    print(f"\nDone! Output: {hwpx_path}")
    print(f"  File size: {os.path.getsize(hwpx_path)} bytes")


def verify_hwpx(hwpx_path):
    """HWPX 파일 검증"""
    with zipfile.ZipFile(hwpx_path) as z:
        names = z.namelist()

        # mimetype 확인
        if names[0] != 'mimetype':
            print("  WARNING: mimetype is not the first entry!")
        else:
            info = z.getinfo('mimetype')
            if info.compress_type != zipfile.ZIP_STORED:
                print("  WARNING: mimetype is compressed!")
            else:
                print("  OK: mimetype is first entry, STORED")

        # section0.xml 확인
        if 'Contents/section0.xml' in names:
            section0_data = z.read('Contents/section0.xml').decode('utf-8')
            eq_count = section0_data.count('hp:equation')
            script_count = section0_data.count('hp:script')
            print(f"  OK: section0.xml found ({len(section0_data)} bytes)")
            print(f"  Equations: {eq_count // 2} (hp:equation tags: {eq_count}, hp:script tags: {script_count})")

            # 수식 스크립트 내용 출력
            import re as _re
            scripts = _re.findall(r'<hp:script>(.*?)</hp:script>', section0_data)
            for i, s in enumerate(scripts):
                print(f"    eq[{i}]: {s}")
        else:
            print("  ERROR: section0.xml not found!")

        # header.xml 확인
        if 'Contents/header.xml' in names:
            header_data = z.read('Contents/header.xml').decode('utf-8')
            print(f"  OK: header.xml found ({len(header_data)} bytes)")
        else:
            print("  ERROR: header.xml not found!")


# ============================================================
# 엔트리 포인트
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_docx_to_hwpx.py <input.docx> [output.hwpx]")
        print()
        print("DOCX to HWPX converter with math equation support.")
        print("Converts Unicode math (sqrt, superscripts, abs) to HWP equation editor format.")
        sys.exit(1)

    docx_file = os.path.abspath(sys.argv[1])
    if len(sys.argv) >= 3:
        hwpx_file = os.path.abspath(sys.argv[2])
    else:
        hwpx_file = os.path.splitext(docx_file)[0] + '.hwpx'

    if not os.path.exists(docx_file):
        print(f"ERROR: Input file not found: {docx_file}")
        sys.exit(1)

    # Backup existing output
    if os.path.exists(hwpx_file):
        backup = hwpx_file + '.backup'
        import shutil
        shutil.copy2(hwpx_file, backup)
        print(f"Backup: {backup}")

    convert_docx_to_hwpx(docx_file, hwpx_file)
