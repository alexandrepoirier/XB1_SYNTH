import pygame
import platform

PLATFORM = platform.uname()[0].upper()

pygame.font.init()
pygame.init()

if PLATFORM == 'WINDOWS':
    DEFAULT_FONT = pygame.font.SysFont('Courier New', 12)
    HUGE_FONT = pygame.font.SysFont('Courier New', 24)
elif PLATFORM == 'DARWIN':
    info = pygame.display.Info()
    if info.current_w >= 2560:
        DEFAULT_FONT = pygame.font.SysFont('Helvetica', 18)
        HUGE_FONT = pygame.font.SysFont('Helvetica', 30)
    else:
        DEFAULT_FONT = pygame.font.SysFont('Helvetica', 12)
        HUGE_FONT = pygame.font.SysFont('Helvetica', 24)
HUGE_FONT.set_bold(True)

COLORS = {'black':pygame.Color('black'), 'white':pygame.Color('white'), 'red':pygame.Color('red')}
DEFAULT_COLOR = COLORS['white']


class Struct(dict):
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        self.__dict__.update(**kwargs)

    def __getitem__(self, item):
        return getattr(self, item)

    def getDynamicValue(self, name):
        def getter():
            return getattr(self, name)
        return getter


def draw_button(button, screen):
    rect = button.rect
    value = 0 if button.value else 1
    pygame.draw.rect(screen, COLORS['white'], rect, value)


def draw_xbox_button(button, screen):
    ox, oy = origin = button.rect.center
    radius = button.rect.h
    value = 0 if button.value else 1
    pygame.draw.circle(screen, COLORS['white'], origin, radius, value)


def draw_stick(stick, screen):
    ox, oy = origin = stick.rect.center
    radius = stick.rect.h
    point_radius = 5
    x, y = int(round(ox + stick.x * radius)), int(round(oy - stick.y * radius))
    pygame.draw.circle(screen, COLORS['white'], origin, radius, 1)
    pygame.draw.circle(screen, COLORS['red'], (x, y), point_radius, 0)


def draw_trigger(trigger, screen):
    rect = trigger.rect
    pygame.draw.rect(screen, COLORS['white'], rect, 1)
    if trigger.value > 0.0:
        r = rect.copy()
        r.h = rect.h * trigger.value
        r.bottom = rect.bottom
        screen.fill(COLORS['white'], r)


def draw_d_pad(d_pad, screen):
    pygame.draw.circle(screen, COLORS['white'], d_pad[0, 0].rect.center, 40, 1)
    for pad in d_pad.values():
        if pad.value:
            pygame.draw.rect(screen, COLORS['white'], pad.rect, 0)
    pygame.draw.rect(screen, COLORS['white'], d_pad[0, 0].rect, 1)


def stick_center_snap(value, snap=0.1):
    # Feeble attempt to compensate for calibration and loose stick.
    if value >= snap or value <= -snap:
        return value
    else:
        return 0.0


def draw_text(text, pos, screen, font=DEFAULT_FONT, color=DEFAULT_COLOR):
    textsurface = font.render(text, True, color)
    screen.blit(textsurface, pos)
    return font.get_linesize()


def draw_values(controller_values, analysis_values, screen):
    column_spacing = 130
    x_margin = 20
    y_margin = 330

    # Controller values display
    text_height = draw_text('RAW Data', (x_margin, y_margin), screen)
    to_draw = ['LX', 'LY', 'RX', 'RY', 'LT', 'RT']
    for key in to_draw:
        text_height += draw_text('/{} : {: .4f}'.format(key, controller_values[key]),
                                 (x_margin, y_margin + text_height), screen)
    draw_text('/DPAD : {}'.format(controller_values['DPAD']), (x_margin, y_margin + text_height), screen)

    # Analysis values display
    text_height = draw_text('Analysis Data', (x_margin + column_spacing, y_margin), screen)
    to_draw = analysis_values.keys()
    for key in to_draw:
        text_height += draw_text('/{} : {:.4f}'.format(key, analysis_values[key]),
                                 (x_margin + column_spacing, y_margin + text_height), screen)


def draw_osc_satus(OSC_STATUS, OSC_STATUS_CODE, IP_ADDRESS, CONTROLLER_ROOT_ADDRESS, ANALYSIS_ROOT_ADDRESS, OSC_PORT, screen):
    x, y = (380, 330)
    text_height = draw_text('OSC Status : {}'.format(OSC_STATUS[OSC_STATUS_CODE]), (x, y), screen)
    text_height += draw_text('CLIENT IP : {}'.format(IP_ADDRESS), (x, y + text_height), screen)
    text_height += draw_text('OSC PORT : {}'.format(OSC_PORT), (x, y + text_height), screen)
    text_height += draw_text('CONTROLLER ROOT ADDRESS : {}'.format(CONTROLLER_ROOT_ADDRESS), (x, y + text_height), screen)
    text_height += draw_text('ANALYSIS ROOT ADDRESS : {}'.format(ANALYSIS_ROOT_ADDRESS), (x, y + text_height), screen)
