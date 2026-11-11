# 添加「短文」列表模块

## Summary

在现有 EbbWords 静态站点中新增一个独立的「短文」分区，作为与 KET/PET/PEP/我的词库 平行的模块（但通过独立导航入口进入，不混入 libbar）。短文内容来源于本地 `D:\AIProjects\MEEProcess\Audios\{NN}.{Title}\Kai\{NN}.{Title}.txt`（共 36 篇纯英文短文）。短文正文中的每个单词可点击，弹出与现有 PEP 单词一致的详情弹窗（音标、翻译、例句）；短文下方再列一份「单词列表」，同样可点击查看。详情弹窗新增「加入默写纸」按钮，复用现有 `state.selected` / 默写纸生成流程。

未收录单词（不在任何词库中的生词）的音标和翻译，由 `build.py` 在构建时调用有道词典 Python API（服务端无 CORS 限制）抓取并缓存到 `data/passage_words.json`，每次新增短文 rebuild 时自动补全缺失的生词。

---

## Current State Analysis

- 静态站点：`template.html`（源）→ `build.py` 注入 `window.EBB` JSON → `index.html`（产出）
- 现有模块切换：`renderLibbar` ([template.html:2240](file:///d:/AIProjects/EbbWords/template.html#L2240)) 渲染 KET/PET/PEP/我的词库 标签；`state.lib` 控制当前库
- `state.selected` (Map) ([template.html:676](file:///d:/AIProjects/EbbWords/template.html#L676))：默写纸选词状态，`toggleSelect` ([template.html:2398](file:///d:/AIProjects/EbbWords/template.html#L2398)) 切换；上限 300，默写纸取前 10
- 单词详情弹窗 `#wmodal` ([template.html:428-446](file:///d:/AIProjects/EbbWords/template.html#L428))：仅含「关闭」按钮，无加入默写纸入口
- `openWordModal(w)` ([template.html:1405](file:///d:/AIProjects/EbbWords/template.html#L1405))：期望 `w` 形如 `{w,p,i,c,e,z}`
- 无词典 API 调用：现有代码仅有 Youdao TTS（音频）URL，缺失音标/翻译时显示空 / "（无释义）"
- `build.py` `write_html` ([build.py:946](file:///d:/AIProjects/EbbWords/build.py#L946))：组装 `payload = {libs:{ket,pet}, pep:{...}}` 后注入模板
- `data/books/*.json`：每本书结构 `{id,name,short,kind,groups:[...],words:[{w,p,i,c,t,e,z}]}`
- `D:\AIProjects\MEEProcess\Audios` 共 36 个 `NN.Title` 文件夹，每个含 `Kai/*.txt`（纯英文，一行一句）
- `data/pdf_examples.json`、`data/pep_examples.json`：未接入的遗留素材，**不**用于本计划（避免无关改动）

### 用户已确认的关键决策

1. **生词数据源**：构建时 Python 脚本调用词典 API 抓取，缓存到 `data/passage_words.json`，rebuild 时自动补全
2. **UI 位置**：独立分区/页面，不混入 libbar

---

## Proposed Changes

### 1. `build.py` — 新增短文加载与生词抓取

**位置**：[build.py](file:///d:/AIProjects/EbbWords/build.py)

**新增常量**（顶部，与 `ROOT`/`BOOKS` 并列，约 line 14 后）：

```python
AUDIOS = Path(r"D:\AIProjects\MEEProcess\Audios")
PASSAGE_WORDS_JSON = ROOT / "data" / "passage_words.json"
```

**新增函数 `load_passages()`**：
- 用 `AUDIOS.glob("*/Kai/*.txt")` 扫描所有 Kai 下的 .txt（按文件名前缀数字排序）
- 对每个 .txt：读取内容，按行拆成句子数组，剥掉行号前缀（若有）
- 用正则 `[A-Za-z]+(?:'[a-z]+)?` 提取所有单词 token，去重、小写、过滤掉常见停用词（a/an/the/is/are/was/were/and/or/but/to/of/in/on/at/for/with/by/from/it/he/she/they/we/i/you/my/your/his/her/their/our/this/that/these/those/me/him/us/them/as/so/do/does/did/be/been/being/have/has/had/will/would/can/could/should/may/might/must/not/no/yes/very/just/too/then/than/if/when/where/why/how/what/which/who/whom/while/again/here/there/up/down/out/over/under/after/before/now）
- 返回 `[{id, title, lines:[...], words:["today","wake",...]}, ...]`

**新增函数 `fetch_unknown_passage_words(passage_word_set, known_word_set)`**：
- 计算 `passage_word_set - known_word_set`（known 来自所有 books 的 `w` 字段，去重小写）
- 读 `data/passage_words.json`（若存在），已缓存的直接复用
- 对未缓存的生词，调用 `https://dict.youdao.com/jsonapi?q={word}&le=eng` 或使用 `requests.get("https://fanyi.youdao.com/openapi.do", params={...})`（如有可用 key），解析返回的 `phonetic`、`translation` 字段
- 备选：若 Youdao API 需要密钥且不可用，使用 `https://dictionaryapi.dev/api/v2/entries/en/{word}`（无需密钥，返回 JSON，含 `phonetics[].text` 音标、`meanings[].definitions[].definition` 英文释义）+ 简单词频表补中文；或在 `data/passage_words.json` 中手动维护
- 每个单词解析后写入缓存：`{word: {w, i: 音标, c: 中文翻译, p: 词性}}`，写回 `data/passage_words.json`
- 返回完整 `passage_words_map`（dict: 小写单词 → word obj）

**修改 `write_html(ket_book, pet_book, pep_books)`**（[build.py:946](file:///d:/AIProjects/EbbWords/build.py#L946)）：
- 在组装 payload 前，调用 `load_passages()` 与 `fetch_unknown_passage_words(...)`
- payload 新增 `passages` 字段：
  ```python
  payload = {
      "libs": {"ket": ket_book, "pet": pet_book},
      "pep": pep_map,
      "passages": {
          "items": passage_list,   # [{id,title,lines,words}]
          "wordMap": passage_words_map  # {"today": {w,i,c,p}, ...}
      },
  }
  ```
- 打印日志：`passages=N unknown_words=M cached=K fetched=L`

**为什么 Python 抓取而非浏览器 API**：静态站点无后端，浏览器侧 Youdao/百度词典 API 不支持 CORS；Python 服务端无此限制，且可缓存到本地 JSON，rebuild 时增量补全。

### 2. `template.html` — 新增短文分区 UI 与导航入口

#### 2.1 顶部导航新增「短文」入口

**位置**：header `.libbar` 同级，[template.html:348](file:///d:/AIProjects/EbbWords/template.html#L348) 附近

在 `.libbar` 后新增一个独立的导航按钮区域（不参与 libbar 的 lib 切换）：

```html
<div class="passagebar" id="passagebar">
  <button type="button" class="btn ghost" id="btnPassages" data-view="passages">短文</button>
  <button type="button" class="btn ghost" id="btnWords" data-view="words" hidden>返回单词</button>
</div>
```

逻辑：点击「短文」进入短文列表视图，隐藏 `.libbar`/`.pepbar`/`.mybar`/`.chips-wrap`/`.dock`，显示短文视图；点击「返回单词」切回原词库视图。

#### 2.2 新增短文视图容器

**位置**：`<main>` 内，[template.html:380-383](file:///d:/AIProjects/EbbWords/template.html#L380) 后

```html
<div class="passage-view" id="passageView" hidden>
  <div class="passage-list-wrap" id="passageListWrap">
    <h2>短文列表</h2>
    <div class="passage-list" id="passageList"></div>
  </div>
  <div class="passage-detail-wrap" id="passageDetailWrap" hidden>
    <button class="btn ghost sm" id="btnPassageBack">← 返回列表</button>
    <h2 id="passageTitle"></h2>
    <div class="passage-body" id="passageBody"></div>
    <div class="wsec" style="margin-top:24px">单词列表</div>
    <div class="passage-words" id="passageWords"></div>
  </div>
</div>
```

#### 2.3 详情弹窗 `#wmodal` 新增「加入默写纸」按钮

**位置**：[template.html:442-444](file:///d:/AIProjects/EbbWords/template.html#L442)

```html
<div class="wbtns">
  <button class="btn ghost" id="wClose">关闭</button>
  <button class="btn primary" id="wAddSheet" hidden>加入默写纸</button>
</div>
```

按钮默认 hidden，进入短文模块或从短文单词列表打开时显示；从 PEP/KET 等主词库打开时维持现有逻辑（已可从 grid 卡片加入选词，故可继续隐藏，避免重复入口）—— 简化起见，统一显示「加入默写纸」按钮，对所有入口可用。

#### 2.4 新增样式

**位置**：模板 `<style>` 区块末尾（需先 grep 确认位置）

```css
.passagebar { padding: 8px 0; border-bottom: 1px solid #e2e8f0; }
.passage-view { padding: 16px 0; }
.passage-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.passage-card { padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; background: #fff; }
.passage-card:hover { border-color: #3182ce; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.passage-card .pnum { color: #718096; font-size: 12px; }
.passage-card .ptitle { font-weight: 600; margin-top: 4px; }
.passage-card .pwords { color: #a0aec0; font-size: 12px; margin-top: 8px; }
.passage-body { font-size: 18px; line-height: 1.9; padding: 16px; background: #f7fafc; border-radius: 8px; }
.passage-body .pw { cursor: pointer; border-bottom: 1px dashed #cbd5e0; }
.passage-body .pw:hover { color: #3182ce; border-color: #3182ce; }
.passage-words { display: flex; flex-wrap: wrap; gap: 8px; }
.passage-word-chip { padding: 6px 12px; border: 1px solid #e2e8f0; border-radius: 16px; cursor: pointer; background: #fff; }
.passage-word-chip:hover { border-color: #3182ce; color: #3182ce; }
.passage-word-chip.unknown { border-style: dashed; color: #c05621; }
```

### 3. `template.html` — 新增短文 JS 逻辑

**位置**：模板 `<script>` 内，紧接现有事件绑定区（约 line 2500+ 末尾）

#### 3.1 视图切换

```js
let view = "words"; // "words" | "passages"

function switchView(v) {
  view = v;
  $("passageView").hidden = v !== "passages";
  // 隐藏/显示词库相关 UI
  document.querySelector("header.app").style.display = v === "passages" ? "" : "";
  $("libbar").hidden = v === "passages";
  // PEP/my bar 隐藏
  $("pepbar").hidden = v === "passages" || state.lib !== "pep";
  $("mybar").hidden = v === "passages" || state.lib !== "my";
  $("chipsWrap").hidden = v === "passages";
  document.querySelector(".dock").style.display = v === "passages" ? "none" : "";
  // grid/empty 隐藏
  $("grid").hidden = v === "passages";
  $("empty").hidden = v === "passages";
  // 短文子视图
  $("passageListWrap").hidden = false;
  $("passageDetailWrap").hidden = true;
  $("btnPassages").hidden = v === "passages";
  $("btnWords").hidden = v !== "passages";
  if (v === "passages") renderPassageList();
}

$("btnPassages").addEventListener("click", () => switchView("passages"));
$("btnWords").addEventListener("click", () => switchView("words"));
$("btnPassageBack").addEventListener("click", () => {
  $("passageListWrap").hidden = false;
  $("passageDetailWrap").hidden = true;
});
```

#### 3.2 短文列表渲染

```js
function renderPassageList() {
  const items = (EBB.passages && EBB.passages.items) || [];
  const map = (EBB.passages && EBB.passages.wordMap) || {};
  $("passageList").innerHTML = items.map(p => {
    const known = p.words.filter(w => findWordAnyLib(w)).length;
    const total = p.words.length;
    return `<div class="passage-card" data-pid="${p.id}">
      <div class="pnum">No.${String(p.id).padStart(2,"0")}</div>
      <div class="ptitle">${escapeHtml(p.title)}</div>
      <div class="pwords">${total} 词 · ${total - known} 生词</div>
    </div>`;
  }).join("") || "<p>暂无短文</p>";
}

$("passageList").addEventListener("click", e => {
  const card = e.target.closest("[data-pid]");
  if (!card) return;
  openPassage(Number(card.dataset.pid));
});
```

#### 3.3 短文详情渲染（正文 + 单词列表）

```js
function openPassage(pid) {
  const items = EBB.passages.items || [];
  const p = items.find(x => x.id === pid);
  if (!p) return;
  $("passageTitle").textContent = `No.${String(p.id).padStart(2,"0")} ${p.title}`;
  // 正文：按行渲染，单词加 span.pw 可点击
  $("passageBody").innerHTML = p.lines.map(line => {
    const html = escapeHtml(line).replace(
      /\b([A-Za-z]+(?:'[a-z]+)?)\b/g,
      (m) => `<span class="pw" data-w="${m.toLowerCase()}">${m}</span>`
    );
    return `<p>${html}</p>`;
  }).join("");
  // 单词列表
  const map = EBB.passages.wordMap || {};
  $("passageWords").innerHTML = p.words.map(w => {
    const wobj = findWordAnyLib(w) || map[w.toLowerCase()] || { w, i: "", c: "" };
    const unknown = !findWordAnyLib(w);
    return `<span class="passage-word-chip${unknown ? " unknown" : ""}" data-w="${w}">${escapeHtml(w)}</span>`;
  }).join("");
  $("passageListWrap").hidden = true;
  $("passageDetailWrap").hidden = false;
}

// 点击正文单词
$("passageBody").addEventListener("click", e => {
  const sp = e.target.closest(".pw");
  if (!sp) return;
  openPassageWord(sp.dataset.w);
});
// 点击单词列表 chip
$("passageWords").addEventListener("click", e => {
  const chip = e.target.closest("[data-w]");
  if (!chip) return;
  openPassageWord(chip.dataset.w);
});

function openPassageWord(word) {
  const w = findWordAnyLib(word) || (EBB.passages.wordMap || {})[word.toLowerCase()] || { w: word, i: "", c: "（未收录）" };
  openWordModal(w);
}
```

#### 3.4 跨词库查找辅助

```js
function findWordAnyLib(word) {
  const key = String(word || "").toLowerCase().trim();
  if (!key) return null;
  // KET/PET
  for (const libId of ["ket", "pet"]) {
    const lib = EBB.libs[libId];
    if (!lib) continue;
    const hit = lib.words.find(w => String(w.w).toLowerCase() === key);
    if (hit) return hit;
  }
  // PEP 所有书
  for (const k in EBB.pep) {
    const b = EBB.pep[k];
    const hit = b.words.find(w => String(w.w).toLowerCase() === key);
    if (hit) return hit;
  }
  return null;
}
```

#### 3.5 详情弹窗「加入默写纸」按钮

```js
$("wAddSheet").addEventListener("click", () => {
  if (!wmodalWord) return;
  const key = selKey(wmodalWord);
  if (!key) return;
  if (state.selected.has(key)) {
    toast("已在默写纸中");
    return;
  }
  if (state.selected.size >= MY_PICK_MAX) {
    toast(`最多选择 ${MY_PICK_MAX} 个单词`);
    return;
  }
  state.selected.set(key, wmodalWord);
  updateSelBar();
  toast("已加入默写纸");
});
```

并把 `openWordModal` 中 `$("wAddSheet").hidden = false;` 一并设置，确保弹窗打开时按钮可见。

---

## Assumptions & Decisions

1. **Audios 路径硬编码**：`D:\AIProjects\MEEProcess\Audios` 写死在 `build.py`（与现有 `data/raw` 路径写死风格一致）；如该目录不存在，build 时打印 warning 并跳过短文模块，不影响主流程
2. **生词抓取 API**：优先尝试 Youdao JSON API；若无 key 或失败，降级到 dictionaryapi.dev（无 key，英文释义无中文，需手动补中文）；最终兜底：生词音标/翻译为空字符串，UI 显示 "（未收录）"，不影响短文阅读
3. **缓存策略**：`data/passage_words.json` 永久缓存，rebuild 时仅对新增的未缓存单词发起请求，避免重复抓取；可手动删除该文件强制重抓
4. **停用词过滤**：构建时过滤常见虚词，避免短文「单词列表」充斥 the/a/is 等；过滤表硬编码在 `build.py`
5. **不使用 Skill**：用户原问「做成 skill 还是直接用接口获取」已由用户选定「构建时 Python 脚本抓取」，无需创建 Trae Skill
6. **不混入 libbar**：短文通过独立「短文」按钮入口，切换 view 而非 lib，避免污染 `state.lib` 与现有 PEP/KET/PET 渲染流程
7. **复用 `openWordModal`**：短文单词与 PEP 单词共用同一详情弹窗，保证视觉与交互一致；短文单词无 `e`/`z` 时 `wordDetail` 内部走 `makeSentence` 兜底（已有逻辑，[template.html:1390](file:///d:/AIProjects/EbbWords/template.html#L1390)）
8. **「加入默写纸」对所有入口开放**：统一显示该按钮，简化逻辑；主词库卡片原有选词交互（toggleSelect on grid）保持不变，按钮只是新增的额外入口
9. **不引入 pdf_examples.json / pep_examples.json**：这两个遗留文件与短文模块无关，不接入
10. **短文 wordMap 结构**：`{lowercase_word: {w, i, c, p}}`，与主词库 word obj 字段对齐（`p` 词性、`i` 音标、`c` 中文）；不含 `t/e/z`（短文单词无 unit 归属，例句由 `makeSentence` 合成或留空）

---

## Verification Steps

1. **构建成功**：
   - 运行 `python build.py`
   - 控制台输出应包含 `passages=36 unknown_words=N cached=M fetched=K`
   - `index.html` 文件大小应较之前增大（嵌入短文 + wordMap）
   - `data/passage_words.json` 文件生成且非空

2. **本地打开 `index.html`**：
   - 顶部应出现「短文」按钮
   - 点击「短文」→ 显示 36 篇短文卡片列表，每张卡片显示编号、标题、词数/生词数
   - 点击任意卡片 → 进入短文详情：标题、正文（单词带下划虚线）、下方单词列表 chip

3. **点击正文单词**：
   - 弹出 `#wmodal` 详情弹窗，显示音标、翻译、例句
   - 已收录词：显示完整音标/翻译/例句（与 PEP 词库一致）
   - 未收录词：显示 `data/passage_words.json` 中抓取到的音标/翻译；若该词也未抓到，显示 "（未收录）"

4. **点击单词列表 chip**：
   - 同样弹出详情弹窗，行为与正文单词一致
   - 未收录词 chip 用虚线边框 + 橙色字区分

5. **加入默写纸**：
   - 详情弹窗中点击「加入默写纸」→ toast 提示 "已加入默写纸"
   - 返回单词视图（点「返回单词」），底部 dock 已选数 +1
   - 点击「生成默写纸」→ 默写纸中包含该短文单词

6. **返回与切换**：
   - 短文详情页点「← 返回列表」回到短文列表
   - 点顶部「返回单词」回到原词库视图，`state.lib`、`state.selected` 等状态未被破坏

7. **增量扩展验证**：
   - 在 `D:\AIProjects\MEEProcess\Audios` 新增一个 `37.New Title\Kai\37.New Title.txt`
   - 重新 `python build.py`
   - 控制台应显示 `passages=37`，且仅对新短文中未缓存的生词发起抓取
   - 页面刷新后列表出现第 37 篇

8. **生词抓取降级**：
   - 若词典 API 不可达，build 应继续完成，对应生词音标/翻译为空，UI 显示 "（未收录）"，不阻塞构建
