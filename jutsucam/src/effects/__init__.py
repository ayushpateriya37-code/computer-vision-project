"""
src/effects package
--------------------
Exposes EFFECT_CLASSES: a registry mapping the effect key used in
config.JUTSU_REGISTRY[...]['effect'] to the concrete effect class that
implements it. vfx_engine.py uses this to instantiate the right effect
for whichever jutsu was just triggered.
"""

from src.effects.rasengan import RasenganEffect
from src.effects.chidori import ChidoriEffect
from src.effects.shadow_clone import ShadowCloneEffect
from src.effects.fire_dragon import FireDragonEffect
from src.effects.water_dragon import WaterDragonEffect
from src.effects.earth_release import EarthReleaseEffect

EFFECT_CLASSES = {
    "rasengan": RasenganEffect,
    "chidori": ChidoriEffect,
    "shadow_clone": ShadowCloneEffect,
    "fire_dragon": FireDragonEffect,
    "water_dragon": WaterDragonEffect,
    "earth_release": EarthReleaseEffect,
}
