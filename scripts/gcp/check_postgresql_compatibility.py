#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL 17 호환성 확인
"""

import sys

print("=" * 80)
print("PostgreSQL 17 호환성 확인")
print("=" * 80)

# psycopg2 버전 확인
try:
    import psycopg2
    print(f"✅ psycopg2 설치됨: {psycopg2.__version__}")
    
    # PostgreSQL 17 호환성
    # psycopg2-binary 2.9.x 이상은 PostgreSQL 17 지원
    version_parts = psycopg2.__version__.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1])
    
    if major >= 2 and minor >= 9:
        print("✅ PostgreSQL 17 호환 가능 (psycopg2 2.9.x 이상)")
    else:
        print("⚠️ psycopg2 버전이 낮을 수 있습니다. 업그레이드 권장")
        
except ImportError:
    print("❌ psycopg2가 설치되지 않았습니다.")

# requirements.txt 확인
print("\n현재 requirements.txt의 psycopg2 버전:")
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if 'psycopg2' in line.lower():
                print(f"  {line.strip()}")
except FileNotFoundError:
    print("  requirements.txt 파일을 찾을 수 없습니다.")

print("\n" + "=" * 80)
print("결론:")
print("PostgreSQL 17은 최신 버전이지만 psycopg2-binary 2.9.x 이상이면")
print("호환됩니다. 문제가 있으면 PostgreSQL 16으로 다운그레이드 가능합니다.")
print("=" * 80)

