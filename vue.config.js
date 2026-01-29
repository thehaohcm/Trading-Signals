const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: config => {
    // Ensure all JS files are transpiled for iOS Safari
    config.module
      .rule('js')
      .test(/\.js$/)
      .use('babel-loader')
      .loader('babel-loader')
      .options({
        presets: [
          ['@babel/preset-env', {
            targets: {
              ios: '12',
              safari: '12'
            }
          }]
        ]
      })
  },
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
      '/cg': {
        target: 'https://api.coingecko.com',
        changeOrigin: true,
        pathRewrite: {
          '^/cg': ''
        }
      },
      '/world': {
        target: 'https://trading-api-dark-sunset-2092.fly.dev',
        changeOrigin: true,
        pathRewrite: {
          '^/world': ''
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
      '/getPotentialForexPairs': {
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
        target: 'https://rsshub.rssforever.com',
        changeOrigin: true,
        pathRewrite: {
          '^/api/news': 'telegram/channel/vnwallstreet'
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
      },
      '/silverprice': {
        target: 'https://giabac.phuquygroup.vn',
        changeOrigin: true,
        pathRewrite: {
          '^/silverprice': '/PhuQuyPrice'
        }
      },
      '/cryto_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/cryto_rrgchart': '/crypto_rrgchart.png'
        }
      },
      '/vnstock_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/vnstock_rrgchart': '/vnstock_rrgchart.png'
        }
      }
    }
  }
})
