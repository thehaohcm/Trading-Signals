const { defineConfig } = require('@vue/cli-service')

// Dev-server proxy targets. Override with DEV_API_TARGET / DEV_VPS_API_TARGET (e.g. in .env.local).
const API_TARGET = process.env.DEV_API_TARGET || 'https://trading-api-dark-sunset-2092.fly.dev'
const VPS_API_TARGET = process.env.DEV_VPS_API_TARGET || 'http://152.53.208.182:8080'

module.exports = defineConfig({
  transpileDependencies: true,
  productionSourceMap: false,
  parallel: false,
  lintOnSave: false,
  configureWebpack: {
    cache: false,
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
      '/api/chat': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/settings': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/trading-settings': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/trading': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/economic-calendar': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/take-notes': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/take-notes': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/asset-signals': {
        target: VPS_API_TARGET,
        changeOrigin: true
      },
      '/api/osint': {
        target: VPS_API_TARGET,
        changeOrigin: true
      },
      '/static/podcasts': {
        target: VPS_API_TARGET,
        changeOrigin: true
      },
      '/api/rates': {
        target: 'https://live-rates.com/rates',
        changeOrigin: true,
        pathRewrite: {
          '^/api/rates': ''
        }
      },
      '/api/currency-prices': {
        target: 'https://live-rates.com/rates',
        changeOrigin: true,
        pathRewrite: {
          '^/api/currency-prices': ''
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
        target: API_TARGET,
        changeOrigin: true,
        pathRewrite: {
          '^/world': ''
        }
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
        target: API_TARGET,
        changeOrigin: true
      },
      '/runSSHScript': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/getPotentialCoins': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/getPotentialFuturesCoins': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/getPotentialForexPairs': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/getRealEstate': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/inputOTP': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/community': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/journal': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/api/news/telegram': {
        target: VPS_API_TARGET,
        changeOrigin: true
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
      '/petrolimex/search': {
        target: 'https://portals.petrolimex.com.vn',
        changeOrigin: true,
        pathRewrite: {
          '^/petrolimex/search': '/~apis/portals/cms.item/search?object-identity=search&x-request=eyJGaWx0ZXJCeSI6eyJBbmQiOlt7IlN5c3RlbUlEIjp7IkVxdWFscyI6IjY3ODNkYzEyNzFmZjQ0OWU5NWI3NGE5NTIwOTY0MTY5In19LHsiUmVwb3NpdG9yeUlEIjp7IkVxdWFscyI6ImE5NTQ1MWUyM2I0NzRmZTU4ODZiZmI3Y2Y4NDNmNTNjIn19LHsiUmVwb3NpdG9yeUVudGl0eUlEIjp7IkVxdWFscyI6IjM4MDEzNzhmZTFlMDQ1YjFhZmExMGRlN2M1Nzc2MTI0In19LHsiU3RhdHVzIjp7IkVxdWFscyI6IlB1Ymxpc2hlZCJ9fV19LCJTb3J0QnkiOnsiTGFzdE1vZGlmaWVkIjoiRGVzY2VuZGluZyJ9LCJQYWdpbmF0aW9uIjp7IlRvdGFsUmVjb3JkcyI6LTEsIlRvdGFsUGFnZXMiOjAsIlBhZ2VTaXplIjowLCJQYWdlTnVtYmVyIjowfX0='
        }
      },
      '/yahoo-finance': {
        target: 'https://query1.finance.yahoo.com',
        changeOrigin: true,
        pathRewrite: {
          '^/yahoo-finance': ''
        }
      },
      '/cryto_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/cryto_rrgchart': '/crypto_rrgchart.png'
        }
      },
      '/futures_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/futures_rrgchart': '/futures_rrgchart.png'
        }
      },
      '/vnstock_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/vnstock_rrgchart': '/vnstock_rrgchart.png'
        }
      },
      '/assets_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/assets_rrgchart': '/assets_rrgchart.png'
        }
      },

      '/breakout': {
        target: API_TARGET,
        changeOrigin: true
      },
      '/forex_rrgchart': {
        target: 'https://thehaohcm.alwaysdata.net',
        changeOrigin: true,
        pathRewrite: {
          '^/forex_rrgchart': '/forex_rrgchart.png'
        }
      },
      '/': {
        target: 'https://services.entrade.com.vn',
        changeOrigin: true
      }
    }
  }
})