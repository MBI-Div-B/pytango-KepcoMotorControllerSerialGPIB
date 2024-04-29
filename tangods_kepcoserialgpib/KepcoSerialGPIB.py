#!/usr/bin/python3 -u
# coding: utf8
from tango import AttrWriteType, DevState, DispLevel
from tango.server import Device, attribute, command, device_property

import serial, time

class KepcoSerialGPIB(Device):
    # -----------------
    # Device Properties
    # -----------------

    Port = device_property(
        dtype=str,
        doc='e.g., /dev/ttyKepco'
    )

    Baudrate = device_property(
        dtype=int,
        default_value=115200,
    )

    Address = device_property(
        dtype=str,
        doc='GPIB device address, e.g., 6'
    )

    # ----------
    # Attributes
    # ----------

    current = attribute(
        label="current",
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit="A",
    )
    
    # ---------------
    # General methods
    # ---------------
    
    def init_device(self):
        self.info_stream("Device initialization...")
        Device.init_device(self)
        self.set_state(DevState.INIT)

        # configure serial
        self.serial = serial.Serial()
        self.serial.baudrate = self.Baudrate
        self.serial.port = self.Port
        self.serial.parity = serial.PARITY_NONE
        self.serial.bytesize = 8
        self.serial.stopbits = 1
        self.serial.timeout = 0
        self.serial.xonxoff = 0
        self.serial.rtscts = 0

        # initialize local variables
        self._isMoving = False
        self._moveStartTime = time.time()
        self._threshold = 0.02
        self._target = 0
        self._timeout = 10

        # open serial port
        try:
            if self.serial.isOpen():
                self.serial.close()
            self.serial.open()

            self.info_stream("Connected to serial port {:s}".format(self.Port))

            self.serial.write(("++addr "+self.Address+"\n").encode("utf-8"))
            self.serial.flush()

            self.info_stream("Looking for GPIB device...")
            self.serial.write("*IDN?\n".encode("utf-8"))
            self.serial.flush()
            time.sleep(0.05)
            self.idn = self.serial.read_all().decode("utf-8")

            if self.idn:
                self.info_stream(self.idn)
                self.info_stream("GPIB device found. Initializing power supply...")

                self.serial.write("FUNC:MODE CURR\n".encode("utf-8"))
                self.serial.flush()
                time.sleep(0.05)
                self.serial.write("CURR:MODE FIX\n".encode("utf-8"))
                self.serial.flush()
                time.sleep(0.05)
                self.serial.write("CURR:LIM:NEG 5\n".encode("utf-8"))
                self.serial.flush()
                time.sleep(0.05)
                self.serial.write("CURR:LIM:POS 5\n".encode("utf-8"))
                self.serial.flush()
                time.sleep(0.05)
                self.serial.write("OUTP ON\n".encode("utf-8"))
                self.serial.flush()
                time.sleep(0.05)
                
                res = self.serial.read_all()
                res = res.decode("utf-8")

                self.info_stream("Power supply is initialized!")

                self.set_state(DevState.ON)
                self.set_status(self.idn+"Power supply is in ON state.")
            else:
                self.error_stream("Power supply is in OFF state.")
                self.set_state(DevState.OFF)
                self.set_status("Power supply is in OFF state.")
        except:
            self.error_stream("Failed to open serial communication with {:s}".format(self.Port))
            self.set_state(DevState.FAULT)
            self.set_status("Failed to open serial communication with {:s}".format(self.Port))

    def always_executed_hook(self):
        pass

    def dev_state(self):
        if self.get_state() == DevState.OFF:
            return DevState.OFF

        if self._isMoving == False:
            self.set_status(self.idn+"Power supply is in ON state.")
            return DevState.ON
        else:
            pos = self.read_current()
            now = time.time()
            if (abs(pos-self._target) > self._threshold):
                # moving and not in threshold window
                if (now-self._moveStartTime) < self._timeout:
                    # before timeout
                    self.set_status(self.idn+"Power supply is in MOVING state.")
                    return DevState.MOVING
                else:
                    # after timeout
                    self.error_stream("Power supply timeout")
                    #self._isMoving = False
                    self.set_status(self.idn+"Timeout occurred! Power supply is in ALARM state.")
                    return DevState.ALARM
            elif (abs(pos-self._target) <= self._threshold):
                self._isMoving = False
                return DevState.ON

    def delete_device(self):
        self.serial.close()
        self.set_state(DevState.OFF)

    # ------------------
    # Attributes methods
    # ------------------

    def read_current(self):
        if self.get_state() == DevState.OFF:
            return None

        self.serial.write("MEAS:CURR?\n".encode("utf-8"))

        res = ""
        timestamp = time.time()
        while not "\n" in res:
            self.serial.flush()
            line = self.serial.readline().decode("utf-8")
            res += line
            if (time.time()-timestamp) > 1:
                self.set_state(DevState.OFF)
                self.set_status("Power supply is in OFF state.")
                return None

        return float(res)
    
    def write_current(self, value):
        if self.get_state() == DevState.OFF:
            self.init_device()
            if self.get_state() != DevState.ON:
                return None

        self._moveStartTime = time.time()
        self._isMoving = True
        self._target = value
        cmd = 'CURR {:f}'.format(value)+'\n'
        self.serial.write(cmd.encode("utf-8"))

        res = ""
        timestamp = time.time()
        while not "\n" in res:
            self.serial.flush()
            line = self.serial.readline().decode("utf-8")
            res += line
            if (time.time()-timestamp) > 1:
                print("timeout")
                self.set_state(DevState.OFF)
                self.set_status("Power supply is in OFF state.")
                break

# start the server
if __name__ == "__main__":
    KepcoSerialGPIB.run_server()
