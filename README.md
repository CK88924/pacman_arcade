# 🎮 Arcade Pac-Man 遊戲

一個使用 Python Arcade 函式庫開發的經典 Pac-Man 遊戲，具有智慧 AI 和隨機迷宮生成。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Arcade](https://img.shields.io/badge/Arcade-2.6+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 特色功能

### 🎯 遊戲機制
- **隨機迷宮生成**：每次遊戲都有不同的地圖佈局
- **4個智慧鬼魂**：紅、藍、粉、橙，各有獨特AI個性
- **Power Pellets**：吃掉後可以反吃鬼魂（持續10秒）
- **計分系統**：普通豆子+10分，Power Pellet+50分，吃鬼+200分
- **遊戲狀態**：開始、進行中、遊戲結束、勝利

### 🤖 混合AI系統
每個鬼魂採用先進的混合AI演算法：

- **狀態機**：在追擊、散開、巡邏、隨機漫步4種模式間切換
- **個性化行為**：
- 👻🔴 紅鬼 (Blinky)：直接追擊玩家
- 👻💖 粉鬼 (Pinky)：預判玩家移動，埋伏前方 4 格
- 👻🔵 藍鬼 (Inky)：使用包抄策略
- 👻🟠 橙鬼 (Clyde)：靠近時逃跑，遠離時追擊
- **噪聲場導航**：生成平滑的隨機移動路徑
- **加權隨機選擇**：70%傾向目標，30%隨機，避免路線固定

## 🎮 操作說明

| 按鍵 | 功能 |
|------|------|
| ⬆️ 上箭頭 | 向上移動 |
| ⬇️ 下箭頭 | 向下移動 |
| ⬅️ 左箭頭 | 向左移動 |
| ➡️ 右箭頭 | 向右移動 |
| R | 遊戲結束後重新開始 |

## 📦 安裝

### 環境需求
- Python 3.8 或更高版本
- pip 套件管理器

### 安裝步驟

1. **複製儲存庫**
```bash
git clone <your-repo-url>
cd pacman_arcade
```

2. **安裝相依套件**
```bash
pip install -r requirements.txt
```

3. **執行遊戲**
```bash
python main.py
```

## 📁 專案結構

```
pacman_arcade/
├── main.py              # 主遊戲迴圈和視窗管理
├── character.py         # 玩家類別和移動邏輯
├── ghost_ai.py          # 鬼魂AI系統
├── item.py              # 豆子和Power Pellet
├── map_generator.py     # 隨機迷宮生成器
├── constants.py         # 遊戲常數設定
├── requirements.txt     # Python 相依套件
├── README.md           # 專案說明文件
└── assets/             # 遊戲資源檔案
    ├── pacman.png
    ├── ghost_red.png
    ├── ghost_blue.png
    ├── ghost_pink.png
    ├── ghost_orange.png
    └── wall.png
```

## 🎨 技術特點

### 核心技術
- **Python Arcade**：現代化的2D遊戲引擎
- **網格系統**：基於瓦片的移動和碰撞偵測
- **狀態機**：管理遊戲和AI狀態
- **深度優先搜尋**：生成連通的隨機迷宮

### 最佳化
- 使用 `arcade.Text` 物件提升渲染效能
- 空間雜湊加速碰撞偵測
- 每幀即時路徑檢測，避免鬼魂卡牆

## 🎯 勝利與失敗條件

- **勝利**：吃掉所有普通豆子和Power Pellets
- **失敗**：被鬼魂抓到（非Power Mode狀態）

## 🔧 設定

可以在 `constants.py` 中調整遊戲參數：

```python
    TILE_SIZE = 32                       # 單一地圖格子的像素大小
    SCREEN_WIDTH = 19 * TILE_SIZE        # 螢幕寬度（19 格）
    SCREEN_HEIGHT = 21 * TILE_SIZE       # 螢幕高度（21 格）
    PLAYER_SPEED = 2.0                   # 玩家移動速度（每幀位移）
    GHOST_SPEED = 1.6                    # 鬼魂移動速度，略慢於玩家
    COLOR_BG = (0, 0, 0)                 # 背景顏色（黑色）
```

## 🎮 遊戲特性與設計

### 隨機性與多樣性
- **動態地圖生成**：每次遊戲都會生成獨特的迷宮佈局
- **鬼魂行為多樣化**：4種AI模式（追擊、散開、巡邏、隨機漫步）動態切換
- **困住檢測系統**：自動檢測並打破鬼魂的重複路徑

### 地圖結構影響
由於採用完全隨機的迷宮生成，某些地圖可能會出現以下特性：
- **區域隔離**：部分鬼魂可能暫時被困在地圖的某個區域
- **難度變化**：不同地圖的鬼魂威脅程度不同，增加遊戲的挑戰性和重玩價值
- **策略性**：利用地形優勢躲避或引誘鬼魂

> 💡 **提示**：如果覺得當前地圖太簡單或太難，按 **R** 鍵重新生成！每次都是全新的體驗。


## 📄 授權條款

本專案採用 MIT 授權條款。詳見 LICENSE 檔案。

## 🙏 致謝

- 靈感來源：經典 Pac-Man 遊戲GOOGLE萬聖節小遊戲
- 使用框架：[Python Arcade Library](https://api.arcade.academy/)

## 📧 聯絡方式

如有問題或建議，歡迎提交 Issue 或 Pull Request！

---

**Enjoy the game! 🎮✨**
