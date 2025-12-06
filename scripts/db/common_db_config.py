#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
공통 데이터베이스 설정 모듈
모든 스크립트에서 사용할 수 있는 공통 DB 연결 함수
"""

import os
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    """환경 변수에서 데이터베이스 설정 가져오기"""
    config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'mypoly_lawdata'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD'),
        'port': int(os.environ.get('DB_PORT', '5432'))
    }
    
    if not config['password']:
        raise ValueError("DB_PASSWORD environment variable is required")
    
    return config

