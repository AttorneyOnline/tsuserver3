from dataclasses import dataclass
from server.network.dataclasses.typing_enforcement import enforce_types
from typing import Union
@enforce_types
@dataclass
class MS_Pre_26:
    msg_type: str
    pre: str
    folder: str
    anim: str
    text: str
    pos: str
    sfx: str
    anim_type: int
    cid: int
    sfx_delay: int
    objection_modifier: Union[str, int]
    evidence: int
    flip: int
    ding: int
    color: int

    @classmethod
    def from_args(cls, args):
        return cls(msg_type=args[0], pre=args[1], folder=args[2], anim=args[3], text=args[4], pos=args[5], sfx=args[6], anim_type=int(args[7]), cid=int(args[8]), sfx_delay=int(args[9]), objection_modifier=args[10], evidence=int(args[11]), flip=int(args[12]), ding=int(args[13]), color=int(args[14]))


