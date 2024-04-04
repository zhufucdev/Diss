import logging

import pygame
from PIL.Image import Image

from display import Display


class LocalDisplay(Display):
    def __init__(self, width: int, height: int):
        super().__init__((width, height), True)
        pygame.init()
        self.__screen = pygame.display.set_mode(self.canvas_size)
        self.__surface = None

    def start(self):
        clock = pygame.time.Clock()

        running = True
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break

                self.__screen.fill('black')
                if self.__surface is not None:
                    self.__screen.blit(self.__surface, (0, 0))

                pygame.display.flip()
                clock.tick(60)
            except KeyboardInterrupt:
                running = False

        pygame.quit()

    def draw(self, canvas: Image):
        self.__surface = pygame.image.fromstring(canvas.convert('RGB').tobytes(), self.canvas_size, 'RGB')
        logging.info('buffer flushed')
