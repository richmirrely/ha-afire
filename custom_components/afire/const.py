"""Constants for the AFIRE Fireplace integration."""

from typing import Final

DOMAIN: Final = "afire"
DEFAULT_NAME: Final = "AFIRE Fireplace"
DEFAULT_PORT: Final = 12416
DEFAULT_SCAN_INTERVAL: Final = 20

CONF_PASSCODE: Final = "passcode"

PLATFORMS: Final = ["switch", "number", "light"]

PRODUCT_KEY: Final = "e2313fe07bca48fb82861d5f961993c5"

# Writable attribute flag bits from the Gizwits datapoint definition.
FLAG_POWER: Final = 1 << 0
FLAG_ORANGE_LIGHT: Final = 1 << 1
FLAG_RGB_POWER: Final = 1 << 2
FLAG_COLORS: Final = sum(1 << bit for bit in range(3, 18))
FLAG_SMOOTH: Final = 1 << 18
FLAG_FADE1: Final = 1 << 19
FLAG_FADE2: Final = 1 << 20
FLAG_EFFECTS: Final = FLAG_SMOOTH | FLAG_FADE1 | FLAG_FADE2
FLAG_FLAME: Final = 1 << 21
FLAG_SPEED: Final = 1 << 22

COLOR_KEYS: Final = (
    "RED_KEY1",
    "RED_KEY2",
    "RED_KEY3",
    "RED_KEY4",
    "RED_KEY5",
    "GREEN_KEY1",
    "GREEN_KEY2",
    "GREEN_KEY3",
    "GREEN_KEY4",
    "GREEN_KEY5",
    "BLUE_KEY1",
    "BLUE_KEY2",
    "BLUE_KEY3",
    "BLUE_KEY4",
    "BLUE_KEY5",
)

# Colours sampled from the original AFIRE React Native template assets.
COLOR_RGB: Final = {
    "RED_KEY1": (240, 16, 27),
    "RED_KEY2": (213, 39, 22),
    "RED_KEY3": (249, 64, 30),
    "RED_KEY4": (249, 126, 36),
    "RED_KEY5": (251, 187, 45),
    "GREEN_KEY1": (26, 175, 30),
    "GREEN_KEY2": (28, 160, 27),
    "GREEN_KEY3": (31, 176, 168),
    "GREEN_KEY4": (19, 124, 225),
    "GREEN_KEY5": (7, 75, 88),
    "BLUE_KEY1": (13, 36, 246),
    "BLUE_KEY2": (16, 81, 248),
    "BLUE_KEY3": (94, 75, 141),
    "BLUE_KEY4": (96, 97, 141),
    "BLUE_KEY5": (191, 78, 143),
}

EFFECT_SMOOTH: Final = "Smooth"
EFFECT_FADE1: Final = "Fade 1"
EFFECT_FADE2: Final = "Fade 2"
EFFECTS: Final = (EFFECT_SMOOTH, EFFECT_FADE1, EFFECT_FADE2)

EFFECT_TO_FLAG: Final = {
    EFFECT_SMOOTH: FLAG_SMOOTH,
    EFFECT_FADE1: FLAG_FADE1,
    EFFECT_FADE2: FLAG_FADE2,
}
