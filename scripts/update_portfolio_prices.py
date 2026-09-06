#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: update_portfolio_prices.py
Tự động quét và cập nhật giá thị trường hiện tại (current_price) 
cho tất cả các loại tài sản trong Sổ tay / My Portfolio (journal_entries).
Hỗ trợ: Crypto (Binance), Cổ phiếu VN (TCBS/Entrade), Cổ phiếu US (Yahoo), Vàng (Giavang/SJC/Yahoo), Bạc, Tiền mặt & Nợ.
"""

import os
import sys
import time
import requests
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        result = urlparse(DATABASE_URL)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port or 5432
        )
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'trading'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

def fetch_usd_vnd_rate():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDVND=X?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rate = data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")
            if rate and rate > 10000:
                return float(rate)
    except Exception as e:
        print(f"⚠️ Không lấy được tỷ giá USD/VND qua Yahoo: {e}")
    return 25450.0

def fetch_crypto_price(symbol):
    clean_sym = symbol.upper().replace('/', '').replace('USDT', '').replace('USD', '').strip()
    if not clean_sym:
        return None
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={clean_sym}USDT"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()
            return float(data.get("price", 0))
    except Exception as e:
        print(f"⚠️ Binance ticker lỗi cho {symbol}: {e}")
    return None

def fetch_vn_stock_price(symbol):
    clean_sym = symbol.upper().strip()
    try:
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol={clean_sym}&resolution=1&from={int(time.time()) - 86400}&to={int(time.time())}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            closes = data.get("c", [])
            if closes:
                return float(closes[-1])
    except Exception:
        pass
    try:
        tcbs_url = f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term?ticker={clean_sym}&type=stock&resolution=D"
        res = requests.get(tcbs_url, timeout=4)
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                price = float(data[-1].get("close", 0))
                return price * 1000 if price < 1000 else price
    except Exception:
        pass
    return None

def fetch_us_stock_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper().strip()}?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            price = data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")
            if price:
                return float(price)
    except Exception as e:
        print(f"⚠️ Yahoo stock US lỗi cho {symbol}: {e}")
    return None

def fetch_gold_price(symbol, currency):
    try:
        res = requests.get("https://giavang.now/api/prices", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("success") and data.get("prices"):
                for k, item in data["prices"].items():
                    if "sjc" in k.lower() or "sjc" in str(item.get("name", "")).lower():
                        val = float(item.get("buy", 0))
                        if val > 0:
                            return val
    except Exception:
        pass
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            price = data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")
            if price:
                return float(price)
    except Exception:
        pass
    return None

def fetch_silver_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            price = data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")
            if price:
                return float(price)
    except Exception:
        pass
    return None

def update_portfolio_prices():
    print("🚀 Bắt đầu quét và cập nhật giá thị trường cho Danh mục Sổ tay (My Portfolio)...")
    usd_rate = fetch_usd_vnd_rate()
    print(f"💱 Tỷ giá USD/VND hiện tại: {usd_rate:,.0f} VND")

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, asset_type, symbol, quantity, price, currency, COALESCE(current_price, 0)
            FROM public.journal_entries
            ORDER BY id ASC;
        """)
        entries = cur.fetchall()
        print(f"📋 Tìm thấy {len(entries)} mục tài sản trong database.\n")

        updated_count = 0
        for entry in entries:
            e_id, user_id, asset_type, symbol, qty, cost_price, currency, old_curr_price = entry
            asset_type = (asset_type or "").upper()
            currency = (currency or "VND").upper()
            symbol = (symbol or "").strip()

            new_price = None

            if asset_type in ('CASH', 'DEBT'):
                new_price = 1.0
            elif asset_type == 'CRYPTO':
                p_usd = fetch_crypto_price(symbol)
                if p_usd:
                    new_price = p_usd * usd_rate if currency == 'VND' else p_usd
            elif asset_type == 'STOCK':
                if len(symbol) == 3 and currency == 'VND':
                    new_price = fetch_vn_stock_price(symbol)
                else:
                    p_usd = fetch_us_stock_price(symbol)
                    if p_usd:
                        new_price = p_usd * usd_rate if currency == 'VND' else p_usd
            elif asset_type == 'GOLD':
                p = fetch_gold_price(symbol, currency)
                if p:
                    new_price = p if currency == 'VND' else p / usd_rate
            elif asset_type == 'SILVER':
                p_usd = fetch_silver_price()
                if p_usd:
                    new_price = p_usd * usd_rate if currency == 'VND' else p_usd

            if new_price and new_price > 0:
                cur.execute("""
                    UPDATE public.journal_entries
                    SET current_price = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (new_price, e_id))
                updated_count += 1
                curr_symbol = "đ" if currency == 'VND' else "$"
                print(f"  ✅ [{asset_type}] {symbol}: {old_curr_price:,.2f} -> {new_price:,.2f}{curr_symbol} (ID: {e_id})")
            else:
                print(f"  ⏭️ [{asset_type}] {symbol}: Giữ nguyên giá hiện tại {old_curr_price:,.2f} (ID: {e_id})")

            time.sleep(0.1)

        conn.commit()
        cur.close()
        print(f"\n🎉 Hoàn tất! Đã cập nhật giá mới nhất cho {updated_count}/{len(entries)} tài sản.")
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật giá danh mục: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    update_portfolio_prices()
