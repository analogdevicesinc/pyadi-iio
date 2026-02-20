/*******************************************************************************
* Copyright 2017 ROBOTIS CO., LTD.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/

/* Author: Ryu Woon Jung (Leon) */

//
// *********     Factory Reset Example      *********
//
//
// Available Dynamixel model on this example : All models using Protocol 1.0
// This example is designed for using a Dynamixel MX-28, and an USB2DYNAMIXEL.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel PRO properties are already set as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
//

// Be aware that:
// This example resets all properties of Dynamixel to default values, such as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
//

using System;
using System.Runtime.InteropServices;
using System.Threading;
using dynamixel_sdk;

namespace reset
{
  class Reset
  {
    // Control table address
    public const int ADDR_MX_BAUDRATE                = 4;                   // Control table address is different in Dynamixel model

    // Protocol version
    public const int PROTOCOL_VERSION                = 1;                   // See which protocol version is used in the Dynamixel

    // Default setting
    public const int DXL_ID                          = 1;                   // Dynamixel ID: 1
    public const int BAUDRATE                        = 57600;
    public const string DEVICENAME                   = "COM1";              // Check which port is being used on your controller
                                                                            // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    public const int FACTORYRST_DEFAULTBAUDRATE      = 57600;               // Dynamixel baudrate set by factoryreset
    public const int NEW_BAUDNUM                     = 1;                   // New baudnum to recover Dynamixel baudrate as it was
    public const byte OPERATION_MODE                 = 0x00;                // Mode is unavailable in Protocol 1.0 Reset

    public const int COMM_SUCCESS                    = 0;                   // Communication Success result value
    public const int COMM_TX_FAIL                    = -1001;               // Communication Tx Failed

    static void Main(string[] args)
    {
      // Initialize PortHandler Structs
      // Set the port path
      // Get methods and members of PortHandlerLinux or PortHandlerWindows
      int port_num = dynamixel.portHandler(DEVICENAME);

      // Initialize PacketHandler Structs
      dynamixel.packetHandler();

      int dxl_comm_result = COMM_TX_FAIL;                                   // Communication result

      byte dxl_error = 0;                                                   // Dynamixel error
      byte dxl_baudnum_read;                                                // Read baudnum

      // Open port
      if (dynamixel.openPort(port_num))
      {
        Console.WriteLine("Succeeded to open the port!");
      }
      else
      {
        Console.WriteLine("Failed to open the port!");
        Console.WriteLine("Press any key to terminate...");
        Console.ReadKey();
        return;
      }

      // Set port baudrate
      if (dynamixel.setBaudRate(port_num, BAUDRATE))
      {
        Console.WriteLine("Succeeded to change the baudrate!");
      }
      else
      {
        Console.WriteLine("Failed to change the baudrate!");
        Console.WriteLine("Press any key to terminate...");
        Console.ReadKey();
        return;
      }

      // Read present baudrate of the controller
      Console.WriteLine("Now the controller baudrate is : {0}", dynamixel.getBaudRate(port_num));

      // Try factoryreset
      Console.WriteLine("[ID: {0}] Try factoryreset : ", DXL_ID);
      dynamixel.factoryReset(port_num, PROTOCOL_VERSION, DXL_ID, OPERATION_MODE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine("Aborted");
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
        return;
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }

      // Wait for reset
      Console.WriteLine("Wait for reset...");
      Thread.Sleep(2000);

      Console.WriteLine("[ID: {0}] factoryReset Success!", DXL_ID);

      // Set controller baudrate to dxl default baudrate
      if (dynamixel.setBaudRate(port_num, FACTORYRST_DEFAULTBAUDRATE))
      {
        Console.WriteLine("Succeed to change the controller baudrate to : {0}", FACTORYRST_DEFAULTBAUDRATE);
      }
      else
      {
        Console.WriteLine("Failed to change the controller baudrate");
        Console.WriteLine("Press any key to terminate...");
        Console.ReadKey();
        return;
      }

      // Read Dynamixel baudnum
      dxl_baudnum_read = dynamixel.read1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_MX_BAUDRATE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }
      else
      {
        Console.WriteLine("[ID: {0}] Dynamixel baudnum is now : {1}", DXL_ID, dxl_baudnum_read);
      }

      // Write new baudnum
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_MX_BAUDRATE, NEW_BAUDNUM);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }
      else
      {
        Console.WriteLine("[ID: {0}] Set Dynamixel baudnum to : {1}", DXL_ID, NEW_BAUDNUM);
      }

      // Set port baudrate to BAUDRATE
      if (dynamixel.setBaudRate(port_num, BAUDRATE))
      {
        Console.WriteLine("Succeed to change the controller baudrate to : {0}", BAUDRATE);
      }
      else
      {
        Console.WriteLine("Failed to change the controller baudrate");
        Console.WriteLine("Press any key to terminate...");
        Console.ReadKey();
        return;
      }

      Thread.Sleep(200);

      // Read Dynamixel baudnum
      dxl_baudnum_read = dynamixel.read1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_MX_BAUDRATE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }
      else
      {
        Console.WriteLine("[ID: {0}] Dynamixel Baudnum is now : {1}", DXL_ID, dxl_baudnum_read);
      }

      // Close port
      dynamixel.closePort(port_num);

      return;
    }
  }
}
