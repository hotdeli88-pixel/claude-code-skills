# -*- coding: utf-8 -*-
"""
HWPX 표 서식 통일 스크립트
Usage: python apply_table_format.py <input.hwpx> <output.hwpx> <section> <config.json>

config.json 예시:
{
    "ref_table_index": 6,
    "target_indices": [7, 8, 9, 10],
    "table_width": 72244,
    "col_widths": [10120, 10120, 52004],
    "bf_pattern": {
        "header": [28, 24, 27],
        "mid_data": [22, 20, 21],
        "last_data": [26, 23, 25]
    },
    "hdr_charpr": "51",
    "data_charpr": "2",
    "hdr_parapr_map": {"0": "1", "1": "1", "2": "1"},
    "data_parapr_map": {"0": "1", "1": "1", "2": "0"}
}
"""

import zipfile
import sys
import io
import os
import json
from lxml import etree

# Windows cp949 인코딩 오류 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 네임스페이스 등록 ──
NS_REGISTRY = {
    'ha': 'http://www.hancom.co.kr/hwpml/2011/app',
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hp10': 'http://www.hancom.co.kr/hwpml/2016/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
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
for prefix, uri in NS_REGISTRY.items():
    etree.register_namespace(prefix, uri)

ns = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'}


def apply_table_format(tbl, col_widths, table_width,
                       bf_pattern, hdr_charpr, data_charpr,
                       hdr_parapr_map, data_parapr_map):
    """하나의 hp:tbl 요소에 서식을 적용한다."""
    rows = tbl.findall('.//hp:tr', ns)
    nrows = len(rows)

    # 표 레벨
    sz = tbl.find('hp:sz', ns)
    if sz is not None:
        sz.set('width', str(table_width))
    tbl.set('noAdjust', '1')

    changes = 0
    for ri, row in enumerate(rows):
        cells = row.findall('hp:tc', ns)
        for ci, cell in enumerate(cells):
            if ci >= len(col_widths):
                continue

            # cellSz
            csz = cell.find('hp:cellSz', ns)
            if csz is not None:
                csz.set('width', str(col_widths[ci]))

            # borderFillIDRef (위치별)
            if ri == 0:
                bf_list = bf_pattern['header']
                cell.set('header', '1')
            elif ri == nrows - 1:
                bf_list = bf_pattern['last_data']
                cell.set('header', '0')
            else:
                bf_list = bf_pattern['mid_data']
                cell.set('header', '0')

            if ci < len(bf_list):
                cell.set('borderFillIDRef', str(bf_list[ci]))

            # charPrIDRef
            cpr = hdr_charpr if ri == 0 else data_charpr
            for run in cell.findall('.//hp:run', ns):
                run.set('charPrIDRef', cpr)

            # paraPrIDRef
            ppr_map = hdr_parapr_map if ri == 0 else data_parapr_map
            for p in cell.findall('.//hp:p', ns):
                p.set('paraPrIDRef', str(ppr_map.get(str(ci), '0')))
                p.set('styleIDRef', '0')

            # linesegarray 제거
            for lsa in cell.findall('.//hp:linesegarray', ns):
                lsa.getparent().remove(lsa)

            changes += 1

    return changes


def repack_hwpx(input_path, output_path, section_name, new_section_bytes):
    """HWPX ZIP을 다시 압축한다. mimetype STORED 첫 번째."""
    zf = zipfile.ZipFile(input_path, 'r')
    files = {}
    for info in zf.infolist():
        files[info.filename] = zf.read(info.filename)
    zf.close()

    with zipfile.ZipFile(output_path, 'w') as zout:
        zout.writestr('mimetype', files['mimetype'],
                      compress_type=zipfile.ZIP_STORED)
        for fname, fdata in files.items():
            if fname == 'mimetype':
                continue
            if fname == f'Contents/{section_name}.xml':
                zout.writestr(fname, new_section_bytes,
                              compress_type=zipfile.ZIP_DEFLATED)
            else:
                zout.writestr(fname, fdata,
                              compress_type=zipfile.ZIP_DEFLATED)


def verify_table(tbl, col_widths, table_width, bf_pattern,
                 hdr_charpr, data_charpr):
    """표 서식을 검증하여 오류 목록을 반환한다."""
    errors = []
    rows = tbl.findall('.//hp:tr', ns)
    nrows = len(rows)

    sz = tbl.find('hp:sz', ns)
    if sz is not None and int(sz.get('width', 0)) != table_width:
        errors.append(f'width={sz.get("width")}!={table_width}')
    if tbl.get('noAdjust') != '1':
        errors.append('noAdjust!=1')

    for ri, row in enumerate(rows):
        cells = row.findall('hp:tc', ns)
        for ci, cell in enumerate(cells):
            if ci >= len(col_widths):
                continue

            bf = int(cell.get('borderFillIDRef', 0))
            if ri == 0:
                exp_bf = bf_pattern['header'][ci] if ci < len(bf_pattern['header']) else 0
            elif ri == nrows - 1:
                exp_bf = bf_pattern['last_data'][ci] if ci < len(bf_pattern['last_data']) else 0
            else:
                exp_bf = bf_pattern['mid_data'][ci] if ci < len(bf_pattern['mid_data']) else 0

            if bf != exp_bf:
                errors.append(f'R{ri}C{ci} bf={bf}!={exp_bf}')

            runs = cell.findall('.//hp:run', ns)
            if runs:
                cpr = runs[0].get('charPrIDRef', '?')
                exp_cpr = hdr_charpr if ri == 0 else data_charpr
                if cpr != exp_cpr:
                    errors.append(f'R{ri}C{ci} cpr={cpr}!={exp_cpr}')

    lsa = len(tbl.findall('.//hp:linesegarray', ns))
    if lsa > 0:
        errors.append(f'lineseg={lsa}')

    return errors


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python apply_table_format.py <input.hwpx> <output.hwpx> <section_name> <config.json>")
        print("  section_name: e.g., 'section0' or 'section1'")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    section_name = sys.argv[3]
    config_path = sys.argv[4]

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Read HWPX
    zf = zipfile.ZipFile(input_path, 'r')
    section_data = zf.read(f'Contents/{section_name}.xml')
    zf.close()

    root = etree.fromstring(section_data)
    tables = root.findall('.//hp:tbl', ns)

    target_indices = config['target_indices']
    col_widths = config['col_widths']
    table_width = config['table_width']
    bf_pattern = config['bf_pattern']
    hdr_charpr = config['hdr_charpr']
    data_charpr = config['data_charpr']
    hdr_parapr_map = config.get('hdr_parapr_map', {})
    data_parapr_map = config.get('data_parapr_map', {})

    total_changes = 0
    for ti in target_indices:
        if ti >= len(tables):
            print(f'WARNING: Table {ti} not found (total: {len(tables)})')
            continue
        tbl = tables[ti]
        changes = apply_table_format(
            tbl, col_widths, table_width,
            bf_pattern, hdr_charpr, data_charpr,
            hdr_parapr_map, data_parapr_map
        )
        total_changes += changes
        print(f'Table {ti}: {changes} cells updated')

    # Serialize
    section_bytes = etree.tostring(root, xml_declaration=True,
                                   encoding='UTF-8', standalone='yes')

    # Repack
    repack_hwpx(input_path, output_path, section_name, section_bytes)
    print(f'\nSaved: {output_path} ({os.path.getsize(output_path)} bytes)')
    print(f'Total changes: {total_changes} cells')

    # Verify
    print('\n=== Verification ===')
    zf2 = zipfile.ZipFile(output_path, 'r')
    d2 = zf2.read(f'Contents/{section_name}.xml')
    zf2.close()
    r2 = etree.fromstring(d2)
    tbls2 = r2.findall('.//hp:tbl', ns)

    ok = fail = 0
    for ti in target_indices:
        if ti >= len(tbls2):
            continue
        errors = verify_table(
            tbls2[ti], col_widths, table_width,
            bf_pattern, hdr_charpr, data_charpr
        )
        if errors:
            fail += 1
            print(f'Table {ti}: FAIL - {errors[:5]}')
        else:
            ok += 1

    print(f'\nResult: {ok} PASS / {fail} FAIL')
