"""Keyboard controls. Rebind keys by editing KEYMAP; actions are handled in app.py.

The defaults avoid arrow keys so they work on compact keyboards. The arrows
are bound too, as alternates, for keyboards that have them.
"""
import pygame

KEYMAP = {
    pygame.K_ESCAPE: "quit",
    pygame.K_SPACE: "next_mode",
    pygame.K_c: "next_palette",
    pygame.K_PERIOD: "more_bars",
    pygame.K_RIGHT: "more_bars",
    pygame.K_COMMA: "fewer_bars",
    pygame.K_LEFT: "fewer_bars",
    pygame.K_EQUALS: "more_sensitive",
    pygame.K_KP_PLUS: "more_sensitive",
    pygame.K_UP: "more_sensitive",
    pygame.K_MINUS: "less_sensitive",
    pygame.K_KP_MINUS: "less_sensitive",
    pygame.K_DOWN: "less_sensitive",
    pygame.K_a: "toggle_auto_gain",
    pygame.K_g: "toggle_glow",
    pygame.K_b: "toggle_beat_fx",
    pygame.K_RIGHTBRACKET: "more_beats",
    pygame.K_LEFTBRACKET: "fewer_beats",
    pygame.K_t: "toggle_trails",
    pygame.K_f: "toggle_fullscreen",
    pygame.K_h: "toggle_help",
}

HELP_LINE = ("SPACE mode  C colors  , . bars  - = sens  A autogain  G glow  "
             "B beat  [ ] beat sens  T trails  F full  H hide  ESC quit")
