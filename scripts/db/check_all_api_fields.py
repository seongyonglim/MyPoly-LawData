#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 응답의 모든 필드 확인 및 누락 필드 검증
"""

import sys
import os
from urllib.parse import unquote
from xml.etree import ElementTree as ET
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

ENCODED_SERVICE_KEY = os.environ.get("BILL_SERVICE_KEY")
if not ENCODED_SERVICE_KEY:
    raise ValueError("BILL_SERVICE_KEY environment variable is required")
SERVICE_KEY = unquote(ENCODED_SERVICE_KEY)

BILL_INFO_API = "https://apis.data.go.kr/9710000/BillInfoService2/getBillInfoList"

def get_all_api_fields():
    """API 응답의 모든 필드 확인"""
    print("=" * 80)
    print("API 응답 필드 전체 확인")
    print("=" * 80)
    
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "start_ord": 22,
        "end_ord": 22,
    }
    
    try:
        response = requests.get(BILL_INFO_API, params=params, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        items = root.findall(".//items/item")
        
        if not items:
            print("❌ API 응답에 데이터가 없습니다.")
            return
        
        print(f"\n✅ {len(items)}건의 의안 조회됨\n")
        
        # 첫 번째 의안의 모든 필드 확인
        first_item = items[0]
        all_fields = {}
        
        for child in first_item:
            tag = child.tag
            text = child.text if child.text else ""
            all_fields[tag] = text
        
        print("=" * 80)
        print("API에서 제공하는 모든 필드:")
        print("=" * 80)
        for field, value in sorted(all_fields.items()):
            value_preview = value[:50] + "..." if len(value) > 50 else value
            print(f"  {field:30s} = {value_preview}")
        
        # 현재 수집하는 필드 목록
        current_fields = {
            'billId': 'bill_id',
            'billNo': 'bill_no',
            'billName': 'title',
            'proposeDt': 'proposal_date',
            'proposerKind': 'proposer_kind',
            'proposerNm': 'proposer_name',
            'proposerName': 'proposer_name',
            'procStageCd': 'proc_stage_cd',
            'passGubn': 'pass_gubn',
            'procDt': 'proc_date',
            'generalResult': 'general_result',
            'summary': 'summary_raw',
            'linkUrl': 'link_url',
        }
        
        print("\n" + "=" * 80)
        print("현재 수집하는 필드:")
        print("=" * 80)
        for api_field, db_field in sorted(current_fields.items()):
            if api_field in all_fields:
                print(f"  ✅ {api_field:30s} → {db_field}")
            else:
                print(f"  ⚠️ {api_field:30s} → {db_field} (API에 없음)")
        
        # 누락된 필드 확인
        print("\n" + "=" * 80)
        print("누락된 필드 (API에 있지만 수집하지 않음):")
        print("=" * 80)
        missing_fields = []
        for api_field in sorted(all_fields.keys()):
            if api_field not in current_fields:
                missing_fields.append(api_field)
                value_preview = all_fields[api_field][:50] + "..." if len(all_fields[api_field]) > 50 else all_fields[api_field]
                print(f"  ❌ {api_field:30s} = {value_preview}")
        
        if not missing_fields:
            print("  ✅ 모든 필드를 수집하고 있습니다!")
        else:
            print(f"\n⚠️ 총 {len(missing_fields)}개의 필드가 누락되었습니다.")
        
        # DB 스키마와 비교
        print("\n" + "=" * 80)
        print("DB 스키마 필드 확인 필요:")
        print("=" * 80)
        db_fields_to_check = [
            'proposer_name',  # 방금 추가
            'proposer_count',  # 제안자 수 (제목에서 추출 가능)
            'committee',  # 소관위원회 (JRCMIT_NM)
            'proposal_session',  # 제안회기 (PPSL_SESS)
            'result',  # 본회의 심의결과 (RGS_CONF_RSLT)
            'result_date',  # 본회의 의결일 (RGS_RSLN_DT)
            'era',  # 대수 (ERACO)
            'bill_kind',  # 의안종류 (BILL_KND)
        ]
        
        for db_field in db_fields_to_check:
            # API 필드명 추정 (camelCase)
            possible_api_fields = [
                db_field.replace('_', ''),
                ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(db_field.split('_'))),
            ]
            found = False
            for api_field in all_fields.keys():
                if api_field.lower() in [pf.lower() for pf in possible_api_fields]:
                    print(f"  ✅ {db_field:30s} → {api_field} (수집 가능)")
                    found = True
                    break
            if not found:
                print(f"  ❌ {db_field:30s} → (API 필드명 확인 필요)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    get_all_api_fields()

