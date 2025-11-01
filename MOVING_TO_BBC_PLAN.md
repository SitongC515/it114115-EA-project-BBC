# 從現有範例轉為 BBC 風格新聞網站 - 細部可執行遷移計畫

說明：本文件把 `rebuild-target` 中定義的「BBC 風格新聞廣播服務」目標拆成最小可執行任務（block-to-block），每個任務列出：目的、需要修改的檔案、必要命令、驗收條件與注意事項。採用繁體中文並盡量把每一步拆成單一改動以便 review / revert。

Use runner `run_and_update_plan.py` to verify every time
---

## 前置條件
- 你已在專案根目錄（含 `app/`）工作。
- 建議先建立虛擬環境並安裝需求：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- 確保能執行單元測試（若有）或至少能啟動 Flask：
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
```

---

## Phase 0 — 文件與小幅文字更新（非破壞性、最快上線）
目標：先把網站文字與 README 對齊，讓 repo 描述與內容一致。

  - Files: `README.md`
  - Action: 在「我可以替你做的三個第一步」上方新增一段 "遷移計畫（詳見 MOVING_TO_BBC_PLAN.md）" 並 commit。
  - Commands:
    ```bash
    git checkout -b docs/add-move-plan
    # 編輯 README.md，加入一行連結
    git add README.md
    git commit -m "docs: link MOVING_TO_BBC_PLAN.md from README"
    git push --set-upstream origin docs/add-move-plan
    ```
  - Validation: PR/commit 顯示新的連結字樣。
  - Status: ✅ 已完成

  - Tests:
- [x] `test/test_phase0.py` — Passed

  - Files: `app/routes.py`, `app/templates/index.html.j2`（或 `templates/index.html.j2`）
  - Action: 找到 index 渲染 `title=_('Home')` 的位置，改為 `title=_('Latest News')`；同時在 template 將頁首文字改成 "Latest News"。
  - Commands: 直接編輯並 commit。
  - Validation: 啟動後首頁標題顯示 "Latest News"。
  - Status: ✅ 已完成

---

## Phase 1 — 分類頁重命名與模板文案
目標：把 `ArticleA`..`ArticleF` 的路由/範本文案改為六大新聞分類。

- Task 1.1 — 路由文案更新
  - Files: `app/routes.py`
  - Action: 找到 `@app.route('/ArticleA')`.. 等函式，修改 `return render_template(..., title='ArticleA')` 為相應分類。例如：
    - `ArticleA` -> World
    - `ArticleB` -> Business
    - `ArticleC` -> Technology
    - `ArticleD` -> Sport
    - `ArticleE` -> Culture
    - `ArticleF` -> Opinion
  - Commands: 編輯並 commit。
  - Validation: 導覽到 `/World` 顯示新的標題。

  - Tests:
- [x] `test/test_phase1.py` — Passed

- Task 1.2 — template 標題與 meta 改寫
  - Files: `app/templates/ArticleA.html.j2` .. `ArticleF.html.j2`
  - Action: 更新每個檔案的頁首 `h1` 或 title，並加入一個簡單 meta description（可短暫填寫示例）。
  - Validation: 開啟對應頁面，確認標題與 meta 變更。

---

## Phase 2 — Article 模型與 DB（需謹慎，涉及 migration）
目標：新增/擴充 `Article` 模型，並用 Alembic 建 migration。

- Task 2.1 — 設計欄位並實作模型
  - Files: `app/models.py`
  - Action: 新增 `Article` 類別（範例欄位見下方程式碼塊）。只提交模型變更，勿修改 migration。 
  - Code sketch:
    ```python
    class Article(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        headline = db.Column(db.String(255), nullable=False)
        summary = db.Column(db.String(512))
        body = db.Column(db.Text)
        category = db.Column(db.String(64), index=True)
        image_url = db.Column(db.String(512))
        published_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
        author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```
  - Commands:
    ```bash
    git checkout -b feat/article-model
    # 編輯 models.py，加入 Article 類別
    git add app/models.py
    git commit -m "feat(models): add Article model"
    ```
  - Validation: Python linter / import 無錯誤 (可執行 `python -c 'from app import models'`)。

  - Tests:
- [x] `test/test_phase2.py` — Passed

- Task 2.2 — 建立 Alembic migration
  - Files: `migrations/versions/` new file
  - Action: 產生 migration 並套用（若專案已設定 Alembic）：
  - Commands:
    ```bash
    flask db migrate -m "add Article model"
    flask db upgrade
    ```
  - Notes: 若專案未啟用 Alembic，改以手動建立表或提供 SQL script。
  - Validation: `flask shell` 中 `Article.query.first()` 不會錯誤（空集合或 None 均可）。

---

## Phase 3 — Templates 與 UI 元件（中等風險）
目標：新增 partials 與新聞卡片、hero article 佈局，`/weather` 作為 sidebar include。

- Task 3.1 — 新增 partials
  - Files: `app/templates/_header.html.j2`, `_footer.html.j2`, `_news_card.html.j2`, `_weather_widget.html.j2`
  - Action: 將通用 header/footer 與新聞卡片做成 partial，並在 `base.html.j2` include。 
  - Validation: 所有頁面仍能渲染，header/footer 顯示。

- Task 3.2 — 修改 `index.html.j2` 為新聞首頁
  - Files: `app/templates/index.html.j2`
  - Action: 使用 hero article（大圖 + headline + summary）與多欄新聞卡片展示其他文章；在右側 include `_weather_widget.html.j2`。
  - Validation: 首頁顯示 hero 與多個新聞卡片，且 weather widget 顯示資料（若 DB 有 sample weather）。

  - Tests:
- [x] `test/test_phase3.py` — Passed

---

## Phase 4 — Seed data 與管理介面
目標：新增 scripts 來匯入示例新聞與提供簡易編輯介面。

- Task 4.1 — scripts/seed_news.py
  - Files: `scripts/seed_news.py`
  - Action: 撰寫小腳本讀取 JSON/CSV，並將示例 Article 寫入 DB。
  - Commands:
    ```bash
    python scripts/seed_news.py
    ```
  - Validation: `Article.query.count()` >= 種子數量。

  - Tests:
- [x] `test/test_phase4.py` — Passed

- Task 4.2 — 管理介面
  - Action: 可快速導入 `Flask-Admin` 或建立一個受保護的 route 來管理文章。

---

## Phase 5 — 部署、清理與安全（最終）

- Task 5.1 — 移除或保護 `/init_db` 路由
  - Files: `app/routes.py`
  - Action: 在 route 中檢查 `app.config['ENV'] == 'development'` 或改成 CLI；或移除此 route。 
  - Validation: 生成 prod build 時無法以 HTTP 存取該 route。

  - Tests:
- [x] `test/test_phase5.py` — Passed

- Task 5.2 — 檢查敏感值、更新 Dockerfile 與 deploy 檔
  - Files: `Dockerfile`, `deploy.sh`, `deployment.yml`, `service.yml`, `config.py`
  - Action: 確保任何憑證透過 env var 注入，並更新文件說明如何設定環境變數。

---

## 每項任務的一般驗收標準（AC）
1. 變更要能通過基本啟動（`flask run`）。
2. 模板變更不應引起 500 錯誤或模板語法錯誤。啟動後手動檢視關鍵頁面（index, category pages, article page）。
3. DB 變更應有 migration 檔並在 staging 上先驗證。

---

## 建議的最小執行順序（快速路徑）
1. Phase 0 全部任務（文字/README）
2. Phase 1 路由與 template 文案
3. Phase 3 Task 3.1 partials（以便快速改版）
4. Phase 2 Task 2.1（新增模型）
5. Phase 2 Task 2.2 migration 並套用
6. Phase 3 Task 3.2（index 改版）
7. Phase 4 seed data（驗證 UI 內容）
8. Phase 5 部署與安全檢查
