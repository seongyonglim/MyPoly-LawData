#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 PostgreSQL 외부 접속 설정 자동화
관리자 권한으로 실행 필요
"""

import os
import sys
import subprocess
import shutil
import re
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def is_admin():
    """관리자 권한 확인"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def find_postgresql_data_dir():
    """PostgreSQL 데이터 디렉토리 찾기"""
    possible_paths = [
        r"C:\Program Files\PostgreSQL\17\data",
        r"C:\Program Files\PostgreSQL\16\data",
        r"C:\Program Files\PostgreSQL\15\data",
        r"C:\Program Files\PostgreSQL\14\data",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def modify_postgresql_conf(conf_path):
    """postgresql.conf 수정"""
    print(f"\n[2] postgresql.conf 수정 중...")
    
    if not os.path.exists(conf_path):
        print(f"❌ 파일을 찾을 수 없습니다: {conf_path}")
        return False
    
    # 백업 생성
    backup_path = f"{conf_path}.backup"
    shutil.copy2(conf_path, backup_path)
    print(f"✅ 백업 생성: {backup_path}")
    
    # 파일 읽기
    with open(conf_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # listen_addresses 확인
    if re.search(r"listen_addresses\s*=\s*['\"]?\*['\"]?", content):
        print("✅ listen_addresses = '*' 이미 설정됨")
        return True
    
    # listen_addresses 수정 또는 추가
    if re.search(r"listen_addresses\s*=", content):
        # 기존 줄 수정
        content = re.sub(
            r"listen_addresses\s*=\s*[^\r\n]+",
            "listen_addresses = '*'",
            content
        )
        print("✅ listen_addresses = '*' 로 변경")
    else:
        # 없으면 추가
        content += "\n# 외부 접속 허용\nlisten_addresses = '*'\n"
        print("✅ listen_addresses = '*' 추가")
    
    # 파일 쓰기
    with open(conf_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ postgresql.conf 수정 완료")
    return True

def modify_pg_hba_conf(hba_path):
    """pg_hba.conf 수정"""
    print(f"\n[3] pg_hba.conf 수정 중...")
    
    if not os.path.exists(hba_path):
        print(f"❌ 파일을 찾을 수 없습니다: {hba_path}")
        return False
    
    # 파일 읽기
    with open(hba_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 이미 설정되어 있는지 확인
    if re.search(r"0\.0\.0\.0/0", content):
        print("✅ 외부 접속 허용 이미 설정됨")
        return True
    
    # 백업 생성
    backup_path = f"{hba_path}.backup"
    shutil.copy2(hba_path, backup_path)
    print(f"✅ 백업 생성: {backup_path}")
    
    # 파일 끝에 추가
    new_line = "\n# 외부 접속 허용 (VM에서 접속용)\nhost    all             all             0.0.0.0/0               md5\n"
    with open(hba_path, 'a', encoding='utf-8') as f:
        f.write(new_line)
    
    print("✅ 외부 접속 허용 추가 완료")
    return True

def restart_postgresql_service():
    """PostgreSQL 서비스 재시작"""
    print(f"\n[4] PostgreSQL 서비스 재시작 중...")
    
    try:
        # 서비스 찾기
        result = subprocess.run(
            ['sc', 'query', 'type=', 'service'],
            capture_output=True,
            text=True
        )
        
        # PostgreSQL 서비스 찾기
        services = []
        for line in result.stdout.split('\n'):
            if 'postgresql' in line.lower():
                # 서비스 이름 추출
                match = re.search(r'SERVICE_NAME:\s*(\S+)', line)
                if match:
                    services.append(match.group(1))
        
        if not services:
            print("❌ PostgreSQL 서비스를 찾을 수 없습니다")
            return False
        
        service_name = services[0]
        print(f"✅ 서비스 발견: {service_name}")
        
        # 서비스 재시작
        subprocess.run(['net', 'stop', service_name], check=True)
        subprocess.run(['net', 'start', service_name], check=True)
        print(f"✅ PostgreSQL 서비스 재시작 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 서비스 재시작 실패: {e}")
        print("수동으로 재시작하세요:")
        print("  서비스 관리자에서 PostgreSQL 서비스 재시작")
        return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def setup_firewall():
    """Windows 방화벽 설정"""
    print(f"\n[5] Windows 방화벽 설정 중...")
    
    try:
        # 방화벽 규칙 확인
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=PostgreSQL'],
            capture_output=True,
            text=True
        )
        
        if 'PostgreSQL' in result.stdout:
            print("✅ 방화벽 규칙 이미 존재")
            return True
        
        # 방화벽 규칙 추가
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=PostgreSQL',
            'dir=in',
            'action=allow',
            'protocol=TCP',
            'localport=5432'
        ], check=True)
        
        print("✅ 방화벽 규칙 추가 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 방화벽 규칙 추가 실패 (이미 존재할 수 있음): {e}")
        return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def get_public_ip():
    """공개 IP 확인"""
    print(f"\n[6] 공개 IP 확인 중...")
    
    try:
        import urllib.request
        ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf-8')
        print(f"✅ 공개 IP: {ip}")
        return ip
    except Exception as e:
        print(f"❌ 공개 IP 확인 실패: {e}")
        return "확인 필요"

def main():
    """메인 함수"""
    print("=" * 80)
    print("로컬 PostgreSQL 외부 접속 설정")
    print("=" * 80)
    
    # 관리자 권한 확인
    if not is_admin():
        print("\n❌ 관리자 권한이 필요합니다.")
        print("PowerShell을 관리자 권한으로 실행하세요.")
        print("또는 명령 프롬프트를 관리자 권한으로 실행하세요.")
        return
    
    # PostgreSQL 데이터 디렉토리 찾기
    print("\n[1] PostgreSQL 설정 파일 찾는 중...")
    data_path = find_postgresql_data_dir()
    
    if not data_path:
        print("❌ PostgreSQL 데이터 디렉토리를 찾을 수 없습니다.")
        print("수동으로 설정하세요:")
        print("  - postgresql.conf: listen_addresses = '*'")
        print("  - pg_hba.conf: host all all 0.0.0.0/0 md5")
        return
    
    print(f"✅ 데이터 디렉토리 발견: {data_path}")
    
    postgresql_conf = os.path.join(data_path, "postgresql.conf")
    pg_hba_conf = os.path.join(data_path, "pg_hba.conf")
    
    # 설정 파일 수정
    modify_postgresql_conf(postgresql_conf)
    modify_pg_hba_conf(pg_hba_conf)
    
    # 서비스 재시작
    restart_postgresql_service()
    
    # 방화벽 설정
    setup_firewall()
    
    # 공개 IP 확인
    public_ip = get_public_ip()
    
    # 완료
    print("\n" + "=" * 80)
    print("설정 완료!")
    print("=" * 80)
    print("\n다음 단계:")
    print("1. VM SSH 접속")
    print("2. 다음 명령어 실행:")
    print("")
    print(f"   cd ~/MyPoly-LawData")
    print("   git pull origin main")
    print("   source venv/bin/activate")
    print(f"   export LOCAL_DB_IP={public_ip}")
    print("   python scripts/gcp/migrate_direct_python.py")
    print("")

if __name__ == '__main__':
    main()

