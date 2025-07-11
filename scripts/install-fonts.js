#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function installFonts(targetDir = './public/fonts') {
  const sourcePath = path.join(__dirname, '..', 'public', 'fonts');
  const destPath = path.resolve(process.cwd(), targetDir);
  
  console.log(`フォントを ${destPath} にインストール中...`);
  
  // ソースディレクトリが存在するかチェック
  if (!fs.existsSync(sourcePath)) {
    console.error(`エラー: ソースディレクトリが見つかりません: ${sourcePath}`);
    return false;
  }
  
  // ディレクトリが存在しない場合は作成
  if (!fs.existsSync(destPath)) {
    fs.mkdirSync(destPath, { recursive: true });
  }
  
  // フォントファイルをコピー
  const files = fs.readdirSync(sourcePath);
  const fontFiles = files.filter(file => 
    file.endsWith('.ttf') || 
    file.endsWith('.woff') || 
    file.endsWith('.woff2') || 
    file.endsWith('.otf')
  );
  
  if (fontFiles.length === 0) {
    console.warn('警告: フォントファイルが見つかりませんでした');
    return false;
  }
  
  fontFiles.forEach(file => {
    const sourceFile = path.join(sourcePath, file);
    const destFile = path.join(destPath, file);
    
    try {
      fs.copyFileSync(sourceFile, destFile);
      console.log(`コピー: ${file}`);
    } catch (error) {
      console.error(`エラー: ${file} のコピーに失敗しました:`, error.message);
    }
  });
  
  console.log('フォントのインストールが完了しました');
  return true;
}

// コマンドラインから直接実行された場合
if (require.main === module) {
  const targetDir = process.argv[2] || './public/fonts';
  installFonts(targetDir);
}

module.exports = { installFonts };