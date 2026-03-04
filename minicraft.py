import math
import random
from dataclasses import dataclass

import pygame


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 32
GRAVITY = 1800
PLAYER_SPEED = 240
JUMP_SPEED = 640
REACH_TILES = 5

SKY_COLOR = (135, 206, 235)

BLOCK_TYPES = {
    0: {"name": "Air", "color": None, "solid": False},
    1: {"name": "Grass", "color": (95, 180, 95), "solid": True},
    2: {"name": "Dirt", "color": (130, 95, 65), "solid": True},
    3: {"name": "Stone", "color": (120, 120, 120), "solid": True},
    4: {"name": "Wood", "color": (140, 100, 55), "solid": True},
    5: {"name": "Leaves", "color": (70, 140, 70), "solid": True},
}

HOTBAR = [1, 2, 3, 4, 5]
WORLD_WIDTH = 300
WORLD_HEIGHT = 80


@dataclass
class Player:
    x: float
    y: float
    width: int = 26
    height: int = 44
    vx: float = 0
    vy: float = 0
    on_ground: bool = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


class MiniCraft:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("MiniCraft (Python)")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)

        self.world = [[0 for _ in range(WORLD_WIDTH)] for _ in range(WORLD_HEIGHT)]
        self.generate_world()

        spawn_x = WORLD_WIDTH // 2 * TILE_SIZE
        spawn_y = self.find_surface(WORLD_WIDTH // 2) * TILE_SIZE - 50
        self.player = Player(spawn_x, spawn_y)

        self.camera_x = 0
        self.camera_y = 0
        self.selected_slot = 0
        self.running = True

    def generate_world(self) -> None:
        base_height = WORLD_HEIGHT // 2
        height = base_height
        for x in range(WORLD_WIDTH):
            height += random.choice((-1, 0, 0, 1))
            height = max(18, min(WORLD_HEIGHT - 10, height))

            for y in range(height, WORLD_HEIGHT):
                depth = y - height
                if depth == 0:
                    self.world[y][x] = 1
                elif depth < 4:
                    self.world[y][x] = 2
                else:
                    self.world[y][x] = 3

            if random.random() < 0.055 and 7 < x < WORLD_WIDTH - 8:
                self.spawn_tree(x, height - 1)

    def spawn_tree(self, x: int, y: int) -> None:
        trunk_height = random.randint(3, 5)
        for i in range(trunk_height):
            ty = y - i
            if 0 <= ty < WORLD_HEIGHT:
                self.world[ty][x] = 4

        top = y - trunk_height
        for lx in range(x - 2, x + 3):
            for ly in range(top - 1, top + 3):
                if 0 <= lx < WORLD_WIDTH and 0 <= ly < WORLD_HEIGHT:
                    if abs(lx - x) + abs(ly - top) < 4:
                        if self.world[ly][lx] == 0:
                            self.world[ly][lx] = 5

    def find_surface(self, x: int) -> int:
        for y in range(WORLD_HEIGHT):
            if self.world[y][x] != 0:
                return y
        return WORLD_HEIGHT - 1

    def block_at(self, tx: int, ty: int) -> int:
        if 0 <= tx < WORLD_WIDTH and 0 <= ty < WORLD_HEIGHT:
            return self.world[ty][tx]
        return 0

    def solid_at(self, tx: int, ty: int) -> bool:
        block = self.block_at(tx, ty)
        return BLOCK_TYPES[block]["solid"]

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.player.vx = 0
        if keys[pygame.K_a]:
            self.player.vx = -PLAYER_SPEED
        if keys[pygame.K_d]:
            self.player.vx = PLAYER_SPEED

        if keys[pygame.K_SPACE] and self.player.on_ground:
            self.player.vy = -JUMP_SPEED
            self.player.on_ground = False

        self.player.vy += GRAVITY * dt
        self.move_and_collide(dt)
        self.update_camera()

    def move_and_collide(self, dt: float) -> None:
        self.player.x += self.player.vx * dt
        self.resolve_horizontal()

        self.player.y += self.player.vy * dt
        self.player.on_ground = False
        self.resolve_vertical()

    def resolve_horizontal(self) -> None:
        rect = self.player.rect
        start_x = rect.left // TILE_SIZE
        end_x = rect.right // TILE_SIZE
        start_y = rect.top // TILE_SIZE
        end_y = rect.bottom // TILE_SIZE

        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                if self.solid_at(tx, ty):
                    tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(tile_rect):
                        if self.player.vx > 0:
                            self.player.x = tile_rect.left - self.player.width
                        elif self.player.vx < 0:
                            self.player.x = tile_rect.right
                        self.player.vx = 0
                        rect = self.player.rect

    def resolve_vertical(self) -> None:
        rect = self.player.rect
        start_x = rect.left // TILE_SIZE
        end_x = rect.right // TILE_SIZE
        start_y = rect.top // TILE_SIZE
        end_y = rect.bottom // TILE_SIZE

        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                if self.solid_at(tx, ty):
                    tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(tile_rect):
                        if self.player.vy > 0:
                            self.player.y = tile_rect.top - self.player.height
                            self.player.on_ground = True
                        elif self.player.vy < 0:
                            self.player.y = tile_rect.bottom
                        self.player.vy = 0
                        rect = self.player.rect

    def update_camera(self) -> None:
        world_pixel_width = WORLD_WIDTH * TILE_SIZE
        world_pixel_height = WORLD_HEIGHT * TILE_SIZE
        target_x = self.player.x + self.player.width / 2 - SCREEN_WIDTH / 2
        target_y = self.player.y + self.player.height / 2 - SCREEN_HEIGHT / 2
        self.camera_x = max(0, min(world_pixel_width - SCREEN_WIDTH, target_x))
        self.camera_y = max(0, min(world_pixel_height - SCREEN_HEIGHT, target_y))

    def mouse_tile(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        world_x = mx + self.camera_x
        world_y = my + self.camera_y
        return int(world_x // TILE_SIZE), int(world_y // TILE_SIZE)

    def can_reach(self, tx: int, ty: int) -> bool:
        px = self.player.x + self.player.width / 2
        py = self.player.y + self.player.height / 2
        bx = tx * TILE_SIZE + TILE_SIZE / 2
        by = ty * TILE_SIZE + TILE_SIZE / 2
        distance_tiles = math.dist((px, py), (bx, by)) / TILE_SIZE
        return distance_tiles <= REACH_TILES

    def handle_mouse_action(self, left_click: bool) -> None:
        tx, ty = self.mouse_tile()
        if not (0 <= tx < WORLD_WIDTH and 0 <= ty < WORLD_HEIGHT):
            return
        if not self.can_reach(tx, ty):
            return

        if left_click:
            if self.world[ty][tx] != 0:
                self.world[ty][tx] = 0
        else:
            if self.world[ty][tx] == 0:
                block = HOTBAR[self.selected_slot]
                self.world[ty][tx] = block
                if self.player.rect.colliderect(
                    pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                ):
                    self.world[ty][tx] = 0

    def draw(self) -> None:
        self.screen.fill(SKY_COLOR)

        start_x = int(self.camera_x // TILE_SIZE)
        end_x = int((self.camera_x + SCREEN_WIDTH) // TILE_SIZE) + 1
        start_y = int(self.camera_y // TILE_SIZE)
        end_y = int((self.camera_y + SCREEN_HEIGHT) // TILE_SIZE) + 1

        for y in range(start_y, min(end_y, WORLD_HEIGHT)):
            for x in range(start_x, min(end_x, WORLD_WIDTH)):
                block = self.world[y][x]
                if block != 0:
                    color = BLOCK_TYPES[block]["color"]
                    rect = pygame.Rect(
                        x * TILE_SIZE - self.camera_x,
                        y * TILE_SIZE - self.camera_y,
                        TILE_SIZE,
                        TILE_SIZE,
                    )
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

        player_rect = pygame.Rect(
            self.player.x - self.camera_x,
            self.player.y - self.camera_y,
            self.player.width,
            self.player.height,
        )
        pygame.draw.rect(self.screen, (235, 60, 60), player_rect)

        self.draw_cursor_block()
        self.draw_hotbar()
        self.draw_help()

        pygame.display.flip()

    def draw_cursor_block(self) -> None:
        tx, ty = self.mouse_tile()
        rect = pygame.Rect(
            tx * TILE_SIZE - self.camera_x,
            ty * TILE_SIZE - self.camera_y,
            TILE_SIZE,
            TILE_SIZE,
        )
        color = (250, 250, 250) if self.can_reach(tx, ty) else (240, 80, 80)
        pygame.draw.rect(self.screen, color, rect, 2)

    def draw_hotbar(self) -> None:
        bar_width = len(HOTBAR) * 70
        x0 = SCREEN_WIDTH // 2 - bar_width // 2
        y0 = SCREEN_HEIGHT - 70

        for i, block in enumerate(HOTBAR):
            rect = pygame.Rect(x0 + i * 70, y0, 60, 60)
            pygame.draw.rect(self.screen, (35, 35, 35), rect)
            pygame.draw.rect(self.screen, (230, 230, 230), rect, 2)

            inner = rect.inflate(-18, -18)
            pygame.draw.rect(self.screen, BLOCK_TYPES[block]["color"], inner)
            if i == self.selected_slot:
                pygame.draw.rect(self.screen, (255, 210, 0), rect, 4)

            number = self.font.render(str(i + 1), True, (255, 255, 255))
            self.screen.blit(number, (rect.x + 4, rect.y + 2))

    def draw_help(self) -> None:
        text = "A/D move  SPACE jump  LMB break  RMB place  1-5 select"
        label = self.font.render(text, True, (20, 20, 20))
        self.screen.blit(label, (16, 12))

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_5:
                        self.selected_slot = event.key - pygame.K_1
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_mouse_action(left_click=True)
                    if event.button == 3:
                        self.handle_mouse_action(left_click=False)

            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    game = MiniCraft()
    game.run()
