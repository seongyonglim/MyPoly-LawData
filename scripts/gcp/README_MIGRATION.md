# GCP 마이그레이션 스크립트 가이드

## ✅ 최종 사용 스크립트

### `migrate_direct_public_ip.py`
**로컬 PC에서 실행**: Cloud SQL 공개 IP를 직접 사용하여 데이터 마이그레이션

**사용법**:
```powershell
cd C:\polywave\MyPoly-LawData
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install psycopg2-binary
python scripts/gcp/migrate_direct_public_ip.py
```

**사전 준비**:
1. GCP 콘솔 → Cloud SQL → 인스턴스 → 연결
2. '승인된 네트워크'에 로컬 PC의 공개 IP 추가

---

## ❌ 사용하지 않는 스크립트들

다음 스크립트들은 시도했지만 실패했거나 사용하지 않는 방법들입니다:

- `migrate_direct_python.py` - VM에서 로컬 DB 접속 시도 (포트 포워딩 필요)
- `migrate_from_local_db.py` - VM에서 로컬 DB 접속 시도 (포트 포워딩 필요)
- `migrate_from_local_to_cloud.py` - SSH 터널링 방식 (SSH 키 설정 복잡)
- `migrate_via_ssh_tunnel.py` - SSH 터널링 방식 (SSH 키 설정 복잡)
- `migrate_via_vm.py` - VM을 통한 마이그레이션 (복잡함)
- `migrate_direct.py` - 구버전
- `migrate_data_to_cloud_sql.py` - 구버전
- `import_csv_*.py`, `import_csv_*.sh` - CSV 방식 (인코딩 문제)
- `fix_csv_encoding.sh` - CSV 인코딩 수정 (사용 안 함)
- `export_to_*.ps1`, `export_to_*.py` - 내보내기 스크립트 (사용 안 함)

---

## 📝 참고

자세한 마이그레이션 과정은 `docs/gcp_migration_summary.md`를 참고하세요.

