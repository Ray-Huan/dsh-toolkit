# 文件整理工具（organize.py）

一个不用装任何依赖的小工具：把乱七八糟的文件夹按类型或日期分好，**默认只试运行**，加了 `--apply` 才真的动，动完能一键撤销。

## 为什么有人愿意付钱

大多数人的「下载」「桌面」「微信文件」文件夹里堆着几百个文件，手动拖一晚上。这个脚本 10 秒搞定，而且撤销有记录，不怕搞坏。

## 怎么用

```bash
python organize.py D:\Downloads              # 先看计划，不动文件
python organize.py D:\Downloads --apply      # 真整理
python organize.py D:\Downloads --by date --apply   # 按年月分
python organize.py D:\Downloads --undo       # 撤销上一次
```

## 行为说明

- 分类：图片 / 视频 / 音频 / 文档 / 压缩包 / 安装包 / 代码 / 其他
- 重名自动加 `(1)`、`(2)`，不覆盖任何文件
- 跳过隐藏文件和已经分好的目录
- 每次整理写 `organize_undo.json`，撤销后自动清理空目录
- Windows / macOS / Linux 都能跑，只要 Python 3.8+

## 可以直接当交付

- 交付物：`organize.py` + 这份说明
- 报价：50–150（按目录规模和是否要定制规则）
- 定制点：按项目名分类、按大小分、只处理指定后缀、加定时任务
