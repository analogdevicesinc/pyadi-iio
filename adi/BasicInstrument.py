#from ADI_GPIB.GPIBObject import GpibInstrument

'''

Defines the core functionality for instruments

'''

class Instrument:
    def __init__(self, instrName, instrID, resourceManager):
        self.instrID = instrID
        self.instrName = instrName
        self.instrCtrl = resourceManager.open_resource(self.instrID)
        self.resourceManager = resourceManager
        #self.instrCtrl = GpibInstrument(self.instrID)

    def write(self, strToWrite): #wrapper for the writing to make code simpler
        self.instrCtrl.write(strToWrite)

    def Get_IDN(self):
        idn = str(self.query("*IDN?"))
        return idn

    def query(self, strToWrite):
        res = self.instrCtrl.query(strToWrite)
        return res

    def ask(self, strToWrite):
        res = self.instrCtrl.ask(strToWrite)
        return res

    def Set_ToLocalMode(self):
        raise Exception("Must override Set_ToLocalMode within specific instrument's class!")

    def Set_ToRemoteMode(self):
        raise Exception("Must override Set_ToRemoteMode within specific instrument's class!")

    def close(self):
        print "Closing connection to " + str(self)
        self.Set_ToLocalMode()
        self.instrCtrl.close()

    def __repr__(self):
        return (self.instrName + " @ " + self.instrID)


