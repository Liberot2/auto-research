---
name: cbg-search
description: |
  Search and query items on Xi You (Fantasy Westward Journey) CBG (Treasure Pavilion) marketplace.
  Use when the user wants to: (1) Search for equipment/characters/pets on CBG, (2) Check item prices,
  (3) View item details, (4) Compare items across servers, (5) Monitor specific item listings.
  Triggers: "藏宝阁", "CBG", "cbg", "藏宝阁搜索", "搜索装备", "查询商品", "买装备", "无级别", "全服搜索".
---

# CBG Search - 藏宝阁商品查询

使用 agent-browser 自动化访问梦幻西游藏宝阁，搜索装备、角色、召唤兽等商品并查看详情。

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `item_type` | string | `equip` | 查询类型: `equip`(装备), `role`(角色), `pet`(召唤兽), `pet_equip`(召唤兽装备), `spirit`(灵饰), `yuangodd`(上古玉魄) |
| `level_min` | integer | `60` | 最低等级 |
| `level_max` | integer | `160` | 最高等级 |
| `kind` | string | `""` | 装备类型，见下方映射表。多个用逗号分隔，如 `男头,女头` |
| `effect` | string | `""` | 特效筛选，如 `无级别`, `永不磨损`, `愤怒` 等 |
| `skill` | string | `""` | 特技筛选，如 `罗汉金钟`, `晶清诀`, `四海升平` 等 |
| `price_min` | integer | `0` | 最低价格(元) |
| `price_max` | integer | `0` | 最高价格(元)，0表示不限 |
| `server` | string | `""` | 指定服务器，如 `北京2区`。留空为全服搜索 |
| `detail` | boolean | `false` | 是否查看搜索结果中指定商品的详情 |

## Workflow

1. **Open Search Page**: Navigate to the correct search form page based on `item_type`. Wait for page load (`wait --load networkidle`).

2. **Set Filters**: Configure search criteria on the form:
   - Level slider: Use search history to restore if available, otherwise drag slider handles
   - Item kind: Click type buttons using `find text "<kind_name>" click`
   - Effect/Skill: Click filter buttons using `find text "<effect_name>" click`
   - Price: Fill price input fields using `fill`

3. **Submit Search**: Click the bottom "全服搜索" button. Wait 5 seconds for AJAX results to load in-page. Results appear BELOW the search form, not in a new page.

4. **Collect Results**: Parse the results table using `snapshot -c`. Extract key fields per item: level, defense/attack, effect/skill, suit, price, server.

5. **Pagination**: If more pages exist, use the page jump textbox (last textbox before footer) — `fill <ref> "2"` then `press Enter`. Wait 3 seconds for results to refresh. Repeat for all pages.

6. **View Details** (if `detail=true`): Click "查看详情" link with `click <ref> --new-tab`. In new tab, use `snapshot -d 10` to get full item detail from popup dialog. Close detail tab after reading.

## CBG Page Interaction Guide

### Entry URLs

| Search Type | URL |
|-------------|-----|
| Equipment | `https://xyq.cbg.163.com/cgi-bin/equipquery.py?act=show_overall_search_equip` |
| Character | `https://xyq.cbg.163.com/cgi-bin/xyq_overall_search.py?act=show_search_role_form` |
| All-in-one | `https://xyq.cbg.163.com/cgi-bin/equipquery.py?act=show_overall_search_equip` (tabs at top) |

### Search Form Interaction

**Level Slider** (自定义JS组件):
- The slider is a custom JS component, NOT a standard HTML input
- **Best approach**: Click the search history link (e.g., `等级:130-130 , 类型...`) to restore previous settings — this sets the slider instantly
- **Alternative**: Use `drag @left_handle @right_handle` to move handles, but this is unreliable for precise values
- **Never**: Reload the page after setting the slider — it resets to 60-160

**Type/Effect/Skill Selection**:
- Use semantic locators: `agent-browser find text "男头" click`
- Multiple selections are additive (click both `男头` and `女头` to search both)
- Selected items show as highlighted/active in the snapshot

**Search Button**:
- The bottom "全服搜索" button uses `javascript:;` — it triggers AJAX, NOT page navigation
- After clicking, results load IN the same page below the form
- Must wait at least 5 seconds: `agent-browser wait 5000`
- Verify results appeared by checking for `columnheader "综合排序"` or price cells

### Pagination

- DO NOT click page number links (e.g., "1", "2", "3") — they use `goto(N)` which opens character search in a new tab instead
- Use the page jump textbox: `fill <ref> "2"` + `press Enter`
- Wait 3 seconds after each page change

### Item Detail View

- "查看详情" links point to new-format URLs: `/equip?s=215&eid=<equip_id>`
- Always use `click <ref> --new-tab` to open in a new tab
- Detail content renders in a popup overlay on the new page
- Use `snapshot -d 10` (depth 10) to capture all popup content including attributes, gems, talismans, suit effects
- Close the detail tab when done: `agent-browser tab close`

### Critical Pitfalls

| Pitfall | Solution |
|---------|----------|
| Direct URL `overall_search_equip` returns `no such act` | Must submit from search form page — results require form session |
| `goto(2)` function opens character search | Use page jump textbox + Enter instead of page number links |
| Level slider resets on page reload | Avoid reloading; use search history to restore slider |
| Search results not appearing | Wait longer (5s+); try clicking "全服搜索" button at the very bottom of the form |
| Detail page shows homepage | Use `click --new-tab` instead of direct `open` |
| `drag` not working on slider | Slider is custom JS; prefer search history restore |

## Equipment Kind Mapping

| Chinese Name | Keyword for `find text` | Category |
|-------------|------------------------|----------|
| 扇 | `扇` | Weapon |
| 剑 | `剑` | Weapon |
| 刀 | `刀` | Weapon |
| 斧 | `斧` | Weapon |
| 锤 | `锤` | Weapon |
| 枪 | `枪` | Weapon |
| 双环 | `双环` | Weapon |
| 双剑 | `双剑` | Weapon |
| 鞭 | `鞭` | Weapon |
| 爪刺 | `爪刺` | Weapon |
| 魔棒 | `魔棒` | Weapon |
| 飘带 | `飘带` | Weapon |
| 宝珠 | `宝珠` | Weapon |
| 弓 | `弓` | Weapon |
| 法杖 | `法杖` | Weapon |
| 灯笼 | `灯笼` | Weapon |
| 巨剑 | `巨剑` | Weapon |
| 伞 | `伞` | Weapon |
| 双斧 | `双斧` | Weapon |
| 棍 | `棍` | Weapon |
| 男衣 | `男衣` | Armor |
| 女衣 | `女衣` | Armor |
| 男头 | `男头` | Armor |
| 女头 | `女头` | Armor |
| 腰带 | `腰带` | Armor |
| 鞋子 | `鞋子` | Armor |
| 饰品 | `饰品` | Accessory |

## Common Effects & Skills

**Effects (特效)**:
`无级别`, `永不磨损`, `简易`, `愤怒`, `暴怒`, `神农`, `神佑`, `精致`, `坚固`, `狩猎`, `绝杀`, `专注`, `伪装`, `易修理`, `再生`, `必中`, `迷踪`, `珍宝`

**Skills (特技)**:
`罗汉金钟`, `晶清诀`, `笑里藏刀`, `破血狂攻`, `破碎无双`, `慈航普度`, `四海升平`, `玉清诀`, `金刚怒目`, `琴音三叠`, `乾坤挪移`, `疾风荡魄`, `放下屠刀`, `野兽之力`, `流云诀`, `凝滞术`, `光辉之甲`, `破甲术`, `水清诀`, `弱点击破`

## Output Format

搜索结果以中文报告输出，格式如下：

```markdown
## 藏宝阁搜索结果

**搜索条件**: 等级 {level_min}-{level_max}, 类型 {kind}, 特效 {effect}, 特技 {skill}
**搜索时间**: {timestamp}
**结果总数**: 约 {total} 件

| # | 等级 | 防御/属性 | 特技/特效 | 套装 | 价格 | 服务器 |
|---|------|----------|----------|------|------|--------|
| 1 | 130 | +16防御 | 无级别 命疗术 | 变身灵鹤 | ￥45,000 | 无与伦比 千里之外 |

### 价格分析
- 最低价: ￥xxx
- 最高价: ￥xxx
- 主流价位: ￥xxx - ￥xxx

### 推荐
{Highlight notable items based on value, attributes, or rarity}
```

## Notes

- Report output in Chinese (Chinese), keep English terms for technical attributes (e.g., JSON field names)
- Always close detail tabs after viewing to avoid tab accumulation
- CBG pages use mootools.js framework — custom UI components may not respond to standard HTML interactions
- If logged in, the account server is shown at top; items on the same server have no cross-server fee
- Cross-server fees are shown in price column as "另需跨服费￥xxx"
