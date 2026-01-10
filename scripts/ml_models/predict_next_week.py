import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import os
import json
from pycaret.regression import *
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

warnings.filterwarnings('ignore')

print("=" * 70)
print("GOLD PRICE PREDICTION - NEXT WEEK FORECAST")
print("=" * 70)

DATA_FILE = 'gold_macro_data_full.csv'
MODEL_FILE = 'best_model_price.pkl'
NEWS_FILE = 'gold_price_model.json'

# ==========================================
# 1. LOAD DATA AND UPDATE WITH LATEST
# ==========================================
def load_and_update_data():
    """Load existing data and update with latest prices"""
    print("\n[1/5] Đang tải dữ liệu và cập nhật giá mới nhất...")
    
    if not os.path.exists(DATA_FILE):
        print("   ❌ Không tìm thấy file dữ liệu. Chạy improved_gold_prediction.py trước.")
        return pd.DataFrame()
    
    # Load existing data
    df = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
    df_weekly = df.resample('W-FRI').last().ffill()
    
    print(f"   ✓ Dữ liệu hiện tại: từ {df_weekly.index[0].date()} đến {df_weekly.index[-1].date()}")
    
    # Try to fetch latest data (last 2 weeks)
    try:
        print("   ⟳ Đang cập nhật giá mới nhất từ Yahoo Finance...")
        tickers = {
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'DXY': 'DX-Y.NYB',
            'US10Y': '^TNX',
            'TIPS': 'TIP',
            'SP500': '^GSPC',
            'VIX': '^VIX',
            'Miners': 'GDX',
            'Oil': 'CL=F'
        }
        
        latest_data = pd.DataFrame()
        for name, ticker in tickers.items():
            temp_df = yf.download(ticker, period='1mo', progress=False)
            if isinstance(temp_df.columns, pd.MultiIndex):
                latest_data[name] = temp_df['Close'].iloc[:, 0]
            else:
                latest_data[name] = temp_df['Close']
        
        latest_weekly = latest_data.resample('W-FRI').last().ffill()
        
        # Merge with existing data (only add new weeks)
        df_combined = pd.concat([df_weekly, latest_weekly])
        df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
        df_combined = df_combined.sort_index()
        
        # Save updated data
        df_combined.to_csv(DATA_FILE)
        print(f"   ✓ Cập nhật thành công! Dữ liệu mới nhất: {df_combined.index[-1].date()}")
        
        return df_combined
        
    except Exception as e:
        print(f"   ⚠ Không thể cập nhật (offline?): {e}")
        print("   → Sử dụng dữ liệu cũ")
        return df_weekly

# ==========================================
# 2. CREATE FEATURES (SAME AS TRAINING)
# ==========================================
def create_advanced_features(df_input):
    """Create same features as training"""
    print("\n[2/5] Đang tạo features...")
    df = df_input.copy()
    
    # GEO SCORE (Historical Events)
    df['Geo_Score'] = 1.0
    df.loc['2022-02':'2022-04', 'Geo_Score'] = 9.0
    df.loc['2023-10':'2023-11', 'Geo_Score'] = 8.0
    df.loc['2020-03':'2020-05', 'Geo_Score'] = 6.0
    
    # BASIC RETURNS
    df['Gold_Ret'] = df['Gold'].pct_change()
    df['DXY_Ret'] = df['DXY'].pct_change()
    df['SP500_Ret'] = df['SP500'].pct_change()
    df['Oil_Ret'] = df['Oil'].pct_change()
    df['Silver_Ret'] = df['Silver'].pct_change()
    
    # LAGGED FEATURES
    for lag in [1, 2, 3, 4]:
        df[f'Gold_Ret_Lag{lag}'] = df['Gold_Ret'].shift(lag)
        df[f'DXY_Ret_Lag{lag}'] = df['DXY_Ret'].shift(lag)
        df[f'VIX_Lag{lag}'] = df['VIX'].shift(lag)
    
    # ROLLING STATISTICS
    for window in [4, 8, 12]:
        df[f'Gold_MA{window}'] = df['Gold'].rolling(window).mean()
        df[f'Gold_Deviation_MA{window}'] = (df['Gold'] - df[f'Gold_MA{window}']) / df[f'Gold_MA{window}']
        df[f'Gold_Std{window}'] = df['Gold_Ret'].rolling(window).std()
        df[f'VIX_MA{window}'] = df['VIX'].rolling(window).mean()
        df[f'Gold_Price_Position{window}'] = df['Gold'] / df[f'Gold_MA{window}'] - 1
    
    # MOMENTUM INDICATORS
    df['Gold_Momentum_4w'] = df['Gold'].pct_change(4)
    df['Gold_Momentum_8w'] = df['Gold'].pct_change(8)
    df['Gold_Momentum_12w'] = df['Gold'].pct_change(12)
    df['Gold_Acceleration'] = df['Gold_Ret'] - df['Gold_Ret'].shift(1)
    
    # VOLATILITY INDICATORS
    df['VIX_Change'] = df['VIX'].pct_change()
    df['VIX_Spike'] = (df['VIX'] > df['VIX'].rolling(12).mean() * 1.5).astype(int)
    
    # REAL YIELD
    df['Real_Yield_Proxy'] = df['US10Y'] / df['TIPS']
    df['Real_Yield_Change'] = df['Real_Yield_Proxy'].pct_change()
    df['Real_Yield_MA4'] = df['Real_Yield_Proxy'].rolling(4).mean()
    
    # FEAR FACTOR
    df['Fear_Factor'] = df['VIX'] * df['Geo_Score']
    df['Fear_Factor_Change'] = df['Fear_Factor'].pct_change()
    
    # CORRELATION FEATURES
    df['Gold_Silver_Ratio'] = df['Gold'] / df['Silver']
    df['Gold_Silver_Ratio_Change'] = df['Gold_Silver_Ratio'].pct_change()
    df['Gold_DXY_Divergence'] = df['Gold_Ret'] + df['DXY_Ret']
    
    # MARKET REGIME
    df['Risk_On'] = ((df['SP500_Ret'] > 0) & (df['VIX'] < 20)).astype(int)
    df['Risk_Off'] = ((df['SP500_Ret'] < 0) & (df['VIX'] > 25)).astype(int)
    
    # TARGET (not used for prediction, but needed for structure)
    df['Target_Price'] = df['Gold'].shift(-1)
    
    df.dropna(inplace=True)
    
    print(f"   ✓ Tạo {len(df.columns)} features")
    return df

# ==========================================
# 3. LOAD NEWS FACTORS (OPTIONAL)
# ==========================================
def load_news_factors():
    """Load news factors if available"""
    print("\n[3/5] Đang kiểm tra news factors...")
    
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, 'r') as f:
                news_data = json.load(f)
            
            print(f"   ✓ Tìm thấy news factors:")
            print(f"      - Geo Score: {news_data.get('geo_score', 'N/A')}")
            print(f"      - VIX: {news_data.get('vix', 'N/A')}")
            print(f"      - DXY Change: {news_data.get('dxy_pct', 'N/A')}%")
            print(f"      - Yield Change: {news_data.get('yield_pct', 'N/A')}%")
            print(f"      - Reasoning: {news_data.get('reasoning', 'N/A')}")
            
            return news_data
        except Exception as e:
            print(f"   ⚠ Không đọc được file: {e}")
            return None
    else:
        print(f"   ℹ Không có file {NEWS_FILE}")
        print("   → Sử dụng giá trị hiện tại (không điều chỉnh)")
        return None

# ==========================================
# 4. MAKE PREDICTION
# ==========================================
def predict_next_week(df, news_factors=None, manual_current_price=None):
    """Make prediction for next week"""
    print("\n[4/5] Đang predict giá tuần tới...")
    
    if not os.path.exists(f'{MODEL_FILE}.pkl'):
        print(f"   ❌ Không tìm thấy model file '{MODEL_FILE}.pkl'")
        print("   → Chạy improved_gold_prediction.py trước để train model")
        return None
    
    # Load model
    model = load_model(MODEL_FILE)
    print(f"   ✓ Đã load model: {type(model).__name__}")
    
    # Get latest row for prediction
    latest_row = df.iloc[-1:].copy()
    
    # Apply news factors if available
    if news_factors:
        print("\n   [Applying News Factors]")
        
        # Update Geo_Score
        if 'geo_score' in news_factors:
            latest_row['Geo_Score'] = news_factors['geo_score']
            latest_row['Fear_Factor'] = latest_row['VIX'] * news_factors['geo_score']
            latest_row['Fear_Factor_Change'] = (latest_row['Fear_Factor'] - 
                                                df.iloc[-2]['Fear_Factor']) / df.iloc[-2]['Fear_Factor']
            print(f"      ✓ Geo_Score updated: {news_factors['geo_score']}")
        
        # Simulate VIX change
        if 'vix' in news_factors:
            vix_new = news_factors['vix']
            vix_change = (vix_new - latest_row['VIX'].values[0]) / latest_row['VIX'].values[0]
            latest_row['VIX_Change'] = vix_change
            latest_row['VIX_Lag1'] = latest_row['VIX'].values[0]
            # Update VIX for Fear Factor
            latest_row['Fear_Factor'] = vix_new * latest_row['Geo_Score'].values[0]
            print(f"      ✓ VIX projected: {vix_new:.1f} (change: {vix_change*100:.2f}%)")
        
        # Simulate DXY change
        if 'dxy_pct' in news_factors:
            dxy_ret = news_factors['dxy_pct'] / 100
            latest_row['DXY_Ret'] = dxy_ret
            latest_row['DXY_Ret_Lag1'] = df.iloc[-1]['DXY_Ret']
            print(f"      ✓ DXY projected change: {news_factors['dxy_pct']:.2f}%")
    
    # Select features (exclude raw prices and target)
    exclude_cols = ['Gold', 'Silver', 'DXY', 'US10Y', 'TIPS', 'SP500', 
                    'VIX', 'Miners', 'Oil', 'Target_Price']
    feature_cols = [col for col in latest_row.columns if col not in exclude_cols]
    
    # Prepare input
    X_pred = latest_row[feature_cols]
    
    # Make prediction
    prediction = predict_model(model, data=X_pred, verbose=False)
    predicted_price = prediction['prediction_label'].values[0]
    
    # Current price - use manual override if provided
    if manual_current_price:
        current_price = manual_current_price
        print(f"   ℹ Using manual price: ${current_price:,.2f}")
    else:
        current_price = df['Gold'].iloc[-1]
        print(f"   ℹ Using latest data price: ${current_price:,.2f} ({df.index[-1].date()})")
    price_change = predicted_price - current_price
    price_change_pct = (price_change / current_price) * 100
    
    print(f"\n   {'='*60}")
    print(f"   📊 PREDICTION RESULTS")
    print(f"   {'='*60}")
    print(f"   Current Gold Price:    ${current_price:,.2f}")
    print(f"   Predicted Next Week:   ${predicted_price:,.2f}")
    print(f"   Expected Change:       ${price_change:+,.2f} ({price_change_pct:+.2f}%)")
    print(f"   {'='*60}")
    
    if price_change > 0:
        print(f"   📈 Outlook: BULLISH (BUY signal)")
    else:
        print(f"   📉 Outlook: BEARISH (SELL signal)")
    
    return {
        'current_price': float(current_price),
        'predicted_price': float(predicted_price),
        'change': float(price_change),
        'change_pct': float(price_change_pct),
        'data_date': df.index[-1].strftime('%Y-%m-%d'),
        'prediction_date': (df.index[-1] + pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    }

# ==========================================
# 5. VISUALIZE PREDICTION
# ==========================================
def visualize_prediction(df, prediction_result, news_factors):
    """Create visualization with prediction"""
    print("\n[5/5] Đang tạo visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Plot 1: Historical Prices with Prediction
    ax1 = axes[0, 0]
    recent_data = df['Gold'].iloc[-52:]  # Last year
    ax1.plot(recent_data.index, recent_data.values, 
            color='blue', linewidth=2, label='Historical')
    
    # Add prediction point
    pred_date = pd.to_datetime(prediction_result['prediction_date'])
    ax1.scatter([pred_date], [prediction_result['predicted_price']], 
               color='red', s=200, zorder=5, label='Prediction')
    ax1.plot([recent_data.index[-1], pred_date],
            [prediction_result['current_price'], prediction_result['predicted_price']],
            'r--', linewidth=2, alpha=0.7)
    
    ax1.set_title('Gold Price - Historical + Next Week Prediction', 
                 fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price (USD)')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Annotate prediction
    ax1.annotate(f"${prediction_result['predicted_price']:,.0f}\n({prediction_result['change_pct']:+.1f}%)",
                xy=(pred_date, prediction_result['predicted_price']),
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                fontsize=10, fontweight='bold')
    
    # Plot 2: Recent Momentum
    ax2 = axes[0, 1]
    recent_returns = df['Gold'].pct_change().iloc[-52:] * 100
    colors = ['green' if x > 0 else 'red' for x in recent_returns]
    ax2.bar(recent_returns.index, recent_returns.values, color=colors, alpha=0.6)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.set_title('Weekly Returns (Last Year)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Return (%)')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Key Indicators
    ax3 = axes[1, 0]
    indicators = df[['VIX', 'DXY', 'US10Y']].iloc[-52:]
    ax3_twin1 = ax3.twinx()
    ax3_twin2 = ax3.twinx()
    ax3_twin2.spines['right'].set_position(('outward', 60))
    
    p1, = ax3.plot(indicators.index, indicators['VIX'], 'r-', label='VIX', linewidth=2)
    p2, = ax3_twin1.plot(indicators.index, indicators['DXY'], 'b-', label='DXY', linewidth=2)
    p3, = ax3_twin2.plot(indicators.index, indicators['US10Y'], 'g-', label='US10Y', linewidth=2)
    
    ax3.set_ylabel('VIX', color='r')
    ax3_twin1.set_ylabel('DXY', color='b')
    ax3_twin2.set_ylabel('US 10Y Yield (%)', color='g')
    ax3.set_title('Market Indicators', fontsize=14, fontweight='bold')
    
    lines = [p1, p2, p3]
    ax3.legend(lines, [l.get_label() for l in lines], loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Prediction Summary Box
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary_text = f"""
    GOLD PRICE FORECAST
    {'='*50}
    
    Data as of:        {prediction_result['data_date']}
    Forecast for:      {prediction_result['prediction_date']}
    
    Current Price:     ${prediction_result['current_price']:,.2f}
    Predicted Price:   ${prediction_result['predicted_price']:,.2f}
    
    Expected Change:   ${prediction_result['change']:+,.2f}
    Percentage:        {prediction_result['change_pct']:+.2f}%
    
    {'='*50}
    """
    
    if news_factors:
        summary_text += f"""
    NEWS FACTORS APPLIED:
    - Geopolitical Score: {news_factors.get('geo_score', 'N/A')}
    - VIX Projection: {news_factors.get('vix', 'N/A')}
    - DXY Change: {news_factors.get('dxy_pct', 'N/A')}%
    - Yield Change: {news_factors.get('yield_pct', 'N/A')}%
    
    Reasoning: {news_factors.get('reasoning', 'N/A')}
    {'='*50}
        """
    
    outlook = "📈 BULLISH" if prediction_result['change'] > 0 else "📉 BEARISH"
    summary_text += f"\n    Outlook: {outlook}\n"
    
    ax4.text(0.05, 0.5, summary_text, fontsize=11, family='monospace',
            verticalalignment='center', bbox=dict(boxstyle='round', 
            facecolor='lightblue', alpha=0.3, pad=1))
    
    plt.tight_layout()
    output_file = 'gold_next_week_prediction.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"   ✓ Đã lưu visualization: '{output_file}'")
    plt.close()

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    import sys
    
    # Check for manual price argument
    manual_price = None
    if len(sys.argv) > 1:
        try:
            manual_price = float(sys.argv[1])
            print(f"\n💡 Manual price override: ${manual_price:,.2f}")
        except ValueError:
            print(f"\n⚠ Invalid price argument: {sys.argv[1]}")
    
    # 1. Load and update data
    df_raw = load_and_update_data()
    
    if not df_raw.empty:
        # 2. Create features
        df = create_advanced_features(df_raw)
        
        # 3. Load news factors (optional)
        news_factors = load_news_factors()
        
        # 4. Make prediction
        prediction_result = predict_next_week(df, news_factors, manual_price)
        
        if prediction_result:
            # 5. Visualize
            visualize_prediction(df, prediction_result, news_factors)
            
            print("\n" + "="*70)
            print("✅ HOÀN TẤT! Kiểm tra 'gold_next_week_prediction.png'")
            print("="*70)
            
            # Save prediction to JSON
            with open('latest_prediction.json', 'w') as f:
                json.dump(prediction_result, f, indent=2)
            print("\n💾 Đã lưu kết quả vào 'latest_prediction.json'")
    else:
        print("\n❌ Không thể thực hiện prediction do lỗi dữ liệu.")
