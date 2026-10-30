# DNS 与 WebRTC 防护：Agent 排查、修复与验收

本指南与共享分流规则配套。**DNS 查询路径、普通连接路径、WebRTC 候选地址必须分别检查。** 规则列表不包含浏览器设置，安装扩展也不会替你配置 DNS。这里只提供公开方法，不代表维护者或阅读者的设备已经通过验收。参考资料核对日期：2026-10-30。

## 1. 先记录目标和现场

在用户自己的设备上确认以下项目，保存必要的配置前像；聊天或公开回执只写脱敏结果。

| 项目 | 需要确认 |
| --- | --- |
| 环境 | 系统、浏览器及配置档、客户端与真实内核版本 |
| 代理方式 | 浏览器代理 / 系统 HTTP(S) 代理 / SOCKS / TUN / 全隧道 VPN；实际启用哪一种 |
| 预期策略 | 本仓库默认是国内直连、海外与未知代理；不是所有请求隐藏本地出口 |
| DNS | 系统解析器、客户端 DNS、国内 / 海外解析器、节点域名的引导解析、浏览器安全 DNS |
| 地址族 | IPv4、IPv6、FakeIP、物理网卡与隧道各自的实际路由 |
| 浏览器限制 | 扩展启用状态、无痕权限、其他扩展冲突、企业策略、已有媒体权限 |

不要为了取“关闭代理时的基线”中断用户现用连接。已有的运营商出口资料、用户授权的独立测试环境可辅助对照；拿不到可靠基线就标注，不能凭 IP 归属地推断无泄露。

## 2. DNS 参考策略

下表是这套规则的通用设计方向，需要按设备能力适配。国内直连属于有意的分流，不承诺对国内站点隐藏本机公网出口。

| 查询类别 | 解析路径 | 后续连接 |
| --- | --- | --- |
| localhost、LAN、private 域名 | 本机系统 / 局域网 DNS；适用时使用系统 mDNS | 本地或直连 |
| 用户明确指定的例外 | 用户认可的独立解析策略 | 对应例外策略 |
| 国内域名 | 国内 DoH，如阿里 `https://223.5.5.5/dns-query`、`https://223.6.6.6/dns-query` | DIRECT |
| 海外域名 | 海外 DoH，如 Cloudflare `https://1.1.1.1/dns-query`、`https://1.0.0.1/dns-query`，连接本身走用户自己的代理组 | PROXY |
| 未知公网域名 | 默认用经代理的海外解析器；失败不悄悄退回运营商明文 DNS | 优先代理；中国 IP 兜底取决于实际解析流程 |
| 节点服务器域名 | 单独的、用户认可的引导解析 | 必须在代理尚未建立时也能连接，避免递归依赖 |

DoH 加密查询与 DNS 经代理是两件事：直连 DoH 仍可让解析服务看到本地出口。只把地址换成 1.1.1.1 也不能证明走了代理。多个解析器如果并发查询，**每个**都必须符合对应的直连 / 代理策略，不能只检查第一个。

本仓库的 `cn-ip` 不是“所有 DNS 查询直连”的开关。应先匹配域名规则，再处理确实得到真实地址的 IP 规则。不要把 FakeIP 当真实中国 IP；IPv4 与 IPv6 混合答案也不应因为其中一个地址在中国就整体放行。

## 3. 各客户端如何修复 DNS

### Mihomo / Clash Meta

1. 核对现有 `dns.enable`、`enhanced-mode`、`nameserver-policy`、`nameserver`、`fallback`、`respect-rules`、`proxy-server-nameserver`，不要新建第二段重复的 DNS 配置。
2. 若采用 DNS 跟随路由，按当前内核文档设置 `respect-rules`，并保留独立的 `proxy-server-nameserver`，避免“解析节点必须先连上节点”的循环。
3. 用 `nameserver-policy` 对接 `rule-set:sr-private`、`rule-set:sr-direct`、`rule-set:sr-proxy`；private 优先于重叠的公网规则。未知查询默认送海外解析器，海外 DoH 端点的连接明确匹配代理组。受控内网域名保留系统 / LAN 解析；使用 FakeIP 时检查内网域名的真实地址例外。
4. 检查 `direct-nameserver` 等二次解析设置是否又把代理域名送到直连解析器。规则资源的 `proxy:` 只管下载文件，不能代替 DNS 出站策略。
5. 使用 TUN 时另查 DNS 劫持和 IPv6 路由是否覆盖目标应用。只开系统 HTTP 代理通常不能接管所有应用的 UDP DNS。

字段定义以 [Mihomo DNS 文档](https://wiki.metacubex.one/config/dns/) 为准。旧 Clash 分支不要照搬新 Mihomo 的全部字段。

### Surge / Shadowrocket

保留现有系统 / LAN 解析能力；按目标版本支持的域名映射或加密 DNS 策略，把国内与海外查询分开。Surge 可参考 `[Host]` 的 `RULE-SET:` / `DOMAIN-SET:` 映射；每条映射能否指定多个解析器以该版本为准。海外 DoH 服务器的连接还要被代理规则接管。不要把中国 IP 兜底一律加上 `no-resolve`，否则尚未解析的域名可能跳过它。

Surge 文档：[本地 DNS 映射](https://manual.nssurge.com/dns/local-dns-mapping.html)、[规则选项](https://manual.nssurge.com/rules/overview.html)。Shadowrocket 的 DNS、IPv6 和资源刷新应在实际 iOS 版本核对，Surge 语法通过不能代替它的设备验收。

### sing-box

公共 `sing-box/*.json` 是 source rule-set，不是 DNS 配置。用该内核支持的 DNS server、DNS rule 与 route rule 配置分别控制解析和连接；远端解析器显式指定用户的代理出站，private 用 local / mDNS 等适用的解析器，节点域名单独引导。

共享的 `examples/sing-box.json` 仅提供路由规则；其 cn-ip 对已经有真实目的 IP 的连接有效。直接送入 SOCKS 的未知域名、FakeIP 或嗅探后的域名不保证自动触发同样的中国 IP 求值。如果要复制“未知答案全部是中国 IP 才直连”的效果，需要按实际内核版本实现 DNS 答案筛选，混合答案 / 失败保持代理；不要仅加一个 cn-ip 规则就声称完成。1.14 的 DNS 迁移字段与旧写法不同，先查 [DNS 规则](https://sing-box.sagernet.org/configuration/dns/rule/) 和 [迁移文档](https://sing-box.sagernet.org/migration/)，不要混用已弃用的字段。

## 4. 浏览器安全 DNS 与 IPv6

浏览器可能启用独立的“安全 DNS”或由企业策略指定解析器。先确定它是否绕过客户端的分域名策略：

- 如果由本地代理客户端统一负责 DNS，可让浏览器使用系统 / 客户端解析路径，再由客户端提供 DoH。关闭浏览器的独立 DoH 不等于关闭客户端的加密 DNS。
- 如果保留浏览器独立 DoH，必须检查该连接经过哪个出口、是否破坏 LAN / private 域名解析，以及是否与客户端策略冲突。
- IPv6 必须单独验证；IPv4 代理成功不能证明 IPv6 被接管。优先修正 IPv6 路由与 DNS，无法验证时明确说明范围，不把全局关闭 IPv6 当默认修复。
- DNS over TLS / HTTPS 不使用明文 53 端口；因此“没看到 UDP 53”不足以证明所有查询都按预期出站。

浏览器与系统 DNS 选项以实际版本和用户策略为准，不直接编辑正在使用的浏览器内部数据库或以脚本覆盖企业管理设置。

## 5. WebRTC：使用 WebRTC Network Limiter

WebRTC 会建立 ICE 候选并尝试音视频 / 数据连接。仅配置 HTTP(S) 代理时，某些 WebRTC UDP 路径可能不受它控制；完整 VPN / TUN 则要看 UDP、IPv6 与路由覆盖，不能笼统说 VPN 只代理网页流量。候选可能是本地 host 地址、STUN 获得的 srflx 地址或 TURN 的 relay 地址；这些类型本身不等于泄露，必须与预期出口比较。参见 [RFC 8828](https://www.rfc-editor.org/rfc/rfc8828.html)。

按用户指定，Chrome / 支持该扩展的 Chromium 桌面浏览器使用 **WebRTC Network Limiter**：

1. 打开 [Chrome Web Store 官方条目](https://chromewebstore.google.com/detail/webrtc-network-limiter/npeicpdbkakmehahjeeohfdhnlpdklia)，核对名称、Google 开发者标识和扩展 ID `npeicpdbkakmehahjeeohfdhnlpdklia`，在目标浏览器配置档安装。
2. 打开扩展的 **Options / 选项**，选择 **Disable non-proxied UDP**（禁用非代理 UDP），对应策略值 `disable_non_proxied_udp`。
3. 保存并重新打开测试页面；重启浏览器后再检查选项仍然生效。按实际使用需要核对无痕模式中的扩展权限；另一个浏览器配置档不自动继承安装。
4. 如果选项不能保存或被覆盖，检查扩展冲突、启用状态与企业策略。受管理策略限制时报告具体原因，不绕过组织控制。

官方条目说明，禁止非代理 UDP 并非安装后的默认配置，因此必须核对选项。它可能使实时通话改走较慢的路径或失败，需要做业务回归。[Chrome 隐私 API](https://developer.chrome.com/docs/extensions/reference/api/privacy) 定义了对应 IP handling policy。

该扩展限制 WebRTC 网络路径，并不等于关闭所有 WebRTC 功能，也不保护其他浏览器、原生 App、DNS、定位权限、账号或 Cookie。手机 Chrome、Safari、Firefox 等不能直接按桌面 Chrome 扩展方案验收；不支持时标为待适配，不自动安装其他插件或禁用整套音视频功能。

## 6. 怎么验证，才算有证据

### DNS 验证

1. 保持用户现有代理开启，使用已知国内、海外、private / LAN 和未知域名四类测试；每类检查 A 与 AAAA。未知域名使用实际可控或认可的有效域名，不用不存在的随机字符串代替成功解析测试。
2. 在客户端的 DNS / 连接记录中核对命中规则、解析器、出站和地址族；必要时在用户授权下短时观察物理网卡与隧道。避免把原始业务日志或完整域名历史公开。
3. 海外与未知查询应按既定策略到达经代理的解析器；private 不应被发送到公网 DNS；国内直连解析器出现本地出口属于本套策略的预期。
4. DNS 检测网站只展示其观测到的递归解析器，不能单凭其国家 / 名称判断真实客户端出口或证明所有应用安全。结合客户端记录、实际网络路径和 IPv6 结果判断。
5. 网络切换、代理节点切换、应用重启后复查。只有本次确实执行的组合才写“通过”。

### WebRTC 验证

1. 在同一浏览器配置档确认普通 HTTPS 请求的预期代理出口；这是本次比较基线，不需要关闭代理。
2. 打开 WebRTC 官方 [Trickle ICE 示例](https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/)，查看 STUN / TURN 配置并收集候选。测试会联系所选服务器，使用用户认可的测试端点，不添加来历不明的 TURN 账号。
3. 对比 host / srflx / relay 候选与预期路径，特别检查是否出现未授权直连的本地运营商公网 IPv4 / IPv6。relay 是中继服务器地址，不要求与 HTTP 出口完全相同；代理的多个出口也需结合路径核实。
4. host 候选显示 mDNS 名称不等于已证明公网地址隐藏；“没有候选”也可能是 STUN 不可达。网络失败、权限差异或单次页面空白都不能单独记作保护通过。
5. 重新打开浏览器并复测，再用用户常用的音视频 / WebRTC 业务做功能回归。出现通话问题时记录影响，按用户选择回退该选项或研究受支持的代理 / TURN 路径，不静默放宽防护。

## 7. Agent 交付格式

```text
检查时间与环境：系统、浏览器配置档、核心版本
规则来源：release commit SHA、manifest 时间、所用格式、哈希结果
代理范围：系统代理 / TUN / VPN，IPv4 与 IPv6 各自覆盖情况
DNS：国内 / 海外 / private / 未知查询的解析器与出站（脱敏）
WebRTC：Network Limiter 的实际选项，重启后是否保持
测试：普通网页出口、ICE 候选分类、音视频回归结果
变更：修改了哪些字段，自己的节点和例外是否保留
回退：对应配置前像与扩展原选项的恢复位置
未验证：移动端、无痕档、IPv6、其他 App、切网等未实际测试项
```

只修改用户已授权的目标，优先保存配置前像并逐项验证。发现 DNS 绕路就修 DNS 路径，发现 WebRTC 绕路就查浏览器策略与实际 UDP / IPv6 路由；不要用重装服务器、换节点或覆盖所有配置替代定位。
