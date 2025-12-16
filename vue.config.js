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
       '/api': {
        target: 'https://live-rates.com',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '' // Remove /api prefix
        }
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
      '/getPotentialCoins': {
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
        target: 'https://rsshub.app',
        changeOrigin: true,
        pathRewrite: {
          '^/api/news': 'telegram/channel/ktnews24'
        }
      },
      '/ff_calendar_thisweek.json': {
        target: 'https://nfs.faireconomy.media',
        changeOrigin: true,
        pathRewrite: {
          '^/ff_calendar_thisweek.json': '/ff_calendar_thisweek.json'
        }
      },
      '/goldprice': {
        target: 'https://sjc.com.vn',
        changeOrigin: true,
        pathRewrite: {
          '^/goldprice': '/GoldPrice'
        }
      }
    }
  }
})
