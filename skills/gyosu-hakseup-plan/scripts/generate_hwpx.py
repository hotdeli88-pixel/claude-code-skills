# -*- coding: utf-8 -*-
"""
교수학습 및 평가 운영 계획 HWPX 생성 스크립트

JSON 데이터를 받아 배포용 HWPX 템플릿에 교과 데이터를 삽입하여
완성된 교수학습-평가 운영 계획 HWPX 파일을 생성한다.

Usage:
    python generate_hwpx.py --data curriculum.json --output result.hwpx
    python generate_hwpx.py --data curriculum.json --template custom.hwpx --output result.hwpx
"""
import sys
import io
import os
import json
import copy
import zipfile
import random
import argparse
import subprocess
from lxml import etree

# Windows 콘솔 인코딩
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# ============================================================
# HWPX 네임스페이스
# ============================================================
NS_MAP = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
    'ha': 'http://www.hancom.co.kr/hwpml/2011/app',
    'hp10': 'http://www.hancom.co.kr/hwpml/2016/paragraph',
    'hhs': 'http://www.hancom.co.kr/hwpml/2011/history',
    'hm': 'http://www.hancom.co.kr/hwpml/2011/master-page',
    'hpf': 'http://www.hancom.co.kr/schema/2011/hpf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'opf': 'http://www.idpf.org/2007/opf/',
    'ooxmlchart': 'http://www.hancom.co.kr/hwpml/2016/ooxmlchart',
    'hwpunitchar': 'http://www.hancom.co.kr/hwpml/2016/HwpUnitChar',
    'epub': 'http://www.idpf.org/2007/ops',
    'config': 'urn:oasis:names:tc:opendocument:xmlns:config:1.0',
}
for prefix, uri in NS_MAP.items():
    etree.register_namespace(prefix, uri)

ns = NS_MAP
HP = NS_MAP['hp']

# ============================================================
# 스킬 경로
# ============================================================
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TEMPLATE = os.path.join(SKILL_DIR, 'assets', 'template.hwpx')
HEADER_ROW_XML_PATH = os.path.join(SKILL_DIR, 'assets', 'template_header_row.xml')
DATA_ROW_XML_PATH = os.path.join(SKILL_DIR, 'assets', 'template_data_row.xml')
FIX_NS_SCRIPT = os.path.join(
    os.path.expanduser('~'), '.claude', 'skills', 'hwpx', 'scripts', 'fix_namespaces.py'
)


# ============================================================
# 유틸리티
# ============================================================
def generate_unique_id():
    return random.randint(1000000000, 2147483647)


def simplify_cell(cell, text_content):
    """셀 내용을 단일 hp:t 텍스트로 교체. 스타일 ID는 첫 번째 단락/런에서 보존."""
    sublist = cell.find('hp:subList', ns)
    if sublist is None:
        return

    first_p = sublist.find('hp:p', ns)
    if first_p is not None:
        para_pr = first_p.get('paraPrIDRef', '1')
        style_id = first_p.get('styleIDRef', '0')
        first_run = first_p.find('hp:run', ns)
        char_pr = first_run.get('charPrIDRef', '147') if first_run is not None else '147'
    else:
        para_pr, style_id, char_pr = '1', '0', '147'

    for child in list(sublist):
        sublist.remove(child)

    new_p = etree.SubElement(sublist, f'{{{HP}}}p')
    new_p.set('id', '2147483648')
    new_p.set('paraPrIDRef', para_pr)
    new_p.set('styleIDRef', style_id)
    new_p.set('pageBreak', '0')
    new_p.set('columnBreak', '0')
    new_p.set('merged', '0')

    new_run = etree.SubElement(new_p, f'{{{HP}}}run')
    new_run.set('charPrIDRef', char_pr)

    new_t = etree.SubElement(new_run, f'{{{HP}}}t')
    new_t.text = text_content if text_content else ''


def find_text_in_tree(root, search_text):
    """XML 트리에서 특정 텍스트를 포함하는 hp:t 요소들을 찾는다."""
    results = []
    for t_elem in root.iter(f'{{{HP}}}t'):
        if t_elem.text and search_text in t_elem.text:
            results.append(t_elem)
    return results


def replace_text_in_tree(root, old_text, new_text):
    """XML 트리에서 텍스트를 찾아 교체한다."""
    count = 0
    for t_elem in root.iter(f'{{{HP}}}t'):
        if t_elem.text and old_text in t_elem.text:
            t_elem.text = t_elem.text.replace(old_text, new_text)
            count += 1
    return count


# ============================================================
# 데이터 로드
# ============================================================
def load_data(json_path):
    """JSON 파일에서 교육과정 데이터를 로드하고 기본 검증."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 필수 키 검증
    assert 'school_info' in data, "school_info 키가 필요합니다"
    assert 'curriculum_tables' in data, "curriculum_tables 키가 필요합니다"

    info = data['school_info']
    assert 'subject' in info, "school_info.subject 키가 필요합니다"
    assert 'grades' in info, "school_info.grades 키가 필요합니다"

    for ct in data['curriculum_tables']:
        assert 'grade' in ct, "curriculum_tables[].grade 키가 필요합니다"
        assert 'rows' in ct, "curriculum_tables[].rows 키가 필요합니다"
        for row in ct['rows']:
            assert len(row) >= 8 or isinstance(row, dict), \
                "각 행은 8개 이상 컬럼 리스트 또는 딕셔너리여야 합니다"

    return data


def normalize_row(row):
    """행 데이터를 [시기, 시수, 누계, 단원명, 성취기준, 평가요소, 수업평가방법, 비고] 리스트로 변환."""
    if isinstance(row, list):
        # 8열 미만이면 빈 문자열로 패딩
        return row + [''] * max(0, 8 - len(row))
    elif isinstance(row, dict):
        keys = ['period', 'hours', 'cumulative', 'unit', 'standards',
                'eval_elements', 'methods', 'notes']
        return [str(row.get(k, '')) for k in keys]
    return [''] * 8


# ============================================================
# 핵심: 표 생성
# ============================================================
def build_grade_table(template_tbl, header_row_template, data_row_template, grade_data):
    """학년별 교수학습-평가 계획 표를 생성한다."""
    new_tbl = copy.deepcopy(template_tbl)
    new_tbl.set('id', str(generate_unique_id()))

    # 기존 행 제거
    for row in new_tbl.findall('hp:tr', ns):
        new_tbl.remove(row)

    # 헤더행 추가
    new_tbl.append(copy.deepcopy(header_row_template))

    # 데이터행 추가
    for row_idx, row_data in enumerate(grade_data):
        cols = normalize_row(row_data)
        new_row = copy.deepcopy(data_row_template)
        cells = new_row.findall('hp:tc', ns)

        for col_idx, cell in enumerate(cells):
            text = cols[col_idx] if col_idx < len(cols) else ''
            cell_addr = cell.find('hp:cellAddr', ns)
            if cell_addr is not None:
                cell_addr.set('rowAddr', str(row_idx + 1))
            simplify_cell(cell, text)

        new_tbl.append(new_row)

    total_rows = 1 + len(grade_data)
    new_tbl.set('rowCnt', str(total_rows))
    return new_tbl


def make_heading_paragraph(text, page_break='0'):
    """학년 제목 문단을 생성한다."""
    p = etree.Element(f'{{{HP}}}p')
    p.set('id', '0')
    p.set('paraPrIDRef', '24')
    p.set('styleIDRef', '0')
    p.set('pageBreak', page_break)
    p.set('columnBreak', '0')
    p.set('merged', '0')

    run = etree.SubElement(p, f'{{{HP}}}run')
    run.set('charPrIDRef', '20')

    t = etree.SubElement(run, f'{{{HP}}}t')
    t.text = text
    return p


def make_table_paragraph(p13_template, grade_tbl, note_tbl_template=None):
    """표를 포함하는 문단을 생성한다."""
    new_p = copy.deepcopy(p13_template)
    new_p.set('pageBreak', '0')

    runs = new_p.findall('hp:run', ns)
    if runs:
        first_run = runs[0]
        for tbl in list(first_run.findall('hp:tbl', ns)):
            first_run.remove(tbl)
        first_run.append(grade_tbl)

        if note_tbl_template is not None:
            note_tbl = copy.deepcopy(note_tbl_template)
            note_tbl.set('id', str(generate_unique_id()))
            first_run.append(note_tbl)

    return new_p


# ============================================================
# 메인 생성 로직
# ============================================================
def generate(data, template_path, output_path):
    """교수학습-평가 운영 계획 HWPX를 생성한다."""
    info = data['school_info']
    subject = info['subject']
    semester = info.get('semester', '1학기')
    year = info.get('year', '2026')
    school_name = info.get('school_name', 'OO중')
    grades = info['grades']

    print(f"[1/5] 템플릿 로드: {template_path}")

    # 템플릿 ZIP 읽기
    zf_in = zipfile.ZipFile(template_path, 'r')
    section0_bytes = zf_in.read('Contents/section0.xml')
    root = etree.fromstring(section0_bytes)

    # 행 템플릿 로드
    with open(HEADER_ROW_XML_PATH, 'r', encoding='utf-8') as f:
        header_row_template = etree.fromstring(f.read().encode('utf-8'))
    with open(DATA_ROW_XML_PATH, 'r', encoding='utf-8') as f:
        data_row_template = etree.fromstring(f.read().encode('utf-8'))

    # 표 목록
    all_tables = root.findall('.//hp:tbl', ns)
    print(f"  section0.xml 표 수: {len(all_tables)}")

    # ── 텍스트 교체 (제목, 기본정보) ──
    print(f"[2/5] 텍스트 교체: {subject}과 / {school_name} / {year}학년도 {semester}")
    # 교과명 교체
    replace_text_in_tree(root, '[ 교과명 ]', f'[ {subject} ]')
    replace_text_in_tree(root, '[교과명]', f'[{subject}]')
    # 학년도/학기
    replace_text_in_tree(root, '2026학년도', f'{year}학년도')

    # 학교명/학급수/교과서명 (기본정보 표 - 일반적으로 Table 2~3 부근)
    for g in grades:
        grade_num = g.get('grade', 1)
        classes = g.get('classes', '')
        textbook = g.get('textbook', '')
        hours = g.get('hours_per_week', '')
        # 템플릿 내의 플레이스홀더가 있으면 교체
        if classes:
            replace_text_in_tree(root, f'{grade_num}학년 학급수', f'{grade_num}학년 {classes}학급')
        if textbook:
            replace_text_in_tree(root, '교과서명', textbook)

    # ── 교수학습-평가 계획 표 생성 ──
    print(f"[3/5] 교수학습-평가 계획 표 생성: {len(data['curriculum_tables'])}개 학년")

    # Table 4 (교수학습-평가 계획 표)를 찾아서 교체
    # 템플릿의 Table 4는 예시 데이터가 들어있는 표
    if len(all_tables) < 5:
        print("  WARNING: 표가 5개 미만입니다. Table 4를 찾을 수 없습니다.")
        zf_in.close()
        return False

    tbl4_template = all_tables[4]
    note_tbl_template = all_tables[5] if len(all_tables) > 5 else None

    # Table 4가 들어있는 문단(p13) 찾기
    p13 = None
    p13_index = -1
    for i, child in enumerate(root):
        if tbl4_template in child.iter():
            p13 = child
            p13_index = i
            break

    if p13 is None:
        # 직접 검색: 부모를 따라가며 찾기
        for i, child in enumerate(root):
            tables_in_child = child.findall('.//hp:tbl', ns)
            if tbl4_template in tables_in_child:
                p13 = child
                p13_index = i
                break

    if p13 is None:
        print("  ERROR: Table 4 의 부모 문단을 찾을 수 없습니다.")
        zf_in.close()
        return False

    p13_template = copy.deepcopy(p13)

    # 학년별 표 생성
    grade_tables = []
    for ct in data['curriculum_tables']:
        grade_num = ct['grade']
        rows = ct['rows']
        tbl = build_grade_table(tbl4_template, header_row_template, data_row_template, rows)
        grade_tables.append((grade_num, tbl, len(rows)))
        print(f"  {grade_num}학년: {len(rows)}행 (헤더 1 + 데이터 {len(rows)})")

    # 원본 p13 제거 후 학년별 요소 삽입
    root.remove(p13)
    elements_to_insert = []

    for idx, (grade_num, tbl, row_count) in enumerate(grade_tables):
        # 학년 제목
        heading = make_heading_paragraph(
            f'{grade_num}학년 교수학습-평가 계획',
            page_break='1'
        )
        elements_to_insert.append(heading)

        # 표 문단
        include_note = (idx == 0 and note_tbl_template is not None)
        table_p = make_table_paragraph(
            p13_template, tbl,
            note_tbl_template if include_note else None
        )
        elements_to_insert.append(table_p)

        # 구분 빈 문단
        if idx < len(grade_tables) - 1:
            elements_to_insert.append(make_heading_paragraph(''))

    for i, elem in enumerate(elements_to_insert):
        root.insert(p13_index + i, elem)

    print(f"  {len(elements_to_insert)}개 요소 삽입 (인덱스 {p13_index})")

    # ── ZIP 리패킹 ──
    print(f"[4/5] HWPX 리패킹: {output_path}")
    section0_new = etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    file_data = {}
    file_meta = {}
    for info_item in zf_in.infolist():
        file_data[info_item.filename] = zf_in.read(info_item.filename)
        file_meta[info_item.filename] = info_item
    zf_in.close()

    with zipfile.ZipFile(output_path, 'w') as zf_out:
        # mimetype 먼저 (STORED)
        zf_out.writestr(
            zipfile.ZipInfo('mimetype', date_time=(2026, 3, 1, 0, 0, 0)),
            file_data['mimetype'],
            compress_type=zipfile.ZIP_STORED
        )
        for fname, fdata in file_data.items():
            if fname == 'mimetype':
                continue
            new_info = zipfile.ZipInfo(fname, date_time=file_meta[fname].date_time)
            if fname == 'Contents/section0.xml':
                new_info.compress_type = zipfile.ZIP_DEFLATED
                zf_out.writestr(new_info, section0_new)
            else:
                new_info.compress_type = file_meta[fname].compress_type
                zf_out.writestr(new_info, fdata)

    # ── 네임스페이스 후처리 ──
    print("[5/5] 네임스페이스 후처리...")
    if os.path.exists(FIX_NS_SCRIPT):
        subprocess.run([sys.executable, FIX_NS_SCRIPT, output_path],
                       capture_output=True, text=True)
        print("  fix_namespaces.py 실행 완료")
    else:
        print(f"  WARNING: {FIX_NS_SCRIPT} 를 찾을 수 없습니다. 수동 실행 필요.")

    # ── 검증 ──
    print("\n=== 검증 ===")
    with zipfile.ZipFile(output_path, 'r') as zf_v:
        # mimetype 확인
        first_entry = zf_v.infolist()[0]
        mime_ok = (first_entry.filename == 'mimetype' and
                   first_entry.compress_type == zipfile.ZIP_STORED)
        print(f"  mimetype STORED 첫 번째: {'PASS' if mime_ok else 'FAIL'}")

        # section0 표 수 확인
        v_root = etree.fromstring(zf_v.read('Contents/section0.xml'))
        v_tables = v_root.findall('.//hp:tbl', ns)
        print(f"  section0.xml 표 수: {len(v_tables)}")
        for i, tbl in enumerate(v_tables):
            rows = tbl.findall('hp:tr', ns)
            print(f"    Table {i}: {len(rows)}행")

        # ns0:/ns1: 확인
        s0_text = zf_v.read('Contents/section0.xml').decode('utf-8')
        has_bad_ns = 'ns0:' in s0_text or 'ns1:' in s0_text
        print(f"  네임스페이스 정상: {'FAIL (ns0/ns1 발견)' if has_bad_ns else 'PASS'}")

    print(f"\n완료: {output_path}")
    return True


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='교수학습-평가 운영 계획 HWPX 생성')
    parser.add_argument('--data', required=True, help='JSON 데이터 파일 경로')
    parser.add_argument('--template', default=DEFAULT_TEMPLATE, help='템플릿 HWPX 경로')
    parser.add_argument('--output', required=True, help='출력 HWPX 파일 경로')
    args = parser.parse_args()

    data = load_data(args.data)
    success = generate(data, args.template, args.output)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
