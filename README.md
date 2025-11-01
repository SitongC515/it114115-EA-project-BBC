# it114115-EA-project-BBC — BBC 風格新聞廣播服務（示範）

本專案已重新定位為「BBC 風格的新聞廣播示範平台」。它是一個基於 Flask 的示範應用，展示如何把小型 web 應用改造成新聞網站的基本構成：首頁頭條、分類頁、文章詳情、天氣小工具與讀者互動功能。

> 注意：本專案為示範/教學用途，不代表真實新聞服務。請勿在未妥善配置安全性與授權的情況下公開部署。

## 快速概覽
- 主題：新聞網站（headline / categories / article detail / comments / weather）
- 技術：Flask, SQLAlchemy, Jinja2 templates, Flask-Login, Flask-Babel
- 現有資源：`app/routes.py`（可對應新聞路由）、`app/templates/`（需調整為新聞風格）、`app/models.py`（需擴充 Article 欄位）

## 目標與對應改動建議
1. 首頁（`/`）：顯示最新新聞與 hero article，加入 breaking-news ticker。
2. 分類頁（將 `ArticleA-F` 對應 World, Business, Technology, Sport, Culture, Opinion）。
3. Article 模型：新增 `headline`, `summary`, `body`, `category`, `image_url`, `published_at`。
4. Templates：建立 partials (`_header`, `_footer`, `_news_card`)、SEO meta、社群分享按鈕。
5. `/weather`：作為 sidebar widget 被 include 在多個頁面。

## 逐步實作建議（MVP）
- Step 1：更新文字與模板的標題（把 index 改為 Latest News，ArticleA..F 改為相對應分類標題）。
- Step 2：新增 `Article` 模型與 migration，建立種子資料（`scripts/seed_news.py`）。
- Step 3：更新 templates 與 CSS，加入新聞卡片 layout 與文章詳情頁。

## 開發快速啟動
1. 建立虛擬環境並安裝依賴：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. 設定環境變數與 DB（視 `config.py`）：
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
# export DATABASE_URL=sqlite:///app.db
```
3. 執行並檢視首頁：
```bash
flask run
# 開啟 http://localhost:5000/ 查看變更
```

## 我可以替你做的三個第一步（請選一項或告訴我其他優先項）
1. 僅更新專案文件（README + rebuild-target）與路由標題文字。
2. 建立 `Article` 模型與 Alembic migration，並寫入 10 筆示例新聞。
3. 修改 `index` 與 `ArticleA-F` 的 templates（加入新聞卡片布局、hero article），並把 `/weather` 變成 sidebar include。

回覆你想先做哪一項，我就開始執行並逐步驗證。 
 
遷移計畫檔：請參考 `MOVING_TO_BBC_PLAN.md`（或搜尋「遷移計畫」）以取得詳細的逐步任務分解。
# it114115-EA-project-Chensitong