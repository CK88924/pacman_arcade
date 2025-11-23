import random

# 0 = 道路, 1 = 牆, 2 = 豆子, 3 = Power Pellet

def generate_map(width=19, height=21):
    """使用改進的迷宮生成算法 - 減少死胡同，增加循環路徑"""
    
    # 確保參數是整數
    width = int(width)
    height = int(height)
    
    # 初始化全牆
    maze = [[1 for _ in range(width)] for _ in range(height)]
    
    def carve_path(x, y):
        """遞迴雕刻路徑"""
        maze[y][x] = 0
        
        # 四個方向：上下左右
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # 檢查是否在邊界內
            if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                if maze[ny][nx] == 1:  # 如果是牆
                    # 雕刻中間的牆
                    maze[y + dy // 2][x + dx // 2] = 0
                    # 遞迴到新位置
                    carve_path(nx, ny)
    
    # 從 (1, 1) 開始生成迷宮
    carve_path(1, 1)
    
    # === 新增：移除死胡同，創建循環路徑 ===
    def remove_dead_ends():
        """找到並移除部分死胡同，創建更多循環"""
        removed = 0
        max_removals = (width * height) // 10  # 最多移除10%的死胡同
        
        for y in range(2, height - 2):
            for x in range(2, width - 2):
                if maze[y][x] == 1:  # 如果是牆
                    # 檢查周圍有多少個路徑
                    neighbors = [
                        maze[y-1][x], maze[y+1][x],
                        maze[y][x-1], maze[y][x+1]
                    ]
                    path_count = sum(1 for n in neighbors if n == 0)
                    
                    # 如果這個牆恰好連接兩個路徑，打通它創建循環
                    if path_count >= 2 and random.random() < 0.4:  # 40%機率打通
                        maze[y][x] = 0
                        removed += 1
                        if removed >= max_removals:
                            return
    
    remove_dead_ends()
    
    # 添加大量額外的通道讓迷宮更開放和互連
    for _ in range(width * height // 6):  # 增加更多開口（從8改為6）
        x = random.randrange(2, width - 2)
        y = random.randrange(2, height - 2)
        if maze[y][x] == 1:
            # 檢查周圍是否有路徑
            if (maze[y-1][x] == 0 or maze[y+1][x] == 0 or 
                maze[y][x-1] == 0 or maze[y][x+1] == 0):
                maze[y][x] = 0
    
    # 添加一些水平和垂直的長通道（增加數量）
    for _ in range(4):  # 從3增加到4
        # 水平通道
        y = random.randrange(2, height - 2)
        for x in range(2, width - 2):
            if random.random() < 0.75:  # 從0.7提高到0.75
                maze[y][x] = 0
        
        # 垂直通道
        x = random.randrange(2, width - 2)
        for y in range(2, height - 2):
            if random.random() < 0.75:
                maze[y][x] = 0
    
    # === 新增：創建大型開放區域 ===
    def create_open_areas():
        """在地圖中創建1-2個大型開放區域"""
        num_areas = random.randint(1, 2)
        for _ in range(num_areas):
            # 隨機選擇區域中心
            center_x = random.randint(4, width - 5)
            center_y = random.randint(4, height - 5)
            
            # 創建3x3或4x4的開放區域
            size = random.randint(2, 3)
            for dy in range(-size, size + 1):
                for dx in range(-size, size + 1):
                    ny, nx = center_y + dy, center_x + dx
                    if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                        maze[ny][nx] = 0
    
    create_open_areas()
    
    # 放置豆子在所有空地上
    for y in range(height):
        for x in range(width):
            if maze[y][x] == 0:
                maze[y][x] = 2
    
    # 隨機選擇4個位置放置 Power Pellets
    empty_positions = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if maze[y][x] == 2:
                empty_positions.append((x, y))
    
    # 選擇角落附近的位置放Power Pellets
    power_positions = []
    corners = [
        (1, 1), (width - 2, 1), 
        (1, height - 2), (width - 2, height - 2)
    ]
    
    for corner_x, corner_y in corners:
        # 找到最近的空地
        min_dist = float('inf')
        best_pos = None
        for px, py in empty_positions:
            dist = abs(px - corner_x) + abs(py - corner_y)
            if dist < min_dist and (px, py) not in power_positions:
                min_dist = dist
                best_pos = (px, py)
        if best_pos:
            power_positions.append(best_pos)
            maze[best_pos[1]][best_pos[0]] = 3  # Power Pellet
    
    # 確保玩家起始位置沒有豆子
    if maze[1][1] == 2 or maze[1][1] == 3:
        maze[1][1] = 0
    
    return maze
