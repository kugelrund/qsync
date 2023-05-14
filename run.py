import dataclasses
import datetime


@dataclasses.dataclass
class Run:
    name: str
    time: float
    date: datetime.date
    demo: str
    video: str
