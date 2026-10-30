# AgentRoute · 智能体分流规则

[![自动构建](https://github.com/Heibai0502/agent-route/actions/workflows/run.yml/badge.svg)](https://github.com/Heibai0502/agent-route/actions/workflows/run.yml)

同一批来源，输出 **Mihomo / Clash、Surge / Shadowrocket、sing-box** 原生规则格式。共用规则、各用自己的节点；公开读取无需账号或 API key。

**给其他 Agent：** 读取 [AGENTS.md](AGENTS.md)，按 [index.json](https://raw.githubusercontent.com/Heibai0502/agent-route/release/index.json) 选择格式，并阅读 [DNS 与 WebRTC 防护指南](docs/DNS-WEBRTC.md)。不要把本仓库当作机场订阅导入。

<a id="agent-prompt"></a>

## 复制给自己的 Agent

点击下面代码块右上角的复制按钮，将完整提示词发给自己的 Agent。它会读取本项目说明，使用你的节点接入规则，并检查 DNS 与 WebRTC 防护。

```markdown
请在我的设备上接入 AgentRoute（Heibai0502/agent-route）分流规则，设置自动同步，保留我自己的节点，并检查、修复 DNS 和 WebRTC 防护。请实际完成配置、验证与交付。

先阅读这些公开资料：
- [Agent 接入说明](https://github.com/Heibai0502/agent-route/blob/master/AGENTS.md)
- [项目说明与客户端示例](https://github.com/Heibai0502/agent-route)
- [规则资源索引](https://raw.githubusercontent.com/Heibai0502/agent-route/release/index.json)
- [来源与校验清单](https://raw.githubusercontent.com/Heibai0502/agent-route/release/manifest.json)
- [DNS / WebRTC 排查修复指南](https://github.com/Heibai0502/agent-route/blob/master/docs/DNS-WEBRTC.md)

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

## Agent 机器接口

- [同步、校验、状态与回退](docs/SYNC.md)
- [客户端格式与规则优先级](docs/CLIENTS.md)
- [维护与验证](docs/MAINTAINING.md)
- [完整来源与许可声明](NOTICE.md) / [机器可读来源登记](sources.json)

## 上游项目与作者

- [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) (historical); GPL-3.0
- [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) (direct); GPL-3.0
- [Loyalsoldier/domain-list-custom](https://github.com/Loyalsoldier/domain-list-custom) (direct); MIT
- [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) (direct); CC-BY-SA-4.0, GPL-3.0
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) (indirect)
- [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) (indirect)
- [gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip) (indirect)
- [gfwlist/gfwlist](https://github.com/gfwlist/gfwlist) (indirect)
- [cokebar/gfwlist2dnsmasq](https://github.com/cokebar/gfwlist2dnsmasq) (indirect)
- [easylist/easylist](https://github.com/easylist/easylist) (indirect)
- [easylist/easylistchina](https://github.com/easylist/easylistchina) (indirect)
- [AdguardTeam/AdGuardSDNSFilter](https://github.com/AdguardTeam/AdGuardSDNSFilter) (indirect)
- [Peter Lowe](https://pgl.yoyo.org/adservers/) (indirect)
- [Dan Pollock](https://someonewhocares.org/hosts/) (indirect)

本项目许可证不替代各上游声明，详见 NOTICE 与保留的许可原文。
