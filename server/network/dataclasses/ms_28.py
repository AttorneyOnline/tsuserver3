from dataclasses import dataclass
from server.network.dataclasses.ms_26 import MS_26
from server.network.dataclasses.typing_enforcement import enforce_types

@enforce_types
@dataclass
class MS_28(MS_26):
    sfx_looping: str = "0"
    screenshake: int = 0
    frames_shake: str = ""
    frames_realization: str = ""
    frames_sfx: str = ""
    additive: int = 0
    effect: str = ""

    @classmethod
    def from_args(cls, args):
        return cls(msg_type=args[0], pre=args[1], folder=args[2], anim=args[3], text=args[4], pos=args[5], sfx=args[6], anim_type=int(args[7]), cid=int(args[8]), sfx_delay=int(args[9]), objection_modifier=args[10], evidence=int(args[11]), flip=int(args[12]), ding=int(args[13]), color=int(args[14]), showname=args[15], charid_pair=args[16], offset_pair=args[17], nonint_pre=int(args[18]), sfx_looping=args[19], screenshake=int(args[20]), frames_shake=args[21], frames_realization=args[22], frames_sfx=args[23], additive=int(args[24]), effect=args[25])

