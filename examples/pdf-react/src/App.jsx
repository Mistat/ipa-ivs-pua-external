import React, { useState, useEffect } from 'react';
import { generate } from '@pdfme/generator';
import { BLANK_A4_PDF } from '@pdfme/common';
import { convertIVSToExternal, hasIVSCharacters, countIVSCharacters, getIVSCharacterDetails } from 'ivs-font-processor';
import './App.css';

const App = () => {
  const [textValue, setTextValue] = useState('\u6AC2\uDB40\uDD01 \u7027\uDB40\uDD07 \u6406\uDB40\uDD03 \u3404\uDB40\uDD00 - \u3404\uDB40\uDD01 - \u3404\uDB40\uDD02 - \u3732\udb40\udd01 - \u4672\udb40\udd00');
  const [fonts, setFonts] = useState({});

  // フォントを読み込み
  useEffect(() => {
    const loadFonts = async () => {
      try {
        // IPA明朝フォント
        const ipaResponse = await fetch('./fonts/ipam.ttf');
        const ipaBuffer = await ipaResponse.arrayBuffer();
        
        // IVS外字フォント
        const ivsResponse = await fetch('./fonts/ipa-ivs-external.ttf');
        const ivsBuffer = await ivsResponse.arrayBuffer();
        
        setFonts({
          'IPA明朝': {
            data: ipaBuffer,
            fallback: true,
          },
          'IPA-IVS-External': {
            data: ivsBuffer
          }
        });
        
        console.log('フォント読み込み完了');
      } catch (error) {
        console.error('フォント読み込みエラー:', error);
      }
    };
    
    loadFonts();
  }, []);

  // 計算されたプロパティ（Vueのcomputed相当）
  const displayText = convertIVSToExternal(textValue);
  const hasIVS = hasIVSCharacters(textValue);
  const ivsCount = countIVSCharacters(textValue);
  const ivsDetails = getIVSCharacterDetails(textValue);

  const generatePDF = async () => {
    try {
      if (Object.keys(fonts).length === 0) {
        alert('フォントがまだ読み込まれていません。しばらくお待ちください。');
        return;
      }
      // 変換されたテキストを確認
      const convertedText = convertIVSToExternal(textValue) || "（未入力）";
      console.log('元のテキスト:', textValue);
      console.log('変換後のテキスト:', convertedText);

      // PDFテンプレート定義（pdfme v4形式）
      const template = {
        basePdf: BLANK_A4_PDF,
        schemas: [
          {
            title: {
              type: 'text',
              position: { x: 50, y: 50 },
              width: 100,
              height: 10,
              fontSize: 24,
              fontName: 'IPA明朝',
              fontColor: '#000000'
            },
            nomalText: {
              type: 'text',
              position: { x: 50, y: 70 },
              width: 100,
              height: 15,
              fontSize: 18,
              fontName: 'IPA明朝',
              fontColor: '#000000'
            },
            puaText: {
              type: 'text',
              position: { x: 50, y: 80 },
              width: 100,
              height: 15,
              fontSize: 18,
              fontName: 'IPA-IVS-External',
              fontColor: '#000000'
            }
          }
        ]
      };

      // 入力データ
      const inputs = [
        {
          title: 'Hello from React + pdfme',
          nomalText: 'ISV:'+ textValue,
          puaText: 'PUA:' + convertedText,
        }
      ];

      // PDF生成（pdfme v5形式）
      const pdf = await generate({
        template,
        inputs,
        options: {
          font: fonts
        }
      });

      // ダウンロード
      const blob = new Blob([pdf], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'ivs-react-example.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('PDF生成エラー:', error);
      alert('PDF生成中にエラーが発生しました。');
    }
  };

  return (
    <div className="app">
      <h1>IVS Font Processor - React + pdfme Example</h1>
      
      <div className="input-section">
        <input
          type="text"
          value={textValue}
          onChange={(e) => setTextValue(e.target.value)}
          placeholder="テキストを入力してください（IVS文字対応）"
          className="text-input"
        />
      </div>

      {textValue && (
        <div className="preview">
          <div className="preview-label">プレビュー（変換後）:</div>
          <div className="preview-text">{displayText}</div>
          
          {hasIVS && (
            <div className="ivs-info">
              <div className="ivs-summary">
                <strong>🔄 IVS文字が{ivsCount}文字検出されました</strong>
              </div>
              <div className="ivs-details">
                {ivsDetails.map((detail, index) => (
                  <div key={index} className="ivs-detail-item">
                    <div className="char-display">
                      <span className="ivs-char">{detail.ivs}</span>
                      <span className="char-code">{detail.ivsCode}</span>
                    </div>
                    <span className="arrow">→</span>
                    <div className="char-display">
                      <span className="external-char">{detail.external}</span>
                      <span className="char-code">{detail.externalCode}</span>
                    </div>
                    <span className="count">({detail.count}個)</span>
                  </div>
                ))}
              </div>
              <small className="ivs-note">PDF生成時に外字フォントで表示されます。</small>
            </div>
          )}
        </div>
      )}

      <button onClick={generatePDF} className="generate-btn">
        PDF生成 (pdfme)
      </button>
    </div>
  );
};

export default App;