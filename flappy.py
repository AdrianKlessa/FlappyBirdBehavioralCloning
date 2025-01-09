import pandas as pd
import pygame, sys, random
from pygame.time import Clock
screen = pygame.display.set_mode((1024, 1024))
gravity = 0.05
clock = Clock()

# TODO: Check for collisions
# TODO: Make a class for getting gameplay data

class Bird:
    bird_surface = pygame.image.load("assets/bird.png")
    bird_surface = pygame.transform.scale(bird_surface, (64, 64))
    vertical_movement = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.bird_rect = self.bird_surface.get_rect(center=(x, y))

    def draw_and_update(self, dt):
        screen.blit(self.bird_surface, self.bird_rect)
        self.vertical_movement += gravity*dt
        self.vertical_movement = min(self.vertical_movement, 20)
        self.y += self.vertical_movement
        self.bird_rect.centery = self.y
        print(f"Vertical movement: {self.vertical_movement}")

    def jump(self):
        self.vertical_movement = -15


class Ground:
    ground_surface = pygame.image.load("assets/ground.png")
    ground_surface = pygame.transform.scale(ground_surface, (1024, 128))

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw_and_update(self, dt):
        screen.blit(self.ground_surface, (self.x, self.y))
        screen.blit(self.ground_surface, (self.x + 1024, self.y))
        self.x -= 0.1*dt
        if self.x < -1024:
            self.x = 0


class Pipe:
    def __init__(self, x, y, manager):
        self.x = x
        self.y = y
        self.pipe_surface = manager.pipe_surface
        self.top_rect = self.pipe_surface.get_rect(midbottom=(x, y-128))
        self.bottom_rect = self.pipe_surface.get_rect(midtop=(x, y+128))

    def draw_and_update(self, dt):
        self.x -= 0.5*dt
        self.top_rect.centerx = self.x
        self.bottom_rect.centerx = self.x
        screen.blit(self.pipe_surface, self.top_rect)
        screen.blit(self.pipe_surface, self.bottom_rect)


class PipeManager:
    pipes_list = []
    pipe_surface = pygame.image.load("assets/pipe.png")
    pipe_surface = pygame.transform.scale(pipe_surface, (96, 768))

    def __init__(self):
        self.pipes_list = []

    def add_pipe(self):
        random_y = random.choice([300, 512, 768])
        new_pipe = Pipe(1024, random_y, self)
        self.pipes_list.append(new_pipe)

    def draw_and_update(self, dt):
        for pipe in self.pipes_list:
            pipe.draw_and_update(dt)
        if len(self.pipes_list) < 1:
            return
        if self.pipes_list[0].x < -1024:
            self.pipes_list.pop(0)


background_surface = pygame.image.load("assets/Background.png").convert()
background_surface = pygame.transform.scale(background_surface, (1024, 1024))

ground = Ground(0, 896)
bird = Bird(100, 100)
pipe_manager = PipeManager()

SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 1200)

dt = clock.tick(60)
while True:
    dt = clock.tick(60)
    print(f"FPS: {clock.get_fps()}")
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bird.jump()
        if event.type == SPAWNPIPE:
            pipe_manager.add_pipe()
    screen.blit(background_surface, (0, 0))
    ground.draw_and_update(dt)
    bird.draw_and_update(dt)
    pipe_manager.draw_and_update(dt)
    pygame.display.update()
