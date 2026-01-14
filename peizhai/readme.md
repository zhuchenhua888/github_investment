要在 Windows 系统中实现 **开机自动运行** 位于 `G:\peizhai` 目录下的 Python 服务命令：

```bash
python fetch_update.py --serve --port 8000 --schedule 09:00
```

你可以通过以下几种**可靠且推荐的方式**来实现。下面按**从简单到健壮**的顺序介绍：

---

## ✅ 推荐方案一：使用「任务计划程序」（Task Scheduler）【最稳定、支持用户未登录】

这是 Windows 官方提供的自动化工具，支持开机启动、后台运行、错误重试等，**即使你没登录系统也能运行**（需配置）。

### 步骤如下：

1. **打开任务计划程序**
   - 按 `Win + R`，输入 `taskschd.msc`，回车。

2. **创建基本任务**
   - 右侧点击「创建基本任务…」
   - 名称：`Peizhai Python Service`
   - 描述（可选）：开机自动启动 fetch_update 服务

3. **触发器 → 选择“当计算机启动时”**
   - 这样确保系统一启动就运行（不依赖用户登录）

4. **操作 → “启动程序”**
   - **程序/脚本**：填写你的 Python 解释器完整路径  
     👉 例如：`C:\Python39\python.exe`  
     （可通过在 CMD 中运行 `where python` 查找）
   - **添加参数（可选）**：
     ```
     fetch_update.py --serve --port 8000 --schedule 08:30
     ```
   - **起始于（可选）**：`G:\peizhai`  
     ⚠️ 这个很重要！必须指定工作目录，否则找不到 `fetch_update.py`

5. **完成前勾选“打开属性对话框”**
   - 在属性中，切换到「常规」选项卡：
     - 勾选 ✅ **“不管用户是否登录都要运行”**
     - 勾选 ✅ **“不存储密码”**（如果不需要访问网络资源）
     - 若需更高权限，可勾选“使用最高权限运行”（谨慎）
   - 切换到「条件」选项卡：
     - 取消勾选 ❌ “只有在计算机使用交流电源时才启动此任务”（如果是台式机可忽略，笔记本建议取消）
   - 切换到「设置」选项卡：
     - 勾选 ✅ “如果任务失败，重新启动每隔：1分钟，最多3次”

6. **点确定，输入当前用户密码（如提示）**

✅ 完成！重启电脑测试即可。

> 💡 提示：若 Python 是通过 Microsoft Store 安装的，建议改用传统安装版（如 python.org 下载），Store 版路径受限，可能无法在后台任务中调用。

---

## ✅ 方案二：使用批处理文件 + 启动文件夹（仅限用户登录后启动）

适合**你每次都会登录 Windows** 的场景，简单但不够健壮。

### 步骤：

1. 创建一个批处理文件，比如 `G:\peizhai\start_service.bat`，内容如下：

```bat
@echo off
cd /d G:\peizhai
python fetch_update.py --serve --port 8000 --schedule 08:30
```

2. 将该 `.bat` 文件放入 Windows 启动文件夹：
   - 按 `Win + R`，输入：
     ```
     shell:startup
     ```
   - 回车后会打开 `C:\Users\<你的用户名>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
   - 把 `start_service.bat` 快捷方式或文件本身放进去

> ⚠️ 缺点：只有你**登录账户后**才会运行；黑窗口会一直开着（可用 vbs 隐藏，但不如任务计划程序专业）。

---

## 🔒 补充建议：隐藏黑窗口（可选）

如果你用批处理方式，又不想看到黑色命令行窗口，可以创建一个 `.vbs` 脚本来静默启动：

1. 创建 `G:\peizhai\run_hidden.vbs`：
```vbs
CreateObject("Wscript.Shell").Run "G:\peizhai\start_service.bat", 0, False
```

2. 把这个 `.vbs` 文件放进 `shell:startup` 文件夹。

但依然**不如任务计划程序可靠**。

---

## 🛠️ 调试技巧

- 在任务计划程序中，可以右键任务 → “运行” 手动测试
- 查看「历史记录」（需先在“操作”→“启用所有任务历史记录”）
- 在 Python 脚本开头加日志，确认是否真的启动了：
  ```python
  import logging
  logging.basicConfig(filename='G:/peizhai/service.log', level=logging.INFO)
  logging.info("Service started at boot")
  ```

---

## ✅ 最终推荐

> **使用「任务计划程序」+ 指定工作目录 + 不管用户是否登录运行**  
> 这是 Windows 下实现开机自启 Python 服务的**最佳实践**，稳定、安全、可控。

如有需要，我也可以帮你生成完整的 XML 任务文件，直接导入使用。