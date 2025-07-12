module.exports = {
  transpileDependencies: [
    '@grapecity/activereports',
    '@grapecity/activereports-vue',
    '@grapecity/ar-js-pdf'
  ],
  parallel: true,
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  outputDir: '../../docs/pdf',
  devServer: {
    port: 8080,
    hot: true,
    historyApiFallback: {
      rewrites: [
        { from: /^\/fonts\/.*$/, to: function(context) {
          return context.parsedUrl.pathname;
        }}
      ]
    },
    before(app, server, compiler) {
      const express = require('express');
      const path = require('path');
      const fs = require('fs');
      
      app.get('/fonts/*', (req, res, next) => {
        const filename = req.params[0];
        const fontsPath = path.join(__dirname, '../..', 'fonts');
        const filePath = path.join(fontsPath, filename);
        if (fs.existsSync(filePath)) {
          const realPath = fs.realpathSync(filePath);          
          if (filename.endsWith('.woff2')) {
            res.setHeader('Content-Type', 'font/woff2');
          } else if (filename.endsWith('.ttf')) {
            res.setHeader('Content-Type', 'font/ttf');
          }
          res.sendFile(realPath);
        } else {
          console.log('Font file not found:', filePath);
          res.status(404).send('Font not found');
        }
      });
    }
  },
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
    
    // CSS内のurl()解決を無効化
    config.module
      .rule('css')
      .oneOf('vue')
      .use('css-loader')
      .tap(options => {
        options.url = false;
        return options;
      })
  }
}