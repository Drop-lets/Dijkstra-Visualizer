"""Pathfinding Visualizer — Dijkstra 最短路径可视化工具
入口模块
"""

import sys
import pygame
from controllers.app_controller import AppController
from config import SCREEN_W, SCREEN_H


def main():
    pygame.init()
    pygame.display.set_caption("Pathfinding Visualizer — Dijkstra's Algorithm")

    try:
        screen = pygame.display.set_mode(
            (SCREEN_W, SCREEN_H),
            pygame.SCALED | pygame.DOUBLEBUF,
            vsync=1,
        )
    except pygame.error:
        try:
            screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        except pygame.error:
            screen = pygame.display.set_mode((1024, 768))
            print("警告：使用 1024×768 分辨率。")

    clock = pygame.time.Clock()
    app = AppController()

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                app.handle_event(event)

        app.update(dt)
        app.draw(screen)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
