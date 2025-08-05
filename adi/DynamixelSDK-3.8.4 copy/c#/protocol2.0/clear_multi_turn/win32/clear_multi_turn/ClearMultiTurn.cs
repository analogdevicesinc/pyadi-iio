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

/* Author: Ki Jong Gil (Gilbert) */

//
// *********     Clear Multi-Turn Example      *********
//
//
// Available Dynamixel model on this example : Dynamixel X-series (firmware v42 or above)
// This example is designed for using a Dynamixel XM430-W350-R, and an U2D2.
// To use another Dynamixel model, such as MX series, see their details in E-Manual(emanual.robotis.com) and edit below "#define"d variables yourself.
// Be sure that Dynamixel properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

using System;
using System.Runtime.InteropServices;
using dynamixel_sdk;

namespace clear_multi_turn
{
  class ClearMultiTurn
  {
    // Control table address
    public const int ADDR_OPERATING_MODE         = 11;                 // Control table address is different in Dynamixel model
    public const int ADDR_TORQUE_ENABLE          = 64;                
    public const int ADDR_GOAL_POSITION          = 116;
    public const int ADDR_PRESENT_POSITION       = 132;

    // Protocol version
    public const int PROTOCOL_VERSION            = 2;                  // See which protocol version is used in the Dynamixel

    // Default setting
    public const int DXL_ID                      = 1;                  // Dynamixel ID: 1
    public const int BAUDRATE                    = 57600;
    public const string DEVICENAME               = "COM1";             // Check which port is being used on your controller
                                                                        // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    public const int TORQUE_ENABLE               = 1;                  // Value for enabling the torque
    public const int TORQUE_DISABLE              = 0;                  // Value for disabling the torque
    public const int MAX_POSITION_VALUE          = 1048575;            // 
    public const int DXL_MOVING_STATUS_THRESHOLD = 20;                 // Dynamixel moving status threshold
    public const int EXT_POSITION_CONTROL_MODE   = 4;                  // Value for extended position control mode (operating mode)

    public const byte ESC_ASCII_VALUE            = 0x1b;
    public const byte SPACE_ASCII_VALUE          = 0x20;

    public const int COMM_SUCCESS = 0;                                 // Communication Success result value
    public const int COMM_TX_FAIL = -1001;                             // Communication Tx Failed

    static void Main(string[] args)
    {
      int port_num = dynamixel.portHandler(DEVICENAME);

      // Initialize PacketHandler Structs
      dynamixel.packetHandler();

      int index = 0;
      int dxl_comm_result = COMM_TX_FAIL;                            // Communication result

      byte dxl_error = 0;                                            // Dynamixel error
      Int32 dxl_present_position = 0;                                // Present position

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

      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_OPERATING_MODE, EXT_POSITION_CONTROL_MODE);
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
        Console.WriteLine("Operating mode changed to extended position control mode.");
      }

      // Enable Dynamixel Torque
      dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE);
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
        Console.WriteLine("Dynamixel has been successfully connected");
      }

      while (true)
      {
        Console.WriteLine("Press any key to continue! (or press ESC to quit!)");
        if (Console.ReadKey(true).KeyChar == ESC_ASCII_VALUE)
            break;

        Console.WriteLine("  Press SPACE key to clear multi-turn information! (or press ESC to stop!)");

        // Write goal position
        dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, MAX_POSITION_VALUE);
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
          // Read present position
          dxl_present_position = (Int32)dynamixel.read4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRESENT_POSITION);
          if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          {
            Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
          }
          else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
          {
            Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
          }

          Console.Write(string.Format("  [ID: {0}] GoalPos: {1}  PresPos: {2}", DXL_ID, MAX_POSITION_VALUE, dxl_present_position, Environment.NewLine));
          Console.Write("\r".PadLeft(Console.WindowWidth - Console.CursorLeft - 1));
          if (Console.KeyAvailable)
          {
            char c = Console.ReadKey().KeyChar;
            if (c == SPACE_ASCII_VALUE)
            {
              Console.WriteLine("\n  Stop & Clear Multi-Turn Information!");

             // Write the present position to the goal position to stop moving
              dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, (UInt32)dxl_present_position);
              if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
              {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
              }
              else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
              {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
              }

              System.Threading.Thread.Sleep(300);

              // Clear Multi-Turn Information
              dynamixel.clearMultiTurn(port_num, PROTOCOL_VERSION, DXL_ID);
              if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
              {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
              }
              else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
              {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
              }

              // Read present position
              dxl_present_position = (Int32)dynamixel.read4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRESENT_POSITION);
              if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
              {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
              }
              else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
              {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
              }

              Console.WriteLine("  Present Position has been reset. : {0} \n", dxl_present_position);

              break;
          }
          else if ( c == ESC_ASCII_VALUE)
          {
            Console.WriteLine("\n  Stopped!! \n");

            // Write the present position to the goal position to stop moving
            dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, (UInt32)dxl_present_position);
            if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result)));
            }
            else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
            {
                Console.WriteLine(Marshal.PtrToStringAnsi(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error)));
            }

              break;
          }
        }
      } while ((Math.Abs(MAX_POSITION_VALUE - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD));
    }

    // Disable Dynamixel Torque
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE);
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