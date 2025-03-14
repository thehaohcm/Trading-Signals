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
        changeOrigin: true
      },
      '/getPotentialSymbols': {
        target: 'https://trading-api-dark-sunset-2092.fly.dev',
        changeOrigin: true
      },
      '/inputOTP': {
        target: 'https://trading-api-dark-sunset-2092.fly.dev',
        changeOrigin: true
      },
      '/userTrade': {
        target: 'https://trading-api-dark-sunset-2092.fly.dev',
        changeOrigin: true
      },
      '/getUserTrade': {
        target: 'https://trading-api-dark-sunset-2092.fly.dev',
        changeOrigin: true,
        pathRewrite: {
          '^/getUserTrade': '/getUserTrade'
        }
      },
      '/updateTradingSignal': {
        target: 'https://trading-api-dark-sunset-2092.fly.dev',
        changeOrigin: true
      },
      '/api/news': {
        target: 'https://fetchrss.com',
        changeOrigin: true,
        pathRewrite: {
          '^/api/news': '/rss/67d59875033449888a001b1267d59854d0dde097270972e2.rss'
        }
      }
    }
  }
})
