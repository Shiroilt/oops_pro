from hardware.dispenser import BaseDispenser

class SpiralDispenser(BaseDispenser):
    """Concrete implementation of a spiral-based dispenser."""
    def get_capabilities(self) -> list:
        caps = super().get_capabilities()
        if "spiral_mechanism" not in caps:
            caps.append("spiral_mechanism")
        return caps

class RoboticArmDispenser(BaseDispenser):
    """Concrete implementation of a robotic arm dispenser."""
    def get_capabilities(self) -> list:
        caps = super().get_capabilities()
        if "robotic_arm" not in caps:
            caps.append("robotic_arm")
        return caps

class ConveyorDispenser(BaseDispenser):
    """Concrete implementation of a conveyor belt dispenser."""
    def get_capabilities(self) -> list:
        caps = super().get_capabilities()
        if "conveyor_belt" not in caps:
            caps.append("conveyor_belt")
        return caps
