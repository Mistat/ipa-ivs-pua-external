<template>
  <div id="app">
    <h1>Hello</h1>
    <input type="text" v-model="textValue" placeholder="テキストを入力してください" />
    <button @click="generatePDF">PDF生成</button>
  </div>
</template>

<script>
import { Core, PdfExport, XlsxExport } from '@grapecity/activereports'

export default {
  name: 'App',
  data() {
    return {
      textValue: ''
    }
  },
  methods: {
    async generatePDF() {
      try {
        // フォントの登録
        const fontUrl = require('./assets/fonts/ipam.ttf')
        const ipaFont = {
          name: "IPA明朝",
          source: fontUrl
        }
        await Core.FontStore.registerFonts(ipaFont)
        
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
                Value: this.textValue || "（未入力）",
                Style: {
                  FontFamily: "IPA明朝",
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
  src: url('./assets/fonts/ipam.ttf') format('truetype');
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
</style>
