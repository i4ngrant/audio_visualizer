"""The on-screen text in the top-left corner and the beat light in the top-right."""
import pygame

from .controls import HELP_LINE


class Hud:
    def __init__(self):
        self._font = pygame.font.SysFont("consolas", 16)

    def draw(self, screen, status, beat_pulse, beat_color):
        screen.blit(self._font.render(status, True, (170, 170, 190)), (10, 10))
        screen.blit(self._font.render(HELP_LINE, True, (110, 110, 130)), (10, 30))

        # Beat light: flashes on every detected beat, even with beat effects off,
        # which makes it easy to tune detection with [ and ].
        center = (screen.get_width() - 22, 20)
        pygame.draw.circle(screen, (40, 40, 55), center, 10)
        if beat_pulse > 0.05:
            pygame.draw.circle(screen, beat_color, center, int(3 + 7 * beat_pulse))
