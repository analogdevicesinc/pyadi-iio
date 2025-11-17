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
// *********     Bulk Read and Bulk Write Example      *********
//
//
// Available Dynamixel model on this example : All models using Protocol 2.0
// This example is designed for using two Dynamixel PRO 54-200, and an USB2DYNAMIXEL.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel PRO properties are already set as %% ID : 1 and 2 / Baudnum : 1 (Baudrate : 57600)
//

using System;
using System.Runtime.InteropServices;
using dynamixel_sdk;

namespace bulk_read_write
{
  class BulkReadWrite
  {
    // Control table address
    public const int ADDR_PRO_TORQUE_ENABLE           = 562;                // Control table address is different in Dynamixel model
    public const int ADDR_PRO_LED_RED                 = 563;
    public const int ADDR_PRO_GOAL_POSITION           = 596;
    public const int ADDR_PRO_PRESENT_POSITION        = 611;


    // Data Byte Length
    public const int LEN_PRO_LED_RED                  = 1;
    public const int LEN_PRO_GOAL_POSITION            = 4;
    public const int LEN_PRO_PRESENT_POSITION         = 4;

    // Protocol version
    public const int PROTOCOL_VERSION                = 2;                   // See which protocol version is used in the Dynamixel

    // Default setting
    public const int DXL1_ID                         = 1;                   // Dynamixel ID: 1
    public const int DXL2_ID                         = 2;                   // Dynamixel ID: 2
    public const int BAUDRATE                        = 57600;
    public const string DEVICENAME                   = "COM1";              // Check which port is being used on your controller
                                                                            // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    public const int TORQUE_ENABLE                   = 1;                   // Value for enabling the torque
    public const int TORQUE_DISABLE                  = 0;                   // Value for disabling the torque
    public const int DXL_MINIMUM_POSITION_VALUE      = -150000;             // Dynamixel will rotate between this value
    public const int DXL_MAXIMUM_POSITION_VALUE      = 150000;              // and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
    public const int DXL_MOVING_STATUS_THRESHOLD     = 20;                  // Dynamixel moving status threshold

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

      // Initialize GroupBulkWrite Struct
      int groupwrite_num = dynamixel.groupBulkWrite(port_num, PROTOCOL_VERSION);

      // Initialize Groupbulkread Structs
      int groupread_num = dynamixel.groupBulkRead(port_num, PROTOCOL_VERSION);

      int index = 0;
      int dxl_comm_result = COMM_TX_FAIL;                                   // Communication result
      bool dxl_addparam_result = false;                                     // AddParam result
      bool dxl_getdata_result = false;                                      // GetParam result
      int[] dxl_goal_position = new int[2]{ DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE };         // Goal position

      byte dxl_error = 0;                                                   // Dynamixel error
      byte[] dxl_led_value = new byte[2]{ 0x00, 0xFF };                     // Dynamixel LED value for write
      Int32 dxl1_present_position = 0;                                      // Present position
      byte dxl2_led_value_read = 0;                                         // Dynamixel moving status

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
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL1_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_ENABLE);
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
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL2_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_ENABLE);
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
      dxl_addparam_result = dynamixel.groupBulkReadAddParam(groupread_num, DXL1_ID, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION);
      if (dxl_addparam_result != true)
      {
        Console.WriteLine("[ID: {0}] groupBulkRead addparam failed", DXL1_ID);
        return;
      }

      // Add parameter storage for Dynamixel#2 present moving value
      dxl_addparam_result = dynamixel.groupBulkReadAddParam(groupread_num, DXL2_ID, ADDR_PRO_LED_RED, LEN_PRO_LED_RED);
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

        // Add parameter storage for Dynamixel#1 goal position
        dxl_addparam_result = dynamixel.groupBulkWriteAddParam(groupwrite_num, DXL1_ID, ADDR_PRO_GOAL_POSITION, LEN_PRO_GOAL_POSITION, (UInt32)dxl_goal_position[index], LEN_PRO_GOAL_POSITION);
        if (dxl_addparam_result != true)
        {
          Console.WriteLine("[ID: {0}] groupBulkWrite addparam failed", DXL1_ID);
          return;
        }

        // Add parameter storage for Dynamixel#2 LED value
        dxl_addparam_result = dynamixel.groupBulkWriteAddParam(groupwrite_num, DXL2_ID, ADDR_PRO_LED_RED, LEN_PRO_LED_RED, dxl_led_value[index], LEN_PRO_LED_RED);
        if (dxl_addparam_result != true)
        {
          Console.WriteLine("[ID: {0}] groupBulkWrite addparam failed", DXL2_ID);
          return;
        }

        // Bulkwrite goal position and LED value
        dynamixel.groupBulkWriteTxPacket(groupwrite_num);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));

        // Clear bulkwrite parameter storage
        dynamixel.groupBulkWriteClearParam(groupwrite_num);

        do
        {
          // Bulkread present position and moving status
          dynamixel.groupBulkReadTxRxPacket(groupread_num);
          if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));

          dxl_getdata_result = dynamixel.groupBulkReadIsAvailable(groupread_num, DXL1_ID, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION);
          if (dxl_getdata_result != true)
          {
            Console.WriteLine("[ID: {0}] groupBulkRead getdata failed", DXL1_ID);
            return;
          }

          dxl_getdata_result = dynamixel.groupBulkReadIsAvailable(groupread_num, DXL2_ID, ADDR_PRO_LED_RED, LEN_PRO_LED_RED);
          if (dxl_getdata_result != true)
          {
            Console.WriteLine("[ID: {0}] groupBulkRead getdata failed", DXL2_ID);
            return;
          }

          // Get Dynamixel#1 present position value
          dxl1_present_position = (Int32)dynamixel.groupBulkReadGetData(groupread_num, DXL1_ID, ADDR_PRO_PRESENT_POSITION, LEN_PRO_PRESENT_POSITION);

          // Get Dynamixel#2 moving status value
          dxl2_led_value_read = (byte)dynamixel.groupBulkReadGetData(groupread_num, DXL2_ID, ADDR_PRO_LED_RED, LEN_PRO_LED_RED);

          Console.WriteLine("[ID: {0}] Present Position : {1} [ID: {2}] LED Value : {3}", DXL1_ID, dxl1_present_position, DXL2_ID, dxl2_led_value_read);

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
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL1_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_DISABLE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
      }

      // Disable Dynamixel#2 Torque
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL2_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_DISABLE);
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
