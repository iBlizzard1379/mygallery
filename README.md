# AI 知识画廊 (AI Knowledge Gallery)

这是一个使用 Three.js 创建的 3D 虚拟画廊，智能展示和处理多种格式的文档和图片，支持 AI 问答功能。

## 特点

- 长廊式画廊布局，模仿真实美术馆的展示效果
- 墙面上嵌入式画框展示图片和文档
- 每个画框都有专门的聚光灯照明
- 第一人称视角控制，可以自由移动和观看
- 支持图片和 PDF 文件的展示
- 响应式设计，适应不同屏幕尺寸

## 如何使用

1. 将您想要展示的图片和文档放入 `images/` 文件夹
2. 打开 `index.html` 文件
3. 点击画面开始交互
4. 使用以下控制方式在画廊中移动：
   - W / ↑ - 前进
   - S / ↓ - 后退
   - A / ← - 左移
   - D / → - 右移
   - 鼠标 - 控制视角

## 技术细节

- 使用 Three.js 构建 3D 场景
- 使用 PointerLockControls 实现第一人称控制
- 动态加载图片作为纹理
- 为 PDF 文件生成预览缩略图
- 碰撞检测防止穿墙

## 进一步开发

- 可以修改 `gallery.js` 中的常量来调整画廊尺寸和布局
- 可以添加更多的光照效果
- 可以实现点击图片查看大图的功能
- 可以添加背景音乐

## 运行方法

由于浏览器安全限制，需要通过 HTTP 服务器访问此应用。可以使用以下方法之一：

1. 使用 Python 的内置服务器：
   ```
   python -m http.server 3000
   ```

2. 使用 Node.js 的 http-server：
   ```
   npx http-server -p 3000
   ```

然后访问 `http://localhost:3000` 或相应的服务器地址。 