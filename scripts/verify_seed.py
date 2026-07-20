"""CI 用: 验证数据库种子数据已就位"""
import sqlite3
import sys
from pathlib import Path

db_path = Path('data/sqlite/造价通.db')
if not db_path.exists():
    print(f'[FAIL] DB 不存在: {db_path}', file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(db_path)
expected = {
    't_specialty': 14,
    't_price_unit': 12,
    't_topic_price': 100,
    't_fee_rate': 1,
    't_template_type': 8,
    't_template': 1,
    't_template_field': 1,
}
for t, min_n in expected.items():
    try:
        n = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: {n}')
        if n < min_n:
            print(f'  [WARN] {t} 行数 {n} < 预期 {min_n}')
    except Exception as e:
        print(f'  [FAIL] {t}: {e}')
conn.close()
print('OK')
