const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/tcanalysis': {
        target: 'https://apipubaws.tcbs.com.vn',
        changeOrigin: true,
        pathRewrite: {
          '^/tcanalysis': '/tcanalysis'
        }
      }
    }
  }
})
