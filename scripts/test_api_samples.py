# -*- coding: utf-8 -*-
"""
API 응답 샘플 확인 스크립트

3개 API의 실제 응답을 확인하여 필드명과 데이터 구조를 검증합니다.
"""

import os
import json
import sys
from urllib.parse import unquote
from xml.etree import ElementTree as ET

import requests

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# API 키
# 환경변수에서 가져오거나 기본값 사용
# 공공데이터포털 인증키 (의안정보 API용)
ENCODED_SERVICE_KEY = os.environ.get("BILL_SERVICE_KEY")
if not ENCODED_SERVICE_KEY:
    raise ValueError("BILL_SERVICE_KEY environment variable is required")
SERVICE_KEY = unquote(ENCODED_SERVICE_KEY)

# 열린국회정보 인증키 (표결정보, 의원정보 API용)
ASSEMBLY_KEY = os.environ.get("ASSEMBLY_SERVICE_KEY")
if not ASSEMBLY_KEY:
    raise ValueError("ASSEMBLY_SERVICE_KEY environment variable is required")

# API 엔드포인트
BILL_INFO_API = "https://apis.data.go.kr/9710000/BillInfoService2/getBillInfoList"
# 국회의원 정보 통합 API
MEMBER_INFO_API = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"
# 국회의원 본회의 표결정보 API
VOTE_INFO_API = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"

def test_bill_info_api():
    """의안정보 통합 API 테스트"""
    print("=" * 80)
    print("1. 의안정보 통합 API 테스트")
    print("=" * 80)
    
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 3,  # 샘플 3건만
        "start_ord": 22,
        "end_ord": 22,
    }
    
    try:
        response = requests.get(BILL_INFO_API, params=params, timeout=10)
        response.raise_for_status()
        
        # XML 파싱
        root = ET.fromstring(response.text)
        
        print(f"\n응답 상태: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        items = root.findall(".//items/item")
        print(f"\n조회된 의안 수: {len(items)}")
        
        if items:
            print("\n첫 번째 의안 샘플:")
            sample = items[0]
            for child in sample:
                print(f"  {child.tag}: {child.text}")
            
            # JSON으로 변환하여 저장
            sample_data = {}
            for child in sample:
                sample_data[child.tag] = child.text
            
            with open("api_samples/bill_info_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            print("\n✅ 샘플 데이터 저장: api_samples/bill_info_sample.json")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def test_vote_info_api():
    """국회의원 본회의 표결정보 API 테스트"""
    print("\n" + "=" * 80)
    print("2. 국회의원 본회의 표결정보 API 테스트")
    print("=" * 80)
    
    # 이미지에서 확인한 의안번호 2211945 (국민연금법 일부개정법률안)로 테스트
    # 이미 찾아놓은 BILL_ID 사용
    target_bill_no = "2211945"  # 이미지에서 확인한 의안번호
    bill_id = "PRC_P2M5U0T8A0Z1W0F9E1D7X5W5G5D0M1"  # 이미 찾아놓은 BILL_ID
    
    print(f"\n의안번호 {target_bill_no} (국민연금법 일부개정법률안)")
    print(f"BILL_ID: {bill_id}")
    
    try:
        print(f"\n의안번호 {target_bill_no}로 BILL_ID 찾는 중...")
        # 여러 페이지를 확인하여 해당 의안번호 찾기
        for page in range(1, 10):  # 최대 10페이지까지 확인
            bill_params = {
                "serviceKey": SERVICE_KEY,
                "pageNo": page,
                "numOfRows": 100,
                "start_ord": 22,
                "end_ord": 22,
            }
            bill_response = requests.get(BILL_INFO_API, params=bill_params, timeout=10)
            bill_root = ET.fromstring(bill_response.text)
            bill_items = bill_root.findall(".//items/item")
            
            for item in bill_items:
                bill_no_elem = item.find("billNo")
                if bill_no_elem is not None and bill_no_elem.text == target_bill_no:
                    bill_id_elem = item.find("billId")
                    if bill_id_elem is not None:
                        bill_id = bill_id_elem.text
                        bill_name = item.find("billName")
                        bill_name_text = bill_name.text if bill_name is not None else ""
                        print(f"✅ 의안번호 {target_bill_no} 발견!")
                        print(f"   BILL_ID: {bill_id}")
                        print(f"   의안명: {bill_name_text}")
                        break
            
            if bill_id:
                break
        
        if not bill_id:
            print(f"\n⚠️ 의안번호 {target_bill_no}를 찾지 못했습니다.")
            # 다른 방법: 처리완료된 의안 찾기
            print("처리완료된 의안 찾는 중...")
            for page in range(1, 5):
                bill_params = {
                    "serviceKey": SERVICE_KEY,
                    "pageNo": page,
                    "numOfRows": 50,
                    "start_ord": 22,
                    "end_ord": 22,
                }
                bill_response = requests.get(BILL_INFO_API, params=bill_params, timeout=10)
                bill_root = ET.fromstring(bill_response.text)
                bill_items = bill_root.findall(".//items/item")
                
                for item in bill_items:
                    pass_gubn = item.find("passGubn")
                    if pass_gubn is not None and "처리완료" in pass_gubn.text:
                        bill_id_elem = item.find("billId")
                        if bill_id_elem is not None:
                            bill_id = bill_id_elem.text
                            bill_name = item.find("billName")
                            bill_name_text = bill_name.text if bill_name is not None else ""
                            print(f"\n처리완료된 의안 발견: {bill_id}")
                            print(f"의안명: {bill_name_text[:50]}...")
                            break
                
                if bill_id:
                    break
        
        if not bill_id:
            # 최후의 수단: 첫 번째 의안 사용
            print("\n⚠️ 특정 의안을 찾지 못했습니다. 첫 번째 의안으로 테스트합니다.")
            bill_params = {
                "serviceKey": SERVICE_KEY,
                "pageNo": 1,
                "numOfRows": 1,
                "start_ord": 22,
                "end_ord": 22,
            }
            bill_response = requests.get(BILL_INFO_API, params=bill_params, timeout=10)
            bill_root = ET.fromstring(bill_response.text)
            bill_item = bill_root.find(".//items/item")
            if bill_item is not None:
                bill_id_elem = bill_item.find("billId")
                if bill_id_elem is not None:
                    bill_id = bill_id_elem.text
                    print(f"\n의안정보 API에서 가져온 BILL_ID: {bill_id}")
    except Exception as e:
        print(f"⚠️ 의안정보에서 BILL_ID 가져오기 실패: {e}")
    
    # BILL_ID가 없으면 샘플 BILL_ID 사용
    if not bill_id:
        bill_id = "PRC_W2U5V1T1P0P6N1P5N5N7L3U7U8S6T3"  # 이전 테스트에서 가져온 샘플
        print(f"\n샘플 BILL_ID 사용: {bill_id}")
    
    # 여러 방법으로 시도
    # 방법 1: BILL_ID와 AGE로 조회
    params = {
        "KEY": ASSEMBLY_KEY,  # 열린국회정보 인증키 사용
        "Type": "xml",
        "pIndex": 1,
        "pSize": 10,  # 더 많은 데이터 가져오기
        "BILL_ID": bill_id,
        "AGE": "22",  # 22대 국회
    }
    
    print(f"\n[방법 1] BILL_ID와 AGE로 조회")
    print(f"  BILL_ID: {bill_id}")
    print(f"  AGE: 22")
    
    try:
        response = requests.get(VOTE_INFO_API, params=params, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        
        print(f"\n응답 상태: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # 에러 체크
        result_code = root.find(".//CODE")
        if result_code is not None and result_code.text != "INFO-000":
            result_msg = root.find(".//MESSAGE")
            msg_text = result_msg.text if result_msg is not None else "알 수 없는 오류"
            print(f"\n⚠️ API 오류: {result_code.text} - {msg_text}")
            # 응답 전체 출력 (디버깅용)
            print(f"\n응답 내용 (일부):\n{response.text[:500]}")
            return None
        
        items = root.findall(".//row")
        print(f"\n조회된 표결 정보 수: {len(items)}")
        
        if items:
            print(f"\n✅ 표결 정보 {len(items)}건 발견!")
            print("\n첫 번째 표결 정보 샘플:")
            sample = items[0]
            for child in sample:
                print(f"  {child.tag}: {child.text}")
            
            sample_data = {}
            for child in sample:
                sample_data[child.tag] = child.text
            
            with open("api_samples/vote_info_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            print("\n✅ 샘플 데이터 저장: api_samples/vote_info_sample.json")
            
            # 추가로 의안번호로도 시도해보기
            if len(items) > 0:
                bill_no_from_vote = sample.find("BILL_NO")
                if bill_no_from_vote is not None:
                    print(f"\n[추가 테스트] 의안번호 {bill_no_from_vote.text}로 조회 시도...")
                    params2 = {
                        "KEY": ASSEMBLY_KEY,
                        "Type": "xml",
                        "pIndex": 1,
                        "pSize": 5,
                        "BILL_NO": bill_no_from_vote.text,
                        "AGE": "22",
                    }
                    try:
                        response2 = requests.get(VOTE_INFO_API, params=params2, timeout=10)
                        response2.raise_for_status()
                        root2 = ET.fromstring(response2.text)
                        items2 = root2.findall(".//row")
                        print(f"  의안번호로 조회 결과: {len(items2)}건")
                    except Exception as e2:
                        print(f"  ⚠️ 의안번호로 조회 실패: {e2}")
        else:
            print("\n⚠️ 표결 정보가 없습니다.")
            # 방법 2: 의안번호로 직접 조회 시도
            print("\n[방법 2] 의안번호 2211945로 직접 조회 시도...")
            params2 = {
                "KEY": ASSEMBLY_KEY,
                "Type": "xml",
                "pIndex": 1,
                "pSize": 10,
                "BILL_NO": "2211945",
                "AGE": "22",
            }
            try:
                response2 = requests.get(VOTE_INFO_API, params=params2, timeout=10)
                response2.raise_for_status()
                root2 = ET.fromstring(response2.text)
                
                result_code2 = root2.find(".//CODE")
                if result_code2 is not None and result_code2.text != "INFO-000":
                    result_msg2 = root2.find(".//MESSAGE")
                    msg_text2 = result_msg2.text if result_msg2 is not None else "알 수 없는 오류"
                    print(f"  ⚠️ API 오류: {result_code2.text} - {msg_text2}")
                else:
                    items2 = root2.findall(".//row")
                    print(f"  ✅ 의안번호로 조회 성공: {len(items2)}건")
                    if items2:
                        sample2 = items2[0]
                        print("\n  첫 번째 표결 정보:")
                        for child in sample2:
                            print(f"    {child.tag}: {child.text}")
                        
                        sample_data2 = {}
                        for child in sample2:
                            sample_data2[child.tag] = child.text
                        
                        with open("api_samples/vote_info_sample.json", "w", encoding="utf-8") as f:
                            json.dump(sample_data2, f, ensure_ascii=False, indent=2)
                        print("\n  ✅ 샘플 데이터 저장: api_samples/vote_info_sample.json")
            except Exception as e2:
                print(f"  ❌ 의안번호로 조회 실패: {e2}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_member_info_api():
    """국회의원 정보 통합 API 테스트"""
    print("\n" + "=" * 80)
    print("3. 국회의원 정보 통합 API 테스트")
    print("=" * 80)
    
    params = {
        "KEY": ASSEMBLY_KEY,  # 열린국회정보 인증키 사용
        "Type": "xml",
        "pIndex": 1,
        "pSize": 3,
    }
    
    try:
        response = requests.get(MEMBER_INFO_API, params=params, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        
        print(f"\n응답 상태: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # 에러 체크
        result_code = root.find(".//CODE")
        if result_code is not None and result_code.text != "INFO-000":
            result_msg = root.find(".//MESSAGE")
            msg_text = result_msg.text if result_msg is not None else "알 수 없는 오류"
            print(f"\n⚠️ API 오류: {result_code.text} - {msg_text}")
            return None
        
        items = root.findall(".//row")
        print(f"\n조회된 의원 정보 수: {len(items)}")
        
        if items:
            print("\n첫 번째 의원 정보 샘플:")
            sample = items[0]
            for child in sample:
                print(f"  {child.tag}: {child.text}")
            
            sample_data = {}
            for child in sample:
                sample_data[child.tag] = child.text
            
            with open("api_samples/member_info_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            print("\n✅ 샘플 데이터 저장: api_samples/member_info_sample.json")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_common_fields():
    """공통 필드 비교 분석"""
    print("\n" + "=" * 80)
    print("4. 공통 필드 비교 분석")
    print("=" * 80)
    
    try:
        # 저장된 샘플 파일 읽기
        bill_sample = None
        vote_sample = None
        member_sample = None
        
        if os.path.exists("api_samples/bill_info_sample.json"):
            with open("api_samples/bill_info_sample.json", "r", encoding="utf-8") as f:
                bill_sample = json.load(f)
        
        if os.path.exists("api_samples/vote_info_sample.json"):
            with open("api_samples/vote_info_sample.json", "r", encoding="utf-8") as f:
                vote_sample = json.load(f)
        
        if os.path.exists("api_samples/member_info_sample.json"):
            with open("api_samples/member_info_sample.json", "r", encoding="utf-8") as f:
                member_sample = json.load(f)
        
        # BILL_ID 비교
        if bill_sample and vote_sample:
            bill_id_bill = bill_sample.get("billId") or bill_sample.get("BILL_ID")
            bill_id_vote = vote_sample.get("billId") or vote_sample.get("BILL_ID")
            
            print("\n[BILL_ID 비교]")
            print(f"  의안정보 API: {bill_id_bill}")
            print(f"  표결정보 API: {bill_id_vote}")
            if bill_id_bill and bill_id_vote:
                if bill_id_bill == bill_id_vote:
                    print("  ✅ 동일한 형식/값으로 보입니다")
                else:
                    print("  ⚠️ 다른 형식/값입니다. 추가 확인 필요")
        
        # 의원 식별자 비교
        if vote_sample and member_sample:
            member_id_vote = vote_sample.get("memberNo") or vote_sample.get("MEMBER_NO")
            member_id_member = member_sample.get("naasCd") or member_sample.get("NAAS_CD")
            
            print("\n[의원 식별자 비교]")
            print(f"  표결정보 API (MEMBER_NO): {member_id_vote}")
            print(f"  의원정보 API (NAAS_CD): {member_id_member}")
            if member_id_vote and member_id_member:
                if member_id_vote == member_id_member:
                    print("  ✅ 동일한 식별자로 보입니다")
                else:
                    print("  ⚠️ 다른 식별자입니다. 매핑 테이블 필요할 수 있음")
        
    except Exception as e:
        print(f"❌ 비교 분석 중 오류: {e}")

def main():
    # 샘플 저장 디렉토리 생성
    os.makedirs("api_samples", exist_ok=True)
    
    print("API 응답 샘플 확인 시작...\n")
    
    # 각 API 테스트
    test_bill_info_api()
    test_vote_info_api()
    test_member_info_api()
    
    # 공통 필드 비교
    compare_common_fields()
    
    print("\n" + "=" * 80)
    print("완료!")
    print("=" * 80)
    print("\n다음 단계:")
    print("1. api_samples/ 디렉토리의 샘플 파일 확인")
    print("2. docs/api-field-mapping.md 문서 업데이트")
    print("3. 실제 필드명과 데이터 구조 반영하여 DB 설계 수정")

if __name__ == "__main__":
    main()

