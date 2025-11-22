# Mitsubishi Owner Portal for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Home Assistant 的三菱车主门户（日本）自定义集成。

此集成允许您通过官方[三菱车主门户](https://connect.mitsubishi-motors.co.jp/) API 监控您的三菱电动汽车。

[English Documentation](README.md) | [日本語ドキュメント](README_JP.md)

## 功能特性

- 电池电量监控
- 充电状态
- 充电模式
- 充电插头连接状态
- 充电就绪状态
- 充满电所需时间
- 点火状态
- 事件时间戳跟踪
- 续航里程（电动、汽油、综合）
- 位置信息跟踪
- 里程表
- 车门状态
- 安全警报
- 车内温度

## 安装

### HACS（推荐）

1. 在 Home Assistant 实例中打开 HACS
2. 点击"集成"
3. 点击右上角的三个点
4. 选择"自定义存储库"
5. 添加此存储库 URL：`https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS`
6. 选择"集成"作为类别
7. 点击"添加"
8. 在列表中找到"Mitsubishi Owner Portal"并点击"下载"
9. 重启 Home Assistant

### 手动安装

1. 从[发布页面][releases]下载最新版本
2. 解压 `custom_components/mitsubishi_owner_portal` 文件夹
3. 将其复制到 Home Assistant 的 `custom_components` 目录
4. 重启 Home Assistant

## 配置

此集成通过 UI 进行配置：

1. 转到设置 → 设备与服务
2. 点击"+ 添加集成"
3. 搜索"Mitsubishi Owner Portal"
4. 输入您的三菱车主门户凭据（电子邮件和密码）
5. 点击"提交"

您的车辆将自动被发现并添加到 Home Assistant。

### SSL 证书验证

默认情况下，集成会验证 SSL 证书。如果遇到证书错误：

1. 可以在集成配置中禁用"验证 SSL 证书"选项
2. 或在集成选项中更改设置

**注意：** 出于安全原因，不建议禁用 SSL 验证。

## 支持的传感器

此集成为每辆车创建以下传感器：

### 电池与充电

| 传感器 | 描述 | 单位 |
|--------|------|------|
| 当前电池电量 | 电池充电状态 | % |
| 充电状态 | 当前充电状态 | - |
| 充电插头状态 | 插头连接状态 | - |
| 充电模式 | 充电模式 | - |
| 充电就绪 | 充电准备状态 | - |
| 充满电所需时间 | 充满电剩余时间 | 分钟 |
| 最后更新时间 | 最后更新时间戳 | - |

### 续航里程信息

| 传感器 | 描述 | 单位 |
|--------|------|------|
| 总续航里程 | 综合续航里程 | km |
| 汽油续航里程 | 汽油续航里程 | km |
| 电动续航里程 | 电动（EV）续航里程 | km |

### 车辆状态

| 传感器 | 描述 | 单位 |
|--------|------|------|
| 点火状态 | 车辆点火状态 | - |
| 点火状态时间 | 点火状态变更时间 | - |
| 里程表 | 行驶里程 | km |
| 里程表更新时间 | 里程表最后更新时间 | - |

### 位置信息

| 传感器 | 描述 | 单位 |
|--------|------|------|
| 位置（纬度） | 车辆纬度坐标 | - |
| 位置（经度） | 车辆经度坐标 | - |
| 位置更新时间 | 位置信息最后更新时间 | - |

### 安全与状态

| 传感器 | 描述 | 单位 |
|--------|------|------|
| 防盗警报 | 防盗警报状态 | - |
| 防盗警报类型 | 防盗警报类型 | - |
| 隐私模式 | 隐私模式状态 | - |
| 车辆温度 | 车内温度 | °C |
| 车辆可访问 | 车辆访问状态 | - |
| 车门状态 | 车门状态 | - |
| 诊断状态 | 诊断状态 | - |

## 系统要求

- Home Assistant 2024.1.0 或更新版本
- 有效的[三菱车主门户](https://connect.mitsubishi-motors.co.jp/)账户（日本）
- 已注册到您账户的三菱电动汽车

## 已测试车型

此集成已在以下车型上测试：
- **三菱欧蓝德 PHEV（2022+）**

**注意：** 不保证与其他三菱车型兼容。该集成可能适用于支持三菱车主门户的其他车辆，但功能和传感器可能因车型和年份而异。

## 故障排除

### 身份验证失败

- 验证您的凭据是否正确
- 确保您的账户在官方三菱车主门户网站上可以正常使用
- 检查您的车辆是否已正确注册到您的账户

### 传感器不更新

- 检查您的互联网连接
- 验证三菱车主门户中有车辆的最新数据
- 检查 Home Assistant 日志中的错误消息

### SSL 证书错误

如果遇到 SSL 证书错误：

1. 确保您的系统 CA 证书是最新的
2. 检查网络连接和防火墙设置
3. 可以在集成配置中禁用"验证 SSL 证书"（不推荐）
4. 如果问题持续存在，请联系三菱技术支持

集成会自动创建修复问题和通知来告知您 SSL 证书错误。

## 更新凭据

使用内置的重新配置流程：

1. 转到集成设置
2. 点击"重新配置"
3. 输入新凭据
4. 集成将自动重新加载

或者，您可以在集成选项中更新密码和 SSL 设置。

## 支持

如果遇到任何问题或有疑问：

1. 检查[现有问题][issues]
2. 创建一个包含问题详细信息的新问题
3. 包含来自 Home Assistant 的相关日志

## 贡献

欢迎贡献！请随时提交拉取请求。

## 许可证

本项目采用 MIT 许可证 - 有关详细信息，请参阅 [LICENSE](LICENSE) 文件。

## 致谢

此集成未与三菱汽车公司关联或获得其认可。

---

[releases-shield]: https://img.shields.io/github/release/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[releases]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[commits]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[issues]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/issues
