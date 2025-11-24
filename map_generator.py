import random

# 0 = 道路, 1 = 牆, 2 = 豆子, 3 = Power Pellet

def generate_map(width=19, height=21):
    """
    Arcade-Pac-Man 友善版迷宮生成：

    - 仍然使用 DFS 建基礎迷宮（保留迷宮感）
    - 強化「迴路」與「十字交叉」→ 鬼 AI 比較有路可以繞、不會全塞同一條
    - 在中間 & 下方（鬼出生常見區域）多開一點空間
    - 最後再鋪豆子 + Power Pellet

    備註：
    - width / height 預設是 19x21，若改尺寸也能跑，只是結構不是完全對稱。
    """

    width = int(width)
    height = int(height)

    # =============================
    # 0. 初始化全牆
    # =============================
    maze = [[1 for _ in range(width)] for _ in range(height)]

    # =============================
    # 1. DFS 造出基本迷宮骨架
    # =============================
    def carve_path(x, y):
        """遞迴雕刻路徑 (以 2 格為步長，確保牆的厚度)"""
        maze[y][x] = 0

        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                if maze[ny][nx] == 1:
                    maze[y + dy // 2][x + dx // 2] = 0
                    carve_path(nx, ny)

    carve_path(1, 1)

    # =============================
    # 2. 適度打通牆，製造「更多迴路」
    # =============================
    def connect_loops():
        """
        找「附近兩邊以上是路」的牆，打通一部分，形成多條環狀路線。
        這是讓鬼可以繞路、不會一直被單線卡住的關鍵。
        """
        removed = 0
        max_removals = (width * height) // 10  # 稍微比原本多一點迴路

        for y in range(2, height - 2):
            for x in range(2, width - 2):
                if maze[y][x] != 1:
                    continue

                neighbors = [
                    maze[y-1][x], maze[y+1][x],
                    maze[y][x-1], maze[y][x+1]
                ]
                path_count = sum(1 for n in neighbors if n == 0)

                # 只處理「至少兩邊是路」的牆，並且有機率打通
                if path_count >= 2 and random.random() < 0.28:
                    maze[y][x] = 0
                    removed += 1
                    if removed >= max_removals:
                        return

    connect_loops()

    # =============================
    # 3. 加強主幹「長通道」
    # =============================
    for _ in range(4):  # 原本是 3，讓主幹多一點
        # 水平主幹
        y = random.randrange(3, height - 3)
        for x in range(2, width - 2):
            if random.random() < 0.7:  # 原本 0.6 → 多一點直線
                maze[y][x] = 0

        # 垂直主幹
        x = random.randrange(3, width - 3)
        for y in range(2, height - 2):
            if random.random() < 0.7:
                maze[y][x] = 0

    # =============================
    # 4. 十字交叉層（Pac-Man 風格骨架）
    # =============================
    def create_cross_layers():
        """
        類似原作 Pac-Man，強制一些水平 / 垂直走廊，
        讓路線不只是「樹狀迷宮」，而是有多個十字交叉。
        """
        # 水平交叉（每 4 列一層）
        for y in range(3, height - 3, 4):
            for x in range(2, width - 2):
                maze[y][x] = 0

        # 垂直交叉（選 3~4 欄作為主幹）
        possible_cols = list(range(3, width - 3, 4))
        random.shuffle(possible_cols)
        for x in possible_cols[:4]:
            for y in range(2, height - 2):
                maze[y][x] = 0

    create_cross_layers()

    # =============================
    # 5. 創建開放區域 + 中央廣場 + 鬼出生區附近加寬
    # =============================
    def create_open_areas():
        """在地圖中創建幾個中型開放區域（不會太多，避免全平地）"""
        num_areas = random.randint(2, 3)
        for _ in range(num_areas):
            center_x = random.randint(4, width - 5)
            center_y = random.randint(4, height - 5)

            size = random.randint(2, 3)  # 半徑
            for dy in range(-size, size + 1):
                for dx in range(-size, size + 1):
                    nx = center_x + dx
                    ny = center_y + dy
                    if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                        maze[ny][nx] = 0

        # 中央區域固定做一個「小廣場」，利於鬼分流 / 包抄
        cx, cy = width // 2, height // 2
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                nx, ny = cx + dx, cy + dy
                if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                    maze[ny][nx] = 0

        # 鬼常見出生區（底部中間）附近再開一點空間
        spawn_cx, spawn_cy = width // 2, height - 3
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                nx, ny = spawn_cx + dx, spawn_cy + dy
                if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                    maze[ny][nx] = 0

    create_open_areas()

    # =============================
    # 6. 全部 0 → 豆子 2
    # =============================
    for y in range(height):
        for x in range(width):
            if maze[y][x] == 0:
                maze[y][x] = 2

    # =============================
    # 7. 配置 Power Pellets（靠近四角）
    # =============================
    empty_positions = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if maze[y][x] == 2:
                empty_positions.append((x, y))

    power_positions = []
    corners = [
        (1, 1), (width - 2, 1),
        (1, height - 2), (width - 2, height - 2)
    ]

    for corner_x, corner_y in corners:
        min_dist = float("inf")
        best_pos = None
        for px, py in empty_positions:
            dist = abs(px - corner_x) + abs(py - corner_y)
            if dist < min_dist and (px, py) not in power_positions:
                min_dist = dist
                best_pos = (px, py)
        if best_pos:
            power_positions.append(best_pos)
            maze[best_pos[1]][best_pos[0]] = 3  # Power Pellet

    # =============================
    # 8. 保證玩家起點 (1,1) 是道路
    # =============================
    if maze[1][1] in (1, 2, 3):
        maze[1][1] = 0

    return maze
