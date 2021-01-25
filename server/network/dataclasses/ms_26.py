from dataclasses import dataclass
from typing import List
from server.network.dataclasses.typing_enforcement import enforce_types
from server.network.dataclasses.ms_pre_26 import MS_Pre_26


@enforce_types
@dataclass
class MS_26(MS_Pre_26):
    showname: str = ""
    charid_pair: str = ""
    offset_pair: str = ""
    _nonint_pre: int = 0

    @property
    def nonint_pre(self) -> int:
        return self._nonint_pre

    @nonint_pre.setter
    def nonint_pre(self, value):
        if value == 1:
            self._nonint_pre = value
            if self.objection_modifier in (1, 2, 3, 4, 23):
                if self.anim_type == 1 or self.anim_type == 2:
                    self.anim_type = 0
                elif self.anim_type == 6:
                    self.anim_type = 5

    @classmethod
    def from_args(cls, args):
        return cls(msg_type=args[0], pre=args[1], folder=args[2], anim=args[3], text=args[4], pos=args[5], sfx=args[6], anim_type=int(args[7]), cid=int(args[8]), sfx_delay=int(args[9]), objection_modifier=args[10], evidence=int(args[11]), flip=int(args[12]), ding=int(args[13]), color=int(args[14]), showname=args[15], charid_pair=args[16], offset_pair=args[17], _nonint_pre=int(args[18]))
