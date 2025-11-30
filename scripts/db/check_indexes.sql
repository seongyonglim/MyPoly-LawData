-- 인덱스 생성 상태 확인

-- bills 테이블 인덱스
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'bills'
ORDER BY indexname;

-- votes 테이블 인덱스
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'votes'
ORDER BY indexname;

-- assembly_members 테이블 인덱스
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'assembly_members'
ORDER BY indexname;

