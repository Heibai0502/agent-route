# Agent 只读接入指南

本仓库的公共数据允许其他人的 Agent 读取、验证并用于各自的客户端。使用自己的节点，不需要维护者的 VpsCT API、面板账号、订阅、Cookie 或任何密钥。

## 入口与目标

- 项目说明：`https://github.com/Heibai0502/surge-rules`
- 本说明：`https://raw.githubusercontent.com/Heibai0502/surge-rules/master/AGENTS.md`
- 格式与资源索引：`https://raw.githubusercontent.com/Heibai0502/surge-rules/release/index.json`
- 来源与校验：`https://raw.githubusercontent.com/Heibai0502/surge-rules/release/manifest.json`
- DNS / WebRTC 诊断修复：[docs/DNS-WEBRTC.md](docs/DNS-WEBRTC.md)

## 接入步骤

1. 读取用户已有的客户端类型、实际核心版本、代理组名、节点来源、DNS、IPv6 与系统代理 / TUN 状态，私密配置只在用户自己的环境处理。备份将要修改的字段，不输出节点密码或完整订阅地址。
2. 从 index 的 `datasets[].resources` 选择客户端原生格式。`mihomo_behavior` 必须与 provider 一致。Surge 和 Shadowrocket 共用 `surge/*.list`；sing-box 使用 source JSON，完整片段要求 1.14+。
3. 合并 [examples](examples/) 中的片段，把 `PROXY` / `DIRECT` 映射到用户已有策略或出站；保留节点、组成员、当前选择、监听端口、LAN、节点解析和明确例外。不要把片段覆盖成完整配置，也不要创建以 DIRECT 充当 PROXY 的假代理组。
4. 优先级：用户 / 节点例外 → LAN → private → reject → proxy → direct → cn-ip → 默认代理。保留唯一的最终规则。规则集不包含自己的 DNS、微信特例、广告白名单或浏览器保护。
5. 原生远程资源默认按 24 小时刷新。需要严格同代时，GET `https://api.github.com/repos/Heibai0502/surge-rules/commits/release` 获取完整 SHA，从 `https://raw.githubusercontent.com/Heibai0502/surge-rules/<SHA>/` 下载 manifest 和所需文件；比对 manifest SHA-256 后整批切换。限制每个下载 16 MiB，拒绝路径穿越和 URL 越界，失败保留上一有效代。不要把多个滚动分支或不同时间的上游拼接。
6. 按 DNS / WebRTC 指南分别排查。Chrome 使用用户选定的 WebRTC Network Limiter；不宣称规则文件可以代替浏览器设置。修复须在该设备用户授权范围内进行，不关闭正在使用的代理作对照，不擅自改变企业策略。
7. 合并后做原生配置检查、空缓存规则加载及域名 / IPv4 / IPv6 / DNS / WebRTC 定向验证；记录版本、规则生成时间、结果和未测范围。语法检查、iOS 文本检查、第三方检测网页各自只能证明其实际范围。

## 可转发任务

> 请读取本仓库 AGENTS.md、README 和 DNS-WEBRTC.md，将同一 release 的规则接入我自己的代理客户端，保留我的节点和已有例外，启用周期刷新。先识别客户端与核心版本，再选择原生格式、映射我已有的代理组；分别检查 DNS 路径与 WebRTC，Chrome 使用 WebRTC Network Limiter 的 Disable non-proxied UDP 选项。做完给出验证结果及未验证事项，不索取规则维护者的任何密钥。

## 维护此仓库时

公共接入不授予仓库写权限。只有仓库所有者明确要求修改 / 发布时才提交；不改写已有 `master` 历史。保留旧根目录文件与 manifest 字段语义，新增格式用子目录，禁止引入维护者的服务器地址、节点、凭据或私密证据。生成结果进入 `release`，源码进入 `master`。发布前运行单元测试、原生检查及同输入下旧九个资源的字节对比；构建或校验失败不替换上一代。不要改动消费者的生产服务来验证公开数据。
