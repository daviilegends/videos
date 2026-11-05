"""Positions tuned to each generated background, in background pixels, and the story beats shared by picture and sound."""
import json
import math
from pathlib import Path

LAYOUT = {
    "lobby": dict(tint=0xFFFFFFFF, light=0xFFD8D8C4, doors=(642, 292, 899, 617)),
    "cabina": dict(tint=0xFFFFFFFF, light=0xFFC4DCCC),
    "panel": dict(tint=0xFFFFFFFF, light=0xFFBCD8D0, buttons=[(863, 468), (926, 307), (863, 307), (600, 376), (926, 468)]),
    "techo": dict(tint=0xFFFFFFFF, light=0xFFFFFFFF),
    "hueco": dict(tint=0xFFFFFFFF, light=0xFFFFFFFF, car=(775, 550)),
    "puertas": dict(tint=0xFFFFFFFF, light=0xFFB8D8D0, doors=(571, 97, 971, 688)),
    "rejilla": dict(tint=0xFFFFFFFF, light=0xFFFFFFFF),
}


def beats(tl):
    """Times of the visible actions, derived from the sentences of the narration."""
    l = [x for s in tl["scenes"] for x in s["lines"]]
    cues = json.loads((Path(__file__).with_name("cues.json")).read_text(encoding="utf-8"))
    press = next(c["start"] for c in cues if c["text"].startswith("presionas el"))
    rise = next(c["start"] for c in cues if "comienzas" in c["text"].split()[0:1])
    return dict(lines=l, door_open=l[1]["start"], press=press, press_hit=press + .55, rise=rise, hit=l[3]["start"],
                lights=l[4]["start"], halt=l[4]["start"] + (l[4]["end"] - l[4]["start"]) * .55,
                presses=[l[5]["start"] + d for d in (.45, 1.05, 1.65)], push=l[7]["start"], vent=l[10]["start"],
                knocks=[l[15]["start"] + (math.pi / 2 + j * math.pi) / 12 for j in range(12)
                        if (math.pi / 2 + j * math.pi) / 12 < (l[16]["start"] - l[15]["start"]) * .55],
                alarm=l[22]["start"] + (l[23]["start"] - l[22]["start"]) * .38 * .4,
                doors=l[22]["start"] + (l[23]["start"] - l[22]["start"]) * .62)
