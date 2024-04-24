from .KepcoMotorControllerSerialGPIB import KepcoMotorControllerSerialGPIB


def main():
    import sys
    import tango.server

    args = ["KepcoMotorControllerSerialGPIB"] + sys.argv[1:]
    tango.server.run((KepcoMotorControllerSerialGPIB,), args=args)
