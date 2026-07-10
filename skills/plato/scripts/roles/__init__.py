from .designer import DesignerStrategy
from .planner import PlannerStrategy
from .coder import CoderStrategy

ROLE_STRATEGIES: dict = {
    "designer": DesignerStrategy(),
    "planner": PlannerStrategy(),
    "coder": CoderStrategy(),
}
