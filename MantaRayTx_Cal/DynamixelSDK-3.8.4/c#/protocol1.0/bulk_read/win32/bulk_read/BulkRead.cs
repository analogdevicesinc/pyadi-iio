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
// *********     Bulk Read Example      *********
//
//
// Available Dynamixel model on this example : MX or X series set to Protocol 1.0
// This example is designed for using two Dynamixel MX-28, and an USB2DYNAMIXEL.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel MX properties are already set as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
//

using System;
using System.Runtime.InteropServices;
using dynamixel_sdk;

namespace bulk_read
{
  class BulkRead
  {
    // Control table address
    public const int ADDR_MX_TORQUE_ENABLE           = 24;                  // Control table address is different in Dynamixel model
    public const int ADDR_MX_GOAL_POSITION           = 30;
    public const int ADDR_MX_PRESENT_POSITION        = 36;
    public const int ADDR_MX_MOVING                  = 46;

    // Data Byte Length
    public const int LEN_MX_GOAL_POSITION            = 2;
    public const int LEN_MX_PRESENT_POSITION         = 2;
    public const int LEN_MX_MOVING                   = 1;

    // Protocol version
    public const int PROTOCOL_VERSION                = 1;                   // See which protocol version is used in the Dynamixel

    // Default setting
    public const int DXL1_ID                         = 1;                   // Dynamixel ID: 1
    public const int DXL2_ID                         = 2;                   // Dynamixel ID: 2
    public const int BAUDRATE                        = 57600;
    public const string DEVICENAME                   = "COM1";              // Check which port is being used on your controller
                                                                            // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    public const int TORQUE_ENABLE                   = 1;                   // Value for enabling the torque
    public const int TORQUE_DISABLE                  = 0;                   // Value for disabling the torque
    public const int DXL_MINIMUM_POSITION_VALUE      = 100;                 // Dynamixel will rotate between this value
    public const int DXL_MAXIMUM_POSITION_VALUE      = 4000;                // and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
    public const int DXL_MOVING_STATUS_THRESHOLD     = 10;                  // Dynamixel moving status threshold

    public const byte ESC_ASCII_VALUE                = 0x1b;

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

      // Initialize Groupbulkread Structs
      int group_num = dynamixel.groupBulkRead(port_num, PROTOCOL_VERSION);

      int index = 0;
      int dxl_comm_result = COMM_TX_FAIL;                                   // Communication result
      bool dxl_addparam_result = false;                                     // AddParam result
      bool dxl_getdata_result = false;                                      // GetParam result
      UInt16[] dxl_goal_position = new UInt16[2]{ DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE }; // Goal position

      byte dxl_error = 0;                                                   // Dynamixel error
      UInt16 dxl1_present_position = 0;                                     // Present position
      byte dxl2_moving = 0;                                                 // Dynamixel moving status

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

      // Enable Dynamixel#1 Torque
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL1_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE);
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
        Console.WriteLine("Dynamixel{0} has been successfully connected ", DXL1_ID);
      }

      // Enable Dynamixel#2 Torque
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL2_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE);
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
        Console.WriteLine("Dynamixel{0} has been successfully connected ", DXL1_ID);
      }

      // Add parameter storage for Dynamixel#1 present position value
      dxl_addparam_result = dynamixel.groupBulkReadAddParam(group_num, DXL1_ID, ADDR_MX_PRESENT_POSITION, LEN_MX_PRESENT_POSITION);
      if (dxl_addparam_result != true)
      {
        Console.WriteLine("[ID: {0}] groupBulkRead addparam failed", DXL1_ID);
        return;
      }

      // Add parameter storage for Dynamixel#2 present moving value
      dxl_addparam_result = dynamixel.groupBulkReadAddParam(group_num, DXL2_ID, ADDR_MX_MOVING, LEN_MX_MOVING);
      if (dxl_addparam_result != true)
      {
        Console.WriteLine("[ID: {0}] groupBulkRead addparam failed", DXL2_ID);
        return;
      }

      while (true)
      {
        Console.WriteLine("Press any key to continue! (or press ESC to quit!)");
        if (Console.ReadKey().KeyChar == ESC_ASCII_VALUE)
          break;

        // Write Dynamixel#1 goal position
        dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL1_ID, ADDR_MX_GOAL_POSITION, dxl_goal_position[index]);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
        {
          Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
        }
        else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
        {
          Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
        }

        // Write Dynamixel#2 goal position
        dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL2_ID, ADDR_MX_GOAL_POSITION, dxl_goal_position[index]);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
        {
          Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
        }
        else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
        {
          Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
        }

        do
        {
          // Bulkread present position and moving status
          dynamixel.groupBulkReadTxRxPacket(group_num);
          if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));

          dxl_getdata_result = dynamixel.groupBulkReadIsAvailable(group_num, DXL1_ID, ADDR_MX_PRESENT_POSITION, LEN_MX_PRESENT_POSITION);
          if (dxl_getdata_result != true)
          {
            Console.WriteLine("[ID: {0}] groupBulkRead getdata failed", DXL1_ID);
            return;
          }

          dxl_getdata_result = dynamixel.groupBulkReadIsAvailable(group_num, DXL2_ID, ADDR_MX_MOVING, LEN_MX_MOVING);
          if (dxl_getdata_result != true)
          {
            Console.WriteLine("[ID: {0}] groupBulkRead getdata failed", DXL2_ID);
            return;
          }

          // Get Dynamixel#1 present position value
          dxl1_present_position = (UInt16)dynamixel.groupBulkReadGetData(group_num, DXL1_ID, ADDR_MX_PRESENT_POSITION, LEN_MX_PRESENT_POSITION);

          // Get Dynamixel#2 moving status value
          dxl2_moving = (byte)dynamixel.groupBulkReadGetData(group_num, DXL2_ID, ADDR_MX_MOVING, LEN_MX_MOVING);

          Console.WriteLine("[ID: {0}] Present Position : {1} [ID: {2}] Is Moving : {3}", DXL1_ID, dxl1_present_position, DXL2_ID, dxl2_moving);

        } while (Math.Abs(dxl_goal_position[index] - dxl1_present_position) > DXL_MOVING_STATUS_THRESHOLD);

        // Change goal position
        if (index == 0)
        {
          index = 1;
        }
        else
        {
          index = 0;
        }
      }

      // Disable Dynamixel#1 Torque
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL1_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }

      // Disable Dynamixel#2 Torque
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL2_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }

      // Close port
      dynamixel.closePort(port_num);

      return;
    }
  }
}
