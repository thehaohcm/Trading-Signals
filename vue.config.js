const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    historyApiFallback: true,
    proxy: {
      '/tcanalysis/v1/evaluation': {
        target: 'https://apipubaws.tcbs.com.vn',
        changeOrigin: true,
        pathRewrite: {
          '^/tcanalysis/v1/evaluation': '/tcanalysis/v1/evaluation'
        }
      },
      '/tcanalysis/v1/ticker': {
        target: 'https://apipubaws.tcbs.com.vn',
        changeOrigin: true
      },
      '/stock-insight/v2/stock/bars-long-term': {
        target: 'https://apipubaws.tcbs.com.vn',
        changeOrigin: true
      },
      '/': {
        target: 'https://services.entrade.com.vn',
        changeOrigin: true
      },
      '/v4': {
        target: 'https://api-finfo.vndirect.com.vn',
        changeOrigin: true
      },
      '/dnse-user-service': {
        target: 'https://services.entrade.com.vn',
        changeOrigin: true
      },
      '/dnse-auth-service': {
        target: 'https://services.entrade.com.vn',
        changeOrigin: true
      },
       '/dnse-order-service': {
        target: 'https://services.entrade.com.vn',
        changeOrigin: true,
        headers: {
          "Referrer-Policy": "same-origin"
        },
        onProxyRes: function (proxyRes, req, res) {
          proxyRes.headers['Access-Control-Allow-Origin'] = '*';
          proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
          proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Trading-Token, smart-otp';
        }
      }
    }
  }
})
