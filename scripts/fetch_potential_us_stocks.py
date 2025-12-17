from finvizfinance.screener.overview import Overview

# Sử dụng mã bộ lọc của Finviz. 
# "ta_changeopen" không trực tiếp, nhưng Finviz có bộ lọc "52-Week High/Low".
# Signal: 'New High' hoặc custom filters.
# Cách tốt nhất: Dùng filters dict
foverview = Overview()

# Bộ lọc: Index = S&P 500, 52-Week High = 0-10% below High
filters_dict = {
    'Index': 'S&P 500', 
    '52-Week High/Low': '0-10% below High' 
}
foverview.set_filter(filters_dict=filters_dict)
df = foverview.screener_view()

# Sau đó bạn có thể lọc tiếp trong DataFrame để lấy chính xác mức 5%
print(df.head())