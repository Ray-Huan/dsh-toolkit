# 列表页采集工具（scrape.py）

把网页上的列表抓成 CSV / Excel。**不装任何第三方库**（只有出 xlsx 时才用 openpyxl，没有就自动退回 CSV）。

## 三步用法

```bash
# 1. 先看结构，找出重复的 class
python scrape.py https://example.com/list --dump

# 2. 试着抓，先不写文件
python scrape.py https://example.com/list --item "div.item" \
    --field "标题=span.title" --field "价格=span.price" --field "链接=a@href"

# 3. 写文件
python scrape.py https://example.com/list --item "div.item" \
    --field "标题=span.title" --field "价格=span.price" --field "链接=a@href" \
    --out 结果.xlsx

# 翻页
python scrape.py "https://example.com/list?cat=1" --item "div.item" \
    --field "标题=span.title" --pages 5 --page-param page --delay 1 --out 结果.csv
```

## 选择器语法

| 写法 | 含义 |
|---|---|
| `div.item` | class 含 item 的 div |
| `span.price` | class 含 price 的 span |
| `a@href` | 取 a 的 href 属性 |
| `a` | 取 a 的文本 |
| `*` | 当前容器自己 |

## 参数

- `--item`：每条记录的容器
- `--field 名称=选择器`：可重复多次
- `--limit`：最多多少条
- `--pages` / `--page-param`：翻页
- `--delay`：请求间隔，默认 0.5 秒，别调太小
- `--out`：`.csv` 或 `.xlsx`
- `--dump`：只看页面结构

## 能卖的场景

- 电商列表、招聘岗位、房源、招标公告、黄页名录、公众号文章清单
- 交付：脚本 + 选择器配置 + 一份示例输出
- 报价：100–500（按站点复杂度、是否要翻页/登录/反爬）

## 边界

- 只抓公开页面；要登录的、需要破解验证码的，不接。
- 不抓个人隐私数据，不绕反爬机制。
- 默认 0.5 秒间隔，客户要求高频的先说清风险。
