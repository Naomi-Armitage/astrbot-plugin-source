# astrbot-plugin-source

私有的 AstrBot 插件源（custom plugin registry）。

AstrBot WebUI 默认只看官方源 `AstrBot_Plugins_Collection`。这个仓库托管一份独立 `plugins.json`，让 AstrBot WebUI 在「插件市场 → 自定义注册表」里可以看到 / 一键安装这边收录的插件，也可以正常收到版本更新提示。

## 用法

在 AstrBot WebUI 的"插件市场"右上角设置里填入：

```
https://raw.githubusercontent.com/<user>/astrbot-plugin-source/main/plugins.json
```

或调用 dashboard API：

```bash
curl -X POST http://<astrbot>:6185/api/plugin/source/save \
  -H "Content-Type: application/json" \
  -d '{"custom_url": "https://raw.githubusercontent.com/<user>/astrbot-plugin-source/main/plugins.json"}'
```

## 收录的插件

| 插件 | 仓库 |
|---|---|
| WebChat Gateway | https://github.com/Naomi-Armitage/astrbot_plugin_webchat_gateway |

## 增加 / 维护插件

1. 编辑 `plugins.json`，按现有格式添加一个条目（必需字段：`display_name`、`desc`、`author`、`repo`；可选：`tags`、`social_link`）
2. push 到 main
3. 等 ~6 小时（`.github/workflows/refresh.yml` 定时跑），或手动到 Actions 触发 `refresh` workflow——它会：
   - 拉取每个 plugin repo 的 `metadata.yaml`，把 `version` 字段同步进 `plugins.json`
   - 重新计算 `plugins-md5.json`（AstrBot 用它判断缓存是否失效）
   - 有变更就自动 commit

也可以本地跑：`python scripts/refresh.py`。

## 文件

- `plugins.json` — 插件索引（AstrBot 拉这个）
- `plugins-md5.json` — `{"md5": "..."}`，AstrBot 短路缓存校验用
- `scripts/refresh.py` — 同步 version + 重算 md5（无第三方依赖，stdlib only）
- `.github/workflows/refresh.yml` — 每 6 小时自动跑一次
