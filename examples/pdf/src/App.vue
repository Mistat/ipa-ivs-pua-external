<template>
  <div id="app">
    <h1>Hello</h1>
    <input type="text" v-model="textValue" placeholder="テキストを入力してください（IVS文字対応）" />
    <div class="preview" v-if="textValue">
      <div class="preview-label">プレビュー（変換後）:</div>
      <div class="preview-text">{{ displayText }}</div>
      <div class="ivs-info" v-if="hasIVS">
        <div class="ivs-summary">
          <strong>🔄 IVS文字が{{ ivsCount }}文字検出されました</strong>
        </div>
        <div class="ivs-details">
          <div v-for="detail in ivsDetails" :key="detail.external" class="ivs-detail-item">
            <div class="char-display">
              <span class="ivs-char">{{ detail.ivs }}</span> 
              <span class="char-code">{{ detail.ivsCode }}</span>
            </div>
            <span class="arrow">→</span>
            <div class="char-display">
              <span class="external-char">{{ detail.external }}</span>
              <span class="char-code">{{ detail.externalCode }}</span>
            </div>
            <span class="count">({{ detail.count }}個)</span>
          </div>
        </div>
        <small class="ivs-note">PDF生成時に外字フォントで表示されます。</small>
      </div>
    </div>
    <button @click="generatePDF">PDF生成</button>
  </div>
</template>

<script>
import { Core, PdfExport, XlsxExport } from '@grapecity/activereports'
import { convertIVSToExternal, hasIVSCharacters, countIVSCharacters, getIVSCharacterDetails } from 'ivs-font-processor'

export default {
  name: 'App',
  data() {
    return {
      textValue:  '\u6AC2\uDB40\uDD01 \u7027\uDB40\uDD07 \u6406\uDB40\uDD03 \u3404\uDB40\uDD00 - \u3404\uDB40\uDD01 - \u3404\uDB40\uDD02 - \u3732\udb40\udd01 - \u4672\udb40\udd00'
    }
  },
  computed: {
    displayText() {
      return convertIVSToExternal(this.textValue)
    },
    hasIVS() {
      return hasIVSCharacters(this.textValue)
    },
    ivsCount() {
      return countIVSCharacters(this.textValue)
    },
    ivsDetails() {
      return getIVSCharacterDetails(this.textValue)
    }
  },
  methods: {
    async generatePDF() {
      try {
        // フォントの登録（相対パス）
        const ipaFont = {
          name: "IPA明朝",
          source: "./fonts/ipam.ttf"
        }
        await Core.FontStore.registerFonts(ipaFont)
        console.log('IPA明朝フォント登録完了')
        
        // IVS外字フォントの登録（相対パス）
        const ivsExternalFont = {
          name: "IPA-IVS-External",
          source: "./fonts/ipa-ivs-external.ttf"
        }
        await Core.FontStore.registerFonts(ivsExternalFont)
        console.log('IVS外字フォント登録完了')
        
        // 登録されたフォントの確認
        const registeredFonts = Core.FontStore.getFonts()
        console.log('登録されたフォント:', registeredFonts)
        
        // 変換されたテキストを確認
        const convertedText = convertIVSToExternal(this.textValue) || "（未入力）"
        console.log('元のテキスト:', this.textValue)
        console.log('変換後のテキスト:', convertedText)
        console.log('変換後の文字コード:', Array.from(convertedText).map(c => `U+${c.codePointAt(0).toString(16).toUpperCase()}`))
        
        // レポート定義を作成
        const reportDef = {
          Type: "report",
          Version: "17.1.0.0",
          Name: "HelloReport",
          Body: {
            ReportItems: [
              {
                Type: "textbox",
                Name: "HelloTextBox",
                Value: "Hello",
                Style: {
                  FontFamily: "IPA明朝",
                  FontSize: "24pt",
                  Color: "#000000",
                  TextAlign: "Center"
                },
                Top: "1in",
                Left: "2in",
                Width: "4in",
                Height: "0.5in"
              },
              {
                Type: "textbox",
                Name: "UserInputTextBox",
                Value: convertedText,
                Style: {
                  FontFamily: "IPA-IVS-External",
                  FontSize: "18pt",
                  Color: "#000000",
                  TextAlign: "Center"
                },
                Top: "2in",
                Left: "2in",
                Width: "4in",
                Height: "0.5in"
              }
            ]
          },
          PageSettings: {
            Size: {
              Width: "8.27in",
              Height: "11.69in"
            },
            Margins: {
              Top: "1in",
              Bottom: "1in",
              Left: "1in",
              Right: "1in"
            }
          }
        }

        // レポートを実行
        const report = new Core.PageReport()
        await report.load(reportDef)
        const document = await report.run()
        
        // PDFエクスポート
 	const result = await PdfExport.exportDocument(document)
        
        // ダウンロード
        this.downloadPDF(result.data, 'hello-report.pdf')
        
      } catch (error) {
        console.error('PDF生成エラー:', error)
        alert('PDF生成中にエラーが発生しました。')
      }
    },
    
    downloadPDF(data, filename) {
      const blob = new Blob([data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }
  }
}
</script>

<style>
@font-face {
  font-family: 'IPA明朝';
  src: url('./fonts/ipam.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
}

@font-face {
  font-family: 'IPA-IVS-External';
  src: url('./fonts/ipa-ivs-external.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
}

#app {
  font-family: 'IPA明朝', serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

input {
  font-family: 'IPA明朝', serif;
  font-size: 16px;
  padding: 8px;
  margin-top: 20px;
}

button {
  font-family: 'IPA明朝', serif;
  font-size: 16px;
  padding: 10px 20px;
  margin-top: 20px;
  background-color: #42b883;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

button:hover {
  background-color: #369870;
}

.preview {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.preview-label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #2c3e50;
}

.preview-text {
  font-family: 'IPA-IVS-External', 'IPA明朝', serif;
  font-size: 18px;
  padding: 10px;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 3px;
  margin-bottom: 10px;
}

.ivs-info {
  color: #42b883;
  background-color: #f0f9ff;
  border: 1px solid #42b883;
  border-radius: 4px;
  padding: 10px;
  margin-top: 10px;
}

.ivs-summary {
  margin-bottom: 8px;
}

.ivs-details {
  margin: 8px 0;
}

.ivs-detail-item {
  display: flex;
  align-items: center;
  margin: 6px 0;
  font-family: 'IPA-IVS-External', 'IPA明朝', monospace;
}

.char-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 8px;
}

.ivs-char {
  background-color: #fff3cd;
  padding: 4px 6px;
  border-radius: 3px;
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 2px;
}

.external-char {
  background-color: #d1ecf1;
  padding: 4px 6px;
  border-radius: 3px;
  font-family: 'IPA-IVS-External', monospace;
  font-size: 18px;
  margin-bottom: 2px;
}

.char-code {
  font-size: 10px;
  color: #666;
  font-family: monospace;
  text-align: center;
}

.arrow {
  font-size: 16px;
  color: #666;
  margin: 0 4px;
}

.count {
  font-size: 0.9em;
  color: #666;
}

.ivs-note {
  display: block;
  margin-top: 8px;
  font-style: italic;
  color: #666;
}
</style>
