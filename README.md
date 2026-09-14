# 艾宾浩斯 单词抗遗忘

KET / PET / 人教版 PEP（3–9 年级）词汇学习页：按主题或单元分组、单词听读，以及艾宾浩斯默写纸打印。

**在线使用：** [https://xiaoyyuchen.github.io/EbbWords/](https://xiaoyyuchen.github.io/EbbWords/)

**开源仓库：** [https://github.com/XiaoyYuChen/EbbWords](https://github.com/XiaoyYuChen/EbbWords)

本地打开 `index.html` 也可使用。搜索支持 `*`（任意字符）和 `_`（单个字符）。可在当前主题里选择 5–10 个单词后，用「顺序选」按列表分段勾选，或用「随机选」每次抽一批。

## 词库

- **KET**：剑桥 KET 高频词，按生活场景主题筛选。
- **PET**：剑桥 PET / B1 Preliminary 词汇表，同样按主题筛选。
- **PEP**：人教版英语 3–9 年级，按 Unit 单元筛选。
  - 三年级：PEP 2024 新教材单元词汇（课本同步）
  - 四至六年级：PEP 三年级起点各册单元词汇总表
  - 七至九年级：人教版新目标（Go for it）各册单元词汇总表

词库源文件为统一 JSON，放在 `data/books/`。每条单词字段为：

```json
{ "w": "apple", "p": "n", "i": "ˈæpl", "c": "苹果", "t": "food" }
```

`w` 单词，`p` 词性，`i` 音标，`c` 中文，`t` 主题或单元 id。修改 JSON 后运行 `python build.py` 即可重新生成页面。从原始资料重建词库（并补全 PEP 词性）可用 `python build.py --from-raw`。

## 一起完善

Token 有富裕的同学，欢迎帮我扩展 **FCE 词汇**、**句型** 等。直接在仓库提 Issue 或 Pull Request 即可。

## 作者

**陈晓雨**

微信二维码：

<img src="assets/wechat-qr.jpg" alt="陈晓雨微信二维码" width="240" />

打赏码：

<img src="assets/donate-qr.jpg" alt="陈晓雨打赏码" width="320" />

## 特别鸣谢

感谢 **@点点爸爸** 提供 KET 资料。

感谢 **@王昳臻妈妈** 提供的建议：添加英语课本后边的单词。

## 开源协议

本项目采用 [Apache License 2.0](LICENSE)。
