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
// *********     MultiPort Example      *********
//
//
// Available Dynamixel model on this example : All models using Protocol 2.0
// This example is designed for using two Dynamixel PRO 54-200, and two USB2DYNAMIXELs.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel PRO properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

import java.util.Scanner;

public class MultiPort
{
  public static void main(String[] args)
  {
    // Control table address
    short ADDR_PRO_TORQUE_ENABLE        = 562;                 // Control table address is different in Dynamixel model
    short ADDR_PRO_GOAL_POSITION        = 596;
    short ADDR_PRO_PRESENT_POSITION     = 611;

    // Protocol version
    int PROTOCOL_VERSION                = 2;                   // See which protocol version is used in the Dynamixel

    // Default setting
    byte DXL1_ID                        = 1;                   // Dynamixel ID: 1
    byte DXL2_ID                        = 2;                   // Dynamixel ID: 2
    int BAUDRATE                        = 57600;
    String DEVICENAME1                   = "/dev/ttyUSB0";     // Check which port is being used on your controller
    String DEVICENAME2                   = "/dev/ttyUSB1";     // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    byte TORQUE_ENABLE                  = 1;                   // Value for enabling the torque
    byte TORQUE_DISABLE                 = 0;                   // Value for disabling the torque
    int DXL_MINIMUM_POSITION_VALUE      = -150000;             // Dynamixel will rotate between this value
    int DXL_MAXIMUM_POSITION_VALUE      = 150000;              // and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
    int DXL_MOVING_STATUS_THRESHOLD     = 20;                  // Dynamixel moving status threshold

    String KEY_FOR_ESCAPE               = "e";                 // Key for escape

    int COMM_SUCCESS                    = 0;                   // Communication Success result value
    int COMM_TX_FAIL                    = -1001;               // Communication Tx Failed

    // Instead of getch
    Scanner scanner = new Scanner(System.in);

    // Initialize Dynamixel class for java
    Dynamixel dynamixel = new Dynamixel();

    // Initialize PortHandler Structs
    // Set the port path
    // Get methods and members of PortHandlerLinux or PortHandlerWindows
    int port_num1 = dynamixel.portHandler(DEVICENAME1);
    int port_num2 = dynamixel.portHandler(DEVICENAME2);

    // Initialize PacketHandler Structs
    dynamixel.packetHandler();

    int index = 0;
    int dxl_comm_result = COMM_TX_FAIL;                        // Communication result
    int[] dxl_goal_position = new int[]{DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE};         // Goal position

    byte dxl_error = 0;                                        // Dynamixel error
    int dxl1_present_position = 0, dxl2_present_position = 0;  // Present position

    // Open port1
    if (dynamixel.openPort(port_num1))
    {
      System.out.println("Succeeded to open the port!");
    }
    else
    {
      System.out.println("Failed to open the port!");
      System.out.println("Press any key to terminate...");
      scanner.nextLine();
      return;
    }

    // Open port2
    if (dynamixel.openPort(port_num2))
    {
      System.out.println("Succeeded to open the port!");
    }
    else
    {
      System.out.println("Failed to open the port!");
      System.out.println("Press any key to terminate...");
      scanner.nextLine();
      return;
    }


    // Set port1 baudrate
    if (dynamixel.setBaudRate(port_num1, BAUDRATE))
    {
      System.out.println("Succeeded to change the baudrate!");
    }
    else
    {
      System.out.println("Failed to change the baudrate!");
      System.out.println("Press any key to terminate...");
      scanner.nextLine();
      return;
    }

    // Set port2 baudrate
    if (dynamixel.setBaudRate(port_num1, BAUDRATE))
    {
      System.out.println("Succeeded to change the baudrate!");
    }
    else
    {
      System.out.println("Failed to change the baudrate!");
      System.out.println("Press any key to terminate...");
      scanner.nextLine();
      return;
    }

    // Enable Dynamixel#1 Torque
    dynamixel.write1ByteTxRx(port_num1, PROTOCOL_VERSION, DXL1_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_ENABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num1, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num1, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }
    else
    {
      System.out.printf("Dynamixel#%d has been successfully connected\n", DXL1_ID);
    }

    // Enable Dynamixel#2 Torque
    dynamixel.write1ByteTxRx(port_num2, PROTOCOL_VERSION, DXL2_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_ENABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num2, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num2, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }
    else
    {
      System.out.printf("Dynamixel#%d has been successfully connected\n", DXL2_ID);
    }

    while (true)
    {
      System.out.println("Press enter to continue! (or press e then enter to quit!)");
      if(scanner.nextLine().equals(KEY_FOR_ESCAPE))
        break;

      // Write Dynamixel#1 goal position
      dynamixel.write4ByteTxRx(port_num1, PROTOCOL_VERSION, DXL1_ID, ADDR_PRO_GOAL_POSITION, dxl_goal_position[index]);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num1, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num1, PROTOCOL_VERSION)) != 0)
      {
        System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
      }

      // Write Dynamixel#2 goal position
      dynamixel.write4ByteTxRx(port_num2, PROTOCOL_VERSION, DXL2_ID, ADDR_PRO_GOAL_POSITION, dxl_goal_position[index]);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num2, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num2, PROTOCOL_VERSION)) != 0)
      {
        System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
      }

      do
      {
        // Read Dynamixel#1 present position
        dxl1_present_position = dynamixel.read4ByteTxRx(port_num1, PROTOCOL_VERSION, DXL1_ID, ADDR_PRO_PRESENT_POSITION);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num1, PROTOCOL_VERSION)) != COMM_SUCCESS)
        {
          System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
        }
        else if ((dxl_error = dynamixel.getLastRxPacketError(port_num1, PROTOCOL_VERSION)) != 0)
        {
          System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
        }

        // Read Dynamixel#2 present position
        dxl2_present_position = dynamixel.read4ByteTxRx(port_num2, PROTOCOL_VERSION, DXL2_ID, ADDR_PRO_PRESENT_POSITION);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num2, PROTOCOL_VERSION)) != COMM_SUCCESS)
        {
          System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
        }
        else if ((dxl_error = dynamixel.getLastRxPacketError(port_num2, PROTOCOL_VERSION)) != 0)
        {
          System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
        }

        System.out.printf("[ID: %d] GoalPos: %d  PresPos: %d [ID: %d] GoalPos: %d  PresPos: %d\n", DXL1_ID, dxl_goal_position[index], dxl1_present_position, DXL2_ID, dxl_goal_position[index], dxl2_present_position);

      } while ((Math.abs(dxl_goal_position[index] - dxl1_present_position) > DXL_MOVING_STATUS_THRESHOLD) || (Math.abs(dxl_goal_position[index] - dxl2_present_position) > DXL_MOVING_STATUS_THRESHOLD));

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
    dynamixel.write1ByteTxRx(port_num1, PROTOCOL_VERSION, DXL1_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_DISABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num1, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num1, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    // Disable Dynamixel#2 Torque
    dynamixel.write1ByteTxRx(port_num2, PROTOCOL_VERSION, DXL2_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_DISABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num2, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num2, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    // Close port1
    dynamixel.closePort(port_num1);

    // Close port2
    dynamixel.closePort(port_num2);

    return;
  }
}
