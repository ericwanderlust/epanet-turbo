---
description: EPANET-Turbo 极速发布流程 (加密/打包/推送)
---

# 🏎️ EPANET-Turbo 发布工作流 (Standard Operating Procedure)

## 📌 流程概览

本工作流旨在确保未来更新时，能够一键完成：核心逻辑加密 -> 依赖同步 -> 双语 README 保全 -> 强制推送到 GitHub。

---

## 🛠️ 步骤 1：本地环境准备

确保你的 Python 环境安装了 PyArmor 9.x 和核心依赖：

```powershell
# 建议在项目根目录下操作
pip install pyarmor polars numpy pandas
```

---

## 🔐 步骤 2：核心逻辑加密

使用 PyArmor 加密核心模块，并将运行时库一并打包。

// turbo

```powershell
# 清理旧的 dist
rmdir /s /q dist_encrypted 2>$null

# 执行加密 (recursive 确保运行时模块 pyarmor_runtime 被正确生成在根部)
python -m pyarmor.cli gen --output dist_encrypted --recursive epanet_turbo

# 同步配置文件 (确保 pyproject.toml 包含 pyarmor_runtime)
copy pyproject.toml dist_encrypted\
copy README.md dist_encrypted\
copy LICENSE dist_encrypted\
copy requirements.txt dist_encrypted\

# 同步示例
mkdir dist_encrypted\examples 2>$null
copy examples\* dist_encrypted\examples\
```

---

## 📝 步骤 3：双语 README 维护

请务必保持 `README.md` 的双语结构。如果你更新了功能，请同步修改：

- **上部**: 🇨🇳 简体中文版 (包括 [🛡️ 安全、合规与统计](#-安全合规与统计))
- **下部**: 🇬🇧 English Version (包括 [🛡️ Compliance & Telemetry](#-compliance--telemetry))
- **底部**: 🤝 致谢名单 (Lee Yau-Wang 皝神)

---

## 🚀 步骤 4：覆盖发布到 GitHub

⚠️ **警告**: 此操作会用加密代码彻底覆盖仓库源码。

1. **备份私密源码** (外部不可见)：

   ```powershell
   mkdir private_src 2>$null
   copy epanet_turbo\*.py private_src\
   ```

2. **本地测试加密包**:

   ```powershell
   cd dist_encrypted
   pip install .
   python -c "from epanet_turbo import InpParser; print('Encrypted Version OK')"
   ```

3. **推送至 GitHub**:

   ```powershell
   # 将加密后的 dist 内容搬运回根目录并提交
   xcopy /E /Y /I dist_encrypted\* .
   git add . --all
   git commit -m "🚀 Update: EPANET-Turbo v[新版本号] (Encrypted Release)"
   git push origin main --force
   ```

---

## 📡 步骤 5：许可证管理 (Kill Switch)

如果你发现某设备滥用：

1. 从 Telegram 通知的 `设备ID` 中复制 ID。
2. 更新你 Gist 中的 `epanet_turbo_blocklist.txt`。
3. 远程封禁会立即生效（客户端有 1 小时缓存）。

---

*Made with 🏎️ for Lee Yau-Wang (皝神)*
