#!/usr/bin/env python3
"""
Sync data from Alwaysdata PostgreSQL to VPS PostgreSQL (152.53.208.182)
High-speed batch migration using execute_values.
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

SRC_CONFIG = {
    'host': 'postgresql-thehaohcm.alwaysdata.net',
    'user': 'thehaohcm',
    'password': 'Davidnth12171',
    'dbname': 'thehaohcm_trading_signal_db',
    'port': 5432,
    'connect_timeout': 15
}

DST_CONFIG = {
    'host': '152.53.208.182',
    'user': 'thehaohcm',
    'password': 'ngotrungtinh',
    'dbname': 'thehaohcm_trading_signal_db',
    'port': 5432,
    'connect_timeout': 15
}

TABLES_TO_SYNC = [
    'user_info',
    'symbols_watchlist',
    'cryptos_watchlist',
    'forex_watchlist',
    'futures_watchlist',
    'world_symbols_watchlist',
    'price_alerts',
    'triggered_alerts',
    'journal_entries',
    'community_posts',
    'community_comments',
    'real_estate_prices',
    'breakout_watchlist',
    'paper_positions',
    'paper_orders',
    'highest_bank_interest_rate',
    'economic_calendar',
    'system_settings',
    'take_notes',
]

def sync_table(src_conn, dst_conn, table):
    try:
        src_cur = src_conn.cursor(cursor_factory=RealDictCursor)
        src_cur.execute(f'SELECT * FROM public."{table}"')
        rows = src_cur.fetchall()
        src_cur.close()

        if not rows:
            print(f"  • {table}: 0 rows (skipped)")
            return

        dst_cur = dst_conn.cursor()
        cols = list(rows[0].keys())
        col_str = ', '.join([f'"{c}"' for c in cols])
        data_tuples = [tuple(row[c] for c in cols) for row in rows]

        insert_sql = f'INSERT INTO public."{table}" ({col_str}) VALUES %s ON CONFLICT DO NOTHING'
        execute_values(dst_cur, insert_sql, data_tuples, page_size=500)
        dst_conn.commit()

        # Update sequence if table has serial id
        if 'id' in cols:
            try:
                seq_query = f"SELECT setval(pg_get_serial_sequence('public.{table}', 'id'), COALESCE(MAX(id), 1)) FROM public.\"{table}\";"
                dst_cur.execute(seq_query)
                dst_conn.commit()
            except Exception:
                dst_conn.rollback()

        dst_cur.close()
        print(f"  ✓ {table}: batch synced {len(rows)} rows")
    except Exception as err:
        print(f"  ✗ {table} error: {err}")
        dst_conn.rollback()

def main():
    print("Connecting to Alwaysdata source DB...")
    src_conn = psycopg2.connect(**SRC_CONFIG)
    print("Connecting to VPS destination DB (152.53.208.182)...")
    dst_conn = psycopg2.connect(**DST_CONFIG)

    print("\nStarting high-speed data migration...")
    for t in TABLES_TO_SYNC:
        sync_table(src_conn, dst_conn, t)

    src_conn.close()
    dst_conn.close()
    print("\n✅ Migration from Alwaysdata to VPS completed!")

if __name__ == '__main__':
    main()
