module.exports = {
  transpileDependencies: [
    '@grapecity/activereports',
    '@grapecity/activereports-vue',
    '@grapecity/ar-js-pdf'
  ],
  parallel: true,
  configureWebpack: {
    optimization: {
      splitChunks: {
        cacheGroups: {
          default: false,
          vendors: false,
          vendor: {
            name: 'vendors',
            chunks: 'all',
            test: /node_modules/
          }
        }
      }
    }
  },
  chainWebpack: config => {
    config.module
      .rule('babel')
      .test(/\.js$/)
      .include.add(/node_modules\/@grapecity\/ar-js-pdf/)
      .end()
      .use('babel-loader')
      .loader('babel-loader')
      .options({
        compact: true,
        presets: [
          ['@babel/preset-env', {
            targets: {
              browsers: ['> 1%', 'last 2 versions']
            }
          }]
        ]
      })
  }
}