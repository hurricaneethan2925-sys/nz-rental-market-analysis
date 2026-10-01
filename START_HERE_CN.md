# 从这里开始

这是刚才说的新西兰租金分析个人项目，使用官方公开数据，没有使用你的课程代码。

## 第一步：解压并打开

1. 下载 ZIP，右键选择“全部解压”。不要直接在压缩包里运行。
2. 在 VS Code 里点 File → Open Folder，选择 `nz-rental-market-analysis` 文件夹。
3. 确认左边能看到 `README.md`、`requirements.txt`、`python`、`sql`、`data`。
4. 点 Terminal → New Terminal，在 PowerShell 里逐条运行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe python\analysis.py
```

如果第一行提示找不到 `py`，而你已装好 Python，可以改用 `python -m venv .venv`。

运行成功后，打开 `images` 看两张图，打开 `outputs/findings.md` 看结果。
正式数据已包含在项目中；第一次安装 pandas 和 Matplotlib 需要联网。

## 文件怎么读

- `python/analysis.py`：读取数据、检查数据、存入 SQLite、执行 SQL、画图。
- `sql/rental_analysis.sql`：真正执行的 SQL，包含 JOIN、GROUP BY、CASE、CTE、排名函数。
- `data/raw/`：官方原始数据，保留不改。
- `outputs/`：分析结果。CSV 可以用 Excel 打开。
- `images/`：可放到 GitHub README 的图。

SQLite 不需要另外安装数据库服务器，Python 自带连接功能。运行后会生成 `outputs/rental.db`。

## 三个必须理解的点

1. 同比 =（这个月的租金中位数 − 去年同月的租金中位数）÷ 去年同月的租金中位数 × 100%。
2. 不能把 12 个月的中位数简单平均后称为“年度租金中位数”。本项目保留月度指标。
3. 官方说近期数据受系统迁移影响，可能会修订；因此结果描述记录中的变化，不能直接证明市场变化的原因。

2026 年 7 月，Christchurch City 的每周租金中位数为 550 纽币，去年同月是 530，计算得到 +3.77%。这是新登记私人租约的汇总，不代表每个租客的租金都涨了 3.77%。

## 上传 GitHub

项目已做好，但还没有上传到你的 GitHub。

进入你创建的 `nz-rental-market-analysis` 仓库，使用文件上传入口，把解压后项目内的文件和文件夹上传到仓库根目录。不要再套一层同名文件夹。

上传 `README.md`、`START_HERE_CN.md`、`requirements.txt`、`.gitignore`、`data`、`python`、`sql`、`tests`、`images` 和 `outputs` 中的 CSV / MD / JSON。

不要上传 `.venv`、`__pycache__` 或 `outputs/rental.db`。数据库可以重新生成，ZIP 包里也没有放它。原始数据已注明来源和许可，可随项目保留。

如果仓库已有旧 README，用这里的新 README 替换。上传后，仓库首页应该能直接显示英文说明和两张图。

## 面试前怎么用这个项目

先亲自运行一次，再读 `clean_data` 和 SQL 的 `monthly_yoy` 视图。尝试把城市换成 Hamilton City，或改趋势图起始年份，确认自己能解释结果。

这是 AI 协助创建的第一版；简历或面试里准确说明自己做过的检查、理解和改进，不要把未掌握的部分说成独立完成。当前 README 已说明 AI 参与。
