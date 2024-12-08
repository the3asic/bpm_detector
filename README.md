# BPM 检测器

一个强大的音频 BPM（每分钟节拍数）检测工具，支持多种检测算法和批量处理功能。本项目完全由 [Cursor](https://cursor.sh) 编辑器和 Claude-3.5-sonnet AI 助手协作完成，算法实现参考了 [Mixxx](https://github.com/mixxxdj/mixxx)（GNU License）和 [Bandcamp Tempo Adjust](https://github.com/jgchk/bandcamp-tempo-adjust) 项目。

## 功能特点

- 🎵 支持多种音频格式（WAV, MP3, OGG, FLAC）
- 🔍 三种检测算法：
  - 自相关算法（参考：Mixxx）
  - 能量流算法（参考：Mixxx）
  - Web 风格算法（参考：Bandcamp Tempo Adjust）
- 📊 置信度评分系统
- 🖥️ 现代化图形界面
- 📁 支持批量处理
- ✨ 支持文件名自动重命名

## 算法说明

### 自相关算法（参考 Mixxx）
- 通过分析音频信号的自相关性来检测节拍
- 适用于节奏清晰的音乐
- 对鼓点和打击乐器效果较好

### 能量流算法（参考 Mixxx）
- 分析音频能量变化来检测节拍
- 适用于电子音乐
- 适用于能量变化明显的音乐效果好

### Web 风格算法（参考 Bandcamp Tempo Adjust）
- 轻量级实现
- 适用于一般流行音乐

## 项目特色

- 🤖 完全由 Cursor + Claude-3.5-sonnet 辅助开发
- 💡 代码清晰易懂
- 🔧 易于扩展和修改
- 📚 详细的中文文档

## 系统要求

- macOS 10.13 或更高版本
- Python 3.9 或更高版本

## 安装说明

### 方法一：直接运行 Python 版本

1. 克隆仓库：

```bash
git clone https://github.com/the3asic/bpm_detector.git
cd bpm_detector
```

2. 创建虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 运行程序：

```bash
python -m bpm_detector.gui
```

### 方法二：安装 macOS 应用程序

1. 下载最新的发布版本
2. 将应用拖入应用程序文件夹
3. 双击运行

## macOS 应用打包详细说明

### 1. 环境准备

```bash
# 安装必要的工具
pip install py2app
brew install libsndfile  # 音频处理库
```

### 2. 创建图标（可选）

```bash
# 1. 准备一个 1024x1024 的 PNG 图片
# 2. 创建图标集
mkdir resources/bpm_detector.iconset
cd resources

# 3. 生成不同尺寸的图标
sips -z 16 16     icon_1024.png --out bpm_detector.iconset/icon_16x16.png
sips -z 32 32     icon_1024.png --out bpm_detector.iconset/icon_16x16@2x.png
sips -z 32 32     icon_1024.png --out bpm_detector.iconset/icon_32x32.png
sips -z 64 64     icon_1024.png --out bpm_detector.iconset/icon_32x32@2x.png
sips -z 128 128   icon_1024.png --out bpm_detector.iconset/icon_128x128.png
sips -z 256 256   icon_1024.png --out bpm_detector.iconset/icon_128x128@2x.png
sips -z 256 256   icon_1024.png --out bpm_detector.iconset/icon_256x256.png
sips -z 512 512   icon_1024.png --out bpm_detector.iconset/icon_256x256@2x.png
sips -z 512 512   icon_1024.png --out bpm_detector.iconset/icon_512x512.png
sips -z 1024 1024 icon_1024.png --out bpm_detector.iconset/icon_512x512@2x.png

# 4. 转换为 icns 文件
iconutil -c icns bpm_detector.iconset
mv bpm_detector.icns icon.icns
```

### 3. 打包应用

```bash
# 1. 清理之前的构建
rm -rf build dist

# 2. 开发模式构建（快速，用于测试）
python setup_macos.py py2app -A

# 3. 测试开发版本
./dist/BPM\ Detector.app/Contents/MacOS/BPM\ Detector

# 4. 生产模式构建（完整独立应用）
python setup_macos.py py2app

# 5. 测试生产版本
open ./dist/BPM\ Detector.app
```

### 4. 签名和公证（可选）

如果要在 macOS 上分发应用，建议进行签名和公证：

```bash
# 1. 应用签名
codesign --force --deep --sign "Developer ID Application: Your Name" "dist/BPM Detector.app"

# 2. 创建 ZIP 包
ditto -c -k --keepParent "dist/BPM Detector.app" "BPM Detector.zip"

# 3. 提交公证
xcrun notarytool submit "BPM Detector.zip" --apple-id "your.email@example.com" --password "app-specific-password" --team-id "YOUR_TEAM_ID"

# 4. 等待公证完成并添加公证标记
xcrun stapler staple "dist/BPM Detector.app"
```

### 5. 常见打包问题

1. Q: 应用无法启动，提示 "无法打开应用程序"？
   A: 可能是签名问题，尝试在终端运行应用查看具体错误信息。

2. Q: 找不到依赖库？
   A: 检查 setup_macos.py 中的 frameworks 配置，确保包含所有必要的动态库。

3. Q: 打包后缺少资源文件？
   A: 检查 setup_macos.py 中的 resources 配置，确保所有需要的资源都被包含。

## 使用说明

1. 启动程序后，您可以：
   - 拖放音频文件到程序窗口
   - 点击选择文件按钮浏览音频文件
   - 一次选择多个文件进行批量处理

2. BPM 检测选项：
   - 可以设置 BPM 范围（默认 92-184）
   - 可以选择是否将结果四舍五入为整数
   - 显示每个算法的检测结果和置信度

3. 结果显示：
   - 绿色：置信度 ≥ 60%
   - 橙色：置信度 ≥ 40%
   - 黄色：置信度 ≥ 20%
   - 红色：置信度 < 20%

4. 文件重命名：
   - 可以选择最佳 BPM 结果
   - 自动在文件名中添加 BPM 信息
   - 格式：原文件名 [140BPM].mp3

## 开发说明

### 项目结构

```
bpm_detector/
├── src/
│   └── bpm_detector/
│       ├── __init__.py
│       ├── detector.py    # 核心检测算法
│       ├── gui.py        # 图形界面
│       └── main.py       # 主程序入口
├── tests/                # 测试文件
├── setup.py             # Python 包配置
├── setup_macos.py       # macOS 应用打包配置
└── requirements.txt     # 依赖项
```

### 打包 macOS 应用

```bash
# 安装打包工具
pip install py2app

# 打包应用
python setup_macos.py py2app
```

## 常见问题

1. Q: 为什么检测结果会有差异？
   A: 不同算法适用于不同类型的音乐，建议参考置信度选择最佳结果。

2. Q: 支持哪些音频格式？
   A: 支持大多数常见音频格式，包括 WAV、MP3、OGG、FLAC 等。

3. Q: 如何选择最佳 BPM？
   A: 程序会自动选择置信度最高的结果，您也可以手动选择其他算法的结果。

## 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

## 开源协议

本项目基于 GNU General Public License v2.0 开源协议发布。

本项目的部分算法实现参考了以下开源项目：
- [Mixxx](https://github.com/mixxxdj/mixxx)：GNU General Public License v2.0
- [Bandcamp Tempo Adjust](https://github.com/jgchk/bandcamp-tempo-adjust)

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

## 联系方式

- 项目主页：[GitHub](https://github.com/the3asic/bpm_detector)
- 问题反馈：请在 [GitHub Issues](https://github.com/the3asic/bpm_detector/issues) 页面提交
