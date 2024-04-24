import serial, time

from sardana import State
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Description, DefaultValue


class KepcoMotorControllerSerialGPIB(MotorController):
    ctrl_properties = {'Port': {Type: str, Description: 'ttyDevice', DefaultValue: '/dev/ttyKepco'}}
    
    MaxDevice = 1
    
    def __init__(self, inst, props, *args, **kwargs):
        #super(kepcoController, self).__init__(
        super(KepcoMotorControllerSerialGPIB, self).__init__(
            inst, props, *args, **kwargs)

        # connection settings
        BAUDRATE = 115200
        PARITY = serial.PARITY_NONE # serial.PARITY_NONE, serial.PARITY_ODD, serial.PARITY_EVEN
        FLOWCONTROL = "none" # "none", "software", "hardware", "sw/hw"
        TIMEOUT = 0
        BYTESIZE = 8
        STOPBITS = 1
    
        # configure serial
        self.serial = serial.Serial()
        self.serial.baudrate = BAUDRATE
        self.serial.port = self.Port
        self.serial.parity = PARITY
        self.serial.bytesize = BYTESIZE
        self.serial.stopbits = STOPBITS
        self.serial.timeout = TIMEOUT

        if FLOWCONTROL == "none":
            self.serial.xonxoff = 0
            self.serial.rtscts = 0
        elif FLOWCONTROL == "software":
            self.serial.xonxoff = 1
            self.serial.rtscts = 0
        elif FLOWCONTROL == "hardware":
            self.serial.xonxoff = 0
            self.serial.rtscts = 1
        elif FLOWCONTROL == "sw/hw":
            self.serial.xonxoff = 1
            self.serial.rtscts = 1

        # open serial port
        self.serial.open()
        
        self.serial.write("++addr 6\n".encode("utf-8"))
        time.sleep(0.05)
        
        print ('Kepco Initialization')
        self.serial.write("*IDN?\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        idn = self.serial.read_all()
        idn = idn.decode("utf-8")

        if idn:
            print (idn)
            print ('Kepco is initialized!')
        else:
            print ('Kepco is NOT initialized!')
        # initialize hardware communication        
        self._motors = {}
        self._isMoving = False
        self._moveStartTime = None
        self._threshold = 0.1
        self._target = None
        self._timeout = 10

    def AddDevice(self, axis):
        self._motors[axis] = True
        self.serial.write("FUNC:MODE CURR\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        self.serial.write("CURR:MODE FIX\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        self.serial.write("CURR:LIM:NEG 5\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        self.serial.write("CURR:LIM:POS 5\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        self.serial.write("OUTP ON\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        
        res = self.serial.read_all()
        res = res.decode("utf-8")

    def DeleteDevice(self, axis):
        
        # close serial port
        self.serial.close()
        
        del self._motors[axis]

    def StateOne(self, axis):
        limit_switches = MotorController.NoLimitSwitch
        pos = self.ReadOne(axis)
        now = time.time()
        
        if self._isMoving == False:
            state = State.On
        elif self._isMoving:
            if (abs(pos-self._target) > self._threshold):
                # moving and not in threshold window
                if (now-self._moveStartTime) < self._timeout:
                    # before timeout
                    state = State.Moving
                else:
                    # after timeout
                    self._log.warning('Kepco Timeout')
                    self._isMoving = False
                    state = State.On
            elif (abs(pos-self._target) <= self._threshold):
                self._isMoving = False
                state = State.On
        else:
            state = State.Fault
        
        return state, 'some text', limit_switches

    def ReadOne(self, axis):
        self.serial.write("MEAS:CURR?\n".encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        res = self.serial.read_all()
        res = res.decode("utf-8")
        return float(res)

    def StartOne(self, axis, position):
        self._moveStartTime = time.time()
        self._isMoving = True
        self._target = position
        cmd = 'CURR {:f}'.format(position)+'\n'
        self.serial.write(cmd.encode("utf-8"))
        #self.serial.flush()
        time.sleep(0.05)
        res = self.serial.read_all()
        res = res.decode("utf-8")

    def StopOne(self, axis):
        pass

    def AbortOne(self, axis):
        pass

    
