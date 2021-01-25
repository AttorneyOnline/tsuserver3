from dataclasses import dataclass
from server.network.dataclasses.typing_enforcement import enforce_types
from server.network.dataclasses.ms_pre_26 import MS_Pre_26

@enforce_types
@dataclass
class MS_26(MS_Pre_26):
    showname: str = ""
    charid_pair: str = ""
    offset_pair: str = ""
    nonint_pre: int = 0

    @classmethod
    def from_args(cls, args):
        return cls(msg_type=args[0], pre=args[1], folder=args[2], anim=args[3], text=args[4], pos=args[5], sfx=args[6], anim_type=int(args[7]), cid=int(args[8]), sfx_delay=int(args[9]), objection_modifier=args[10], evidence=int(args[11]), flip=int(args[12]), ding=int(args[13]), color=int(args[14]), showname=args[15], charid_pair=args[16], offset_pair=args[17], nonint_pre=int(args[18]))
