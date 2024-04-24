from .KepcoSerialGPIB import KepcoSerialGPIB


def main():
    import sys
    import tango.server

    args = ["KepcoSerialGPIB"] + sys.argv[1:]
    tango.server.run((KepcoSerialGPIB,), args=args)
