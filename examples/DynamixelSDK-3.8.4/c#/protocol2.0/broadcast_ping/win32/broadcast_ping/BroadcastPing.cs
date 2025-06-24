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
// *********     BroadcastPing Example      *********
//
//
// Available Dynamixel model on this example : All models using Protocol 2.0
// This example is designed for using a Dynamixel PRO 54-200, and an USB2DYNAMIXEL.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel PRO properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

using System;
using System.Runtime.InteropServices;
using dynamixel_sdk;

namespace broadcast_ping
{
  class BroadcastPing
  {
    // Protocol version
    public const int PROTOCOL_VERSION   = 2;                // See which protocol version is used in the Dynamixel

    // Default setting
    public const int BAUDRATE           = 57600;
    public const string DEVICENAME      = "COM1";           // Check which port is being used on your controller
                                                            // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    public const byte ESC_ASCII_VALUE   = 0x1b;

    public const int MAX_ID             = 252;              // Maximum ID value
    public const int COMM_SUCCESS       = 0;                // Communication Success result value
    public const int COMM_TX_FAIL       = -1001;            // Communication Tx Failed

    static void Main(string[] args)
    {
      // Initialize PortHandler Structs
      // Set the port path
      // Get methods and members of PortHandlerLinux or PortHandlerWindows
      int port_num = dynamixel.portHandler(DEVICENAME);

      // Initialize PacketHandler Structs
      dynamixel.packetHandler();

      int dxl_comm_result = COMM_TX_FAIL;                   // Communication result
      int id;

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

      // Try to broadcast ping the Dynamixel
      dynamixel.broadcastPing(port_num, PROTOCOL_VERSION);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));

      Console.WriteLine("Detected Dynamixel :");
      for (id = 0; id < MAX_ID; id++)
      {
        if (dynamixel.getBroadcastPingResult(port_num, PROTOCOL_VERSION, id))
          Console.WriteLine("[ID: {0}]", id);
      }

      // Close port
      dynamixel.closePort(port_num);

      return;
    }
  }
}
