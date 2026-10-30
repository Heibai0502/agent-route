# 共享分流规则 · Shared Routing Rules

[![自动构建](https://github.com/Heibai0502/surge-rules/actions/workflows/run.yml/badge.svg)](https://github.com/Heibai0502/surge-rules/actions/workflows/run.yml)

同一批来源，输出 **Mihomo / Clash、Surge / Shadowrocket、sing-box** 原生规则格式。共用规则、各用自己的节点；公开读取不需要 GitHub token、VpsCT 账号或 API key。

**给其他 Agent：** 读取 [AGENTS.md](AGENTS.md)，按 [index.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/index.json) 选择格式，并阅读 [DNS 与 WebRTC 防护指南](docs/DNS-WEBRTC.md)。不要把本仓库当作机场订阅导入。

<a id="agent-prompt"></a>

## 复制给自己的 Agent

点击下面代码块右上角的复制按钮，将完整提示词发给自己的 Agent。它会读取本项目说明，使用你的节点接入规则，并检查 DNS 与 WebRTC 防护。

```markdown
请在我的设备上接入 Heibai0502/surge-rules 共享分流规则，设置自动同步，保留我自己的节点，并检查、修复 DNS 和 WebRTC 防护。请实际完成配置、验证与交付。

先阅读这些公开资料：
- [Agent 接入说明](https://github.com/Heibai0502/surge-rules/blob/master/AGENTS.md)
- [项目说明与客户端示例](https://github.com/Heibai0502/surge-rules)
- [规则资源索引](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/index.json)
- [来源与校验清单](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/manifest.json)
- [DNS / WebRTC 排查修复指南](https://github.com/Heibai0502/surge-rules/blob/master/docs/DNS-WEBRTC.md)

执行要求：

1. 先识别我的操作系统、代理客户端、实际核心版本、浏览器配置档，以及当前系统代理/TUN、DNS 和 IPv6 状态。修改前保存必要的配置备份；缺少关键环境信息时再询问我。

2. 保留我的节点、机场订阅、认证信息、代理组成员、当前节点选择和已有明确例外。将示例中的 PROXY/DIRECT 映射到我的实际策略或出站名称。只合并需要的规则与设置，不用示例片段覆盖完整配置，不索取规则维护者的任何密钥。

3. 根据客户端选择匹配的原生规则格式。规则顺序保持：
   我的节点与明确例外 → LAN → private → reject → proxy → direct → cn-ip → 默认代理。
   保留唯一的最终规则，区分精确域名与后缀；广告白名单不能导致原本需要代理的网站被改成直连。

4. 优先使用客户端原生远程规则功能，设置约每 24 小时自动刷新。确认刷新配置已保存且资源成功加载。如果由脚本或 Agent 自行同步，固定同一个 release commit SHA，按 manifest 校验文件，整批验证成功后再替换；失败保留上一有效版本。不要仅下载一次静态文件就宣称已实现自动同步。

5. 检查并修复 DNS 路径：private/LAN 使用适用的本地解析；国内域名按预期直连解析；海外和未知域名使用经过我自己的代理出站的解析器。节点域名需要独立、可用的引导解析，避免循环依赖。检查浏览器安全 DNS、备用解析器、二次解析、FakeIP 和 IPv6 是否绕过预期策略。DoH 加密不等于 DNS 已经走代理；失败时不要静默添加直连或明文回退。

6. WebRTC 使用 Google 发布的 WebRTC Network Limiter。对于支持该扩展的 Chrome/Chromium 桌面浏览器，核对官方来源，在实际使用的配置档中安装或检查，并选择：
   Disable non-proxied UDP
   对应策略值：disable_non_proxied_udp。
   确认设置保存、重新打开浏览器后仍有效，并按实际使用情况检查无痕权限与扩展冲突。若浏览器不支持或受到企业策略限制，说明具体限制和待处理步骤，不绕过管理策略。

7. 分别验证规则加载、普通网页代理出口、国内/海外/private/未知域名的 DNS 路径，以及 IPv4/IPv6 和 WebRTC ICE 候选。不要关闭我正在使用的代理来做对照。安装扩展、只看到 mDNS 名称、没有 ICE 候选或检测页面空白，都不能单独作为“没有泄露”的证据。检查防护设置是否影响常用音视频功能。

8. 完成后给我简洁报告：修改了什么、使用的规则版本与生成时间、自动刷新方式、我的节点与选择是否保留、DNS/WebRTC 实际验证结果、备份和回退位置，以及尚未验证的范围。无法实测的项目明确标注，不把配置检查当作真实设备验收。
```

## 快速接入

1. 选择下面的配置片段，合并到自己的现有配置。
2. 将 `PROXY` 替换成自己的代理组或出站名称。sing-box 中 `DIRECT` 也要对应自己的直连出站。
3. 保留原来的节点、LAN、用户例外、DNS 与监听配置；规则顺序按下一节处理。
4. 执行客户端配置检查，再刷新规则资源。规则数据通常每 24 小时自动检查；配置片段本身不会远程覆盖你的设置。

| 客户端 | 标准格式 | 可直接参考的片段 |
| --- | --- | --- |
| Mihomo / Clash Meta / FlClash | YAML `payload`，域名用 `behavior: domain`，IP 用 `ipcidr` | [examples/mihomo.yaml](examples/mihomo.yaml) |
| Surge | 无策略列的 `RULE-SET` 文本 | [examples/surge.conf](examples/surge.conf) |
| Shadowrocket | 同一份 `RULE-SET` 文本；刷新周期在客户端设置 | [examples/shadowrocket.conf](examples/shadowrocket.conf) |
| sing-box | JSON source rule-set version 3；示例使用 1.14+ HTTP client 语法 | [examples/sing-box.json](examples/sing-box.json) |

Clash 分支和不同版本的字段支持可能不同；Mihomo 示例验证基线为 1.19.32，旧版 Clash 不宣称全部兼容。sing-box 数据格式要求 1.11+，完整示例验证基线为 1.14.4。Shadowrocket 只有文本结构检查，未宣称实体 iOS 已验证。

## 稳定资源地址

基础地址为 `https://raw.githubusercontent.com/Heibai0502/surge-rules/release/`。下面全部是不含凭据的公开文件。

| 规则 | 动作 | Surge / Shadowrocket | Mihomo | sing-box |
| --- | --- | --- | --- | --- |
| 私有 / 内网域名 | DIRECT | [private.list](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/surge/private.list) | [private.yaml](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/mihomo/private.yaml) | [private.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/sing-box/private.json) |
| 广告域名 | REJECT | [reject.list](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/surge/reject.list) | [reject.yaml](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/mihomo/reject.yaml) | [reject.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/sing-box/reject.json) |
| 海外域名 | 自己的 PROXY | [proxy.list](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/surge/proxy.list) | [proxy.yaml](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/mihomo/proxy.yaml) | [proxy.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/sing-box/proxy.json) |
| 国内域名 | DIRECT | [direct.list](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/surge/direct.list) | [direct.yaml](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/mihomo/direct.yaml) | [direct.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/sing-box/direct.json) |
| 中国 IPv4 / IPv6 | DIRECT 兜底 | [cn-ip.list](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/surge/cn-ip.list) | [cn-ip.yaml](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/mihomo/cn-ip.yaml) | [cn-ip.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/sing-box/cn-ip.json) |

机器入口：[index.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/index.json) · 同批时间、来源及 SHA-256：[manifest.json](https://raw.githubusercontent.com/Heibai0502/surge-rules/release/manifest.json)。`index.json` 是本项目版本化的 JSON 索引，不是客户端配置或通用标准协议。

## 规则优先级

**自己的节点和明确例外 → LAN → private → reject → proxy → direct → cn-ip → 默认代理。**

- `private` 必须早于海外与广告名单，例如精确的 `router.asus.com` 不应被 `.asus.com` 海外后缀覆盖；这里的 private 指通用内网域名规则，不是维护者的私密数据。
- 精确域名不能擅自扩成后缀。Mihomo 的 `+.example.com` 同时覆盖根域名和子域名；sing-box 的 `domain` / `domain_suffix` 分开保存。
- 新目录里的 `direct` **只含域名**，`cn-ip` **只含公网中国 IP**。cn-ip 剔除来源附带的 LAN / 合成地址，任一地址族缺失或出现重叠异常时拒绝发布新代。
- IP 兜底是否能处理未知域名，取决于客户端的解析流程。Surge / Mihomo 示例有意不为 cn-ip 加 `no-resolve`；sing-box 的远程 SOCKS 域名请求或 FakeIP 流量不能仅靠这一规则保证触发真实 IP 求值，见 [DNS 指南](docs/DNS-WEBRTC.md)。
- 个人强制代理域名、业务直连 IP、微信专用例外、广告白名单、浏览器设置和自己的节点不在共享数据里。需要的例外在自己的配置中维护；广告白名单应只跳过广告过滤，不能直接把原本需要代理的站点改为直连。

## 自动更新与失败保留

GitHub Actions 每天 **UTC+8 06:30** 计划运行；调度可能延迟，以 Actions 成功记录和 manifest 时间为准。每次先跑测试，再从固定上游下载，生成所有格式并通过官方 Mihomo / sing-box 原生检查，最后一次性切换 `release` 分支。失败时不推送，旧规则仍可用。

普通客户端按远程 URL 自动更新，各设备刷新时刻不同，不保证同一秒切换。其他 Agent / 自托管服务要严格使用同一代时：先解析 `release` 的完整 commit SHA，再从这个 SHA 下载 manifest 和需要的文件，逐个校验哈希，整批成功才原子替换；超时、截断、混代、校验失败或来源超过 48 小时应保留上一有效代并报告。源码更新不要 `git pull` 到生成分支：`master` 是源码，`release` 是可重建数据分支，发布会替换其历史。

VpsCT 的下游转换是独立消费端，既有部署按 4 小时检查来源、客户端按 24 小时刷新；这不是其他使用者必须运行的服务。共享仓库不会向任何人的节点或浏览器写入配置。

## DNS / WebRTC

域名规则决定连接往哪里走，DNS 决定查询往哪里走，WebRTC 还涉及浏览器自己的连接候选与 UDP 路径。这三项要分别验证。完整的排查、修复、回退与验证步骤见 [DNS-WEBRTC.md](docs/DNS-WEBRTC.md)。Chrome / 支持扩展的 Chromium 浏览器按该指南使用 **WebRTC Network Limiter**，并明确选择限制非代理 UDP 的选项；仅安装扩展不构成验收。

## 兼容旧消费者

根目录原有的 `direct.list` / `direct.json` / `direct.domains` / `direct.ipcidr`、`private.domains`、`proxy-source.txt`、`reject.domains` / `reject.list` / `reject.json` 和 manifest 字段继续保留。旧 `direct.list` / `direct.json` 仍混合域名、LAN 和 IP，不能拿它替换新目录中的纯域名资源。新文件只扩展 manifest 的 `files` 映射；消费者不要假设映射永远只有固定数量。

## 维护与来源

```sh
python3 -B -m unittest discover -s scripts -p 'test_*.py'
python3 -B scripts/build_rules.py
# 原生验证需要 PyYAML 6.0.3，以及自己核验过的官方可执行文件：
python3 -B scripts/validate_native.py --mihomo /path/to/mihomo --sing-box /path/to/sing-box
```

构建使用 Python 3.9+ 标准库，原生示例检查另外使用 PyYAML。无需项目密钥，勿使用 sudo。

数据来源为 Loyalsoldier 的 [v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat)（direct / proxy / reject）、[domain-list-custom](https://github.com/Loyalsoldier/domain-list-custom)（private）与 [geoip](https://github.com/Loyalsoldier/geoip)（中国 IP）。固定 URL 和每次输入摘要写入 manifest；海外原文 `proxy-source.txt` 与国内冲突清洗来自同一批下载。保留本仓库 [GPL-3.0 LICENSE](LICENSE) 和来源说明。

格式依据：[Mihomo rule-providers](https://wiki.metacubex.one/config/rule-providers/) · [Surge RULE-SET](https://manual.nssurge.com/rules/ruleset.html) · [sing-box rule-set](https://sing-box.sagernet.org/configuration/rule-set/)。DNS / 域名过滤不能可靠消除与正常内容共域名的视频广告；原生检查不等于每台设备的真实网络验收。
