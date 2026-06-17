"""全局配置常量 — 现代化 UI 配色 & 布局"""

# ============================================================
# 窗口尺寸
# ============================================================
SCREEN_W = 1280
SCREEN_H = 800
TITLE_H = 44

TOOLBAR_W = 210
TOOLBAR_X = 0
TOOLBAR_Y = TITLE_H
TOOLBAR_H = SCREEN_H - TITLE_H

STATUS_H = 30  # 画布底部状态栏高度

CANVAS_X = TOOLBAR_W
CANVAS_Y = TITLE_H
CANVAS_W = SCREEN_W - TOOLBAR_W - 310
CANVAS_H = SCREEN_H - TITLE_H - STATUS_H

INFO_X = CANVAS_X + CANVAS_W
INFO_Y = TITLE_H
INFO_W = 310
INFO_H = SCREEN_H - TITLE_H

# ============================================================
# 颜色 — 现代扁平风格
# ============================================================
# 全局
BG_COLOR        = (240, 242, 245)   # 冷灰背景
CANVAS_BG       = (255, 255, 255)   # 纯白画布
PANEL_BG        = (255, 255, 255)   # 面板白
PANEL_BORDER    = (229, 231, 235)   # 细边框
TITLE_BG        = (30,  41,  59)    # 深灰蓝标题栏
TITLE_TEXT      = (241, 245, 249)   # 浅色标题文字
STATUS_BG       = (248, 250, 252)   # 状态栏背景

# 顶点（淡色背景 + 黑色加粗标签，确保可读性）
VERTEX_DEFAULT   = (185, 188, 245)   # 淡紫蓝
VERTEX_CURRENT   = (255, 235, 140)   # 淡金
VERTEX_VISITED   = (178, 175, 235)   # 淡紫
VERTEX_SOURCE    = (140, 225, 190)   # 淡翠绿
VERTEX_TARGET    = (245, 155, 155)   # 淡红
VERTEX_PATH      = (140, 225, 190)   # 淡翠绿（最短路径）
VERTEX_LABEL     = (0,   0,   0)     # 黑色加粗
VERTEX_HOVER     = (205, 210, 252)   # 悬停高亮

# 顶点光环
RING_CURRENT     = (250, 204, 21)
RING_SOURCE      = (16,  185, 129)
RING_TARGET      = (239, 68,  68)
RING_EDGE_SRC    = (251, 191, 36)    # 添加边时源顶点光环

# 边
EDGE_DEFAULT     = (156, 163, 175)   # 灰
EDGE_RELAXING    = (251, 191, 36)    # 琥珀
EDGE_PATH        = (16,  185, 129)   # 翠绿
EDGE_WEIGHT_BG   = (255, 255, 255)
EDGE_WEIGHT_TEXT = (55,  65,  81)

# 按钮
BTN_IDLE         = (229, 231, 235)
BTN_HOVER        = (209, 213, 219)
BTN_ACTIVE       = (59,  130, 246)    # 蓝色（选中态）
BTN_ACTIVE_HOVER = (37,  99,  235)
BTN_TEXT         = (55,  65,  81)
BTN_TEXT_WHITE   = (255, 255, 255)
BTN_DISABLED     = (243, 244, 246)
BTN_DISABLED_TEXT = (187, 191, 198)

# 表格
TABLE_HEADER_BG  = (243, 244, 246)
TABLE_HEADER_TEXT = (55,  65,  81)
TABLE_ROW_EVEN   = (255, 255, 255)
TABLE_ROW_ODD    = (249, 250, 251)
TABLE_ROW_HL     = (254, 243, 199)    # 高亮行
TABLE_TEXT       = (55,  65,  81)
TABLE_BORDER     = (229, 231, 235)

# 分隔 & 输入
SEPARATOR_COLOR  = (209, 213, 219)
INPUT_BG         = (255, 255, 255)
INPUT_BORDER     = (59,  130, 246)
INPUT_TEXT       = (55,  65,  81)
INPUT_CURSOR     = (55,  65,  81)

# ============================================================
# 顶点 & 边 渲染参数
# ============================================================
VERTEX_R = 22
VERTEX_RING_W = 3
EDGE_WIDTH = 2
EDGE_HIGHLIGHT_W = 3
ARROW_SIZE = 10
WEIGHT_FONT_SIZE = 13
WEIGHT_OFFSET = 18

# ============================================================
# 字体
# ============================================================
FONT_FAMILY = "Microsoft YaHei"
FONT_FALLBACK = "SimHei"  # 备选中文字体
TITLE_FONT_SIZE = 18
SECTION_FONT_SIZE = 13
BTN_FONT_SIZE = 14
TABLE_FONT_SIZE = 13
STEP_MSG_SIZE = 12
STATUS_SIZE = 12

# ============================================================
# 算法控制
# ============================================================
AUTO_STEP_MS = 800
INF = float("inf")
