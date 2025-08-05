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
// *********     Indirect Address Example      *********
//
//
// Available Dynamixel model on this example : All models using Protocol 2.0
// This example is designed for using a Dynamixel PRO 54-200, and an USB2DYNAMIXEL.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel PRO properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

import java.util.Scanner;

public class IndirectAddress
{
  public static void main(String[] args)
  {
    // Control table address                                    // Control table address is different in Dynamixel model
    short ADDR_PRO_INDIRECTADDRESS_FOR_WRITE      = 49;         // EEPROM region
    short ADDR_PRO_INDIRECTADDRESS_FOR_READ       = 59;         // EEPROM region
    short ADDR_PRO_TORQUE_ENABLE                  = 562;
    short ADDR_PRO_LED_RED                        = 563;
    short ADDR_PRO_GOAL_POSITION                  = 596;
    short ADDR_PRO_MOVING                         = 610;
    short ADDR_PRO_PRESENT_POSITION               = 611;
    short ADDR_PRO_INDIRECTDATA_FOR_WRITE         = 634;
    short ADDR_PRO_INDIRECTDATA_FOR_READ          = 639;

    // Data Byte Length
    short LEN_PRO_LED_RED                         = 1;
    short LEN_PRO_GOAL_POSITION                   = 4;
    short LEN_PRO_MOVING                          = 1;
    short LEN_PRO_PRESENT_POSITION                = 4;
    short LEN_PRO_INDIRECTDATA_FOR_WRITE          = 5;
    short LEN_PRO_INDIRECTDATA_FOR_READ           = 5;

    // Protocol version
    int PROTOCOL_VERSION                = 2;                   // See which protocol version is used in the Dynamixel

    // Default setting
    byte DXL_ID                         = 1;                   // Dynamixel ID: 1
    int BAUDRATE                        = 57600;
    String DEVICENAME                   = "/dev/ttyUSB0";      // Check which port is being used on your controller
                                                               // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    byte TORQUE_ENABLE                  = 1;                   // Value for enabling the torque
    byte TORQUE_DISABLE                 = 0;                   // Value for disabling the torque
    int DXL_MINIMUM_POSITION_VALUE      = -150000;             // Dynamixel will rotate between this value
    int DXL_MAXIMUM_POSITION_VALUE      = 150000;              // and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
    short DXL_MINIMUM_LED_VALUE         = 0;                   // Dynamixel LED will light between this value
    short DXL_MAXIMUM_LED_VALUE         = 255;                 // and this value
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
    int port_num = dynamixel.portHandler(DEVICENAME);

    // Initialize PacketHandler Structs
    dynamixel.packetHandler();

    // Initialize Groupsyncwrite instance
    int groupwrite_num = dynamixel.groupSyncWrite(port_num, PROTOCOL_VERSION, ADDR_PRO_INDIRECTDATA_FOR_WRITE, LEN_PRO_INDIRECTDATA_FOR_WRITE);

    // Initialize Groupsyncread Structs for Present Position
    int groupread_num = dynamixel.groupSyncRead(port_num, PROTOCOL_VERSION, ADDR_PRO_INDIRECTDATA_FOR_READ, LEN_PRO_INDIRECTDATA_FOR_READ);

    int index = 0;
    int dxl_comm_result = COMM_TX_FAIL;                         // Communication result
    Boolean dxl_addparam_result = false;                        // AddParam result
    Boolean dxl_getdata_result = false;                         // GetParam result
    int[] dxl_goal_position = new int[]{DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE};        // Goal position

    byte dxl_error = 0;                                         // Dynamixel error
    byte dxl_moving = 0;                                        // Dynamixel moving status
    byte[] dxl_led_value = new byte[]{ (byte)DXL_MINIMUM_LED_VALUE, (byte)DXL_MAXIMUM_LED_VALUE };      // Dynamixel LED value
    int dxl_present_position = 0;                               // Present position

    // Open port
    if (dynamixel.openPort(port_num))
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

    // Set port baudrate
    if (dynamixel.setBaudRate(port_num, BAUDRATE))
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

    // Disable Dynamixel Torque :
    // Indirect address would not accessible when the torque is already enabled
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_DISABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }
    else
    {
      System.out.println("Dynamixel has been successfully connected");
    }

    // INDIRECTDATA parameter storages replace LED, goal position, present position and moving status storages
    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_WRITE + 0), (short)(ADDR_PRO_GOAL_POSITION + 0));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_WRITE + 2), (short)(ADDR_PRO_GOAL_POSITION + 1));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_WRITE + 4), (short)(ADDR_PRO_GOAL_POSITION + 2));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_WRITE + 6), (short)(ADDR_PRO_GOAL_POSITION + 3));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_WRITE + 8), ADDR_PRO_LED_RED);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_READ + 0), (short)(ADDR_PRO_PRESENT_POSITION + 0));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_READ + 2), (short)(ADDR_PRO_PRESENT_POSITION + 1));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_READ + 4), (short)(ADDR_PRO_PRESENT_POSITION + 2));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_READ + 6), (short)(ADDR_PRO_PRESENT_POSITION + 3));
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    dynamixel.write2ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, (short)(ADDR_PRO_INDIRECTADDRESS_FOR_READ + 8), ADDR_PRO_MOVING);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    // Enable Dynamixel Torque
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_ENABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    // Add parameter storage for Dynamixel present position value
    dxl_addparam_result = dynamixel.groupSyncReadAddParam(groupread_num, DXL_ID);
    if (dxl_addparam_result != true)
    {
      System.out.printf("[ID: %d] groupSyncRead addparam failed\n", DXL_ID);
      return;
    }

    while (true)
    {
      System.out.println("Press enter to continue! (or press e then enter to quit!)");
      if(scanner.nextLine().equals(KEY_FOR_ESCAPE))
        break;

      // Add values to the Syncwrite storage
      dxl_addparam_result = dynamixel.groupSyncWriteAddParam(groupwrite_num, DXL_ID, dxl_goal_position[index], LEN_PRO_GOAL_POSITION);
      if (dxl_addparam_result != true)
      {
        System.out.printf("[ID: %d] groupSyncWrite addparam failed\n", DXL_ID);
        return;
      }
      dxl_addparam_result = dynamixel.groupSyncWriteAddParam(groupwrite_num, DXL_ID, dxl_led_value[index], LEN_PRO_LED_RED);
      if (dxl_addparam_result != true)
      {
        System.out.printf("[ID: %d] groupSyncWrite addparam failed\n", DXL_ID);
        return;
      }

      // Syncwrite goal position
      dynamixel.groupSyncWriteTxPacket(groupwrite_num);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
        System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));

      // Clear syncwrite parameter storage
      dynamixel.groupSyncWriteClearParam(groupwrite_num);

      do
      {
        // Syncread present position from indirectdata2
        dynamixel.groupSyncReadTxRxPacket(groupread_num);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));

        // Check if groupsyncread data of Dyanamixel is available
        dxl_getdata_result = dynamixel.groupSyncReadIsAvailable(groupread_num, DXL_ID, ADDR_PRO_INDIRECTDATA_FOR_READ, LEN_PRO_PRESENT_POSITION);
        if (dxl_getdata_result != true)
        {
          System.out.printf("[ID: %d] groupSyncRead getdata failed\n", DXL_ID);
          return;
        }

        // Check if groupsyncread data of Dyanamixel is available
        dxl_getdata_result = dynamixel.groupSyncReadIsAvailable(groupread_num, DXL_ID, (short)(ADDR_PRO_INDIRECTDATA_FOR_READ + LEN_PRO_PRESENT_POSITION), LEN_PRO_MOVING);
        if (dxl_getdata_result != true)
        {
          System.out.printf("[ID: %d] groupSyncRead getdata failed\n", DXL_ID);
          return;
        }

        // Get Dynamixel present position value
        dxl_present_position = dynamixel.groupSyncReadGetData(groupread_num, DXL_ID, ADDR_PRO_INDIRECTDATA_FOR_READ, LEN_PRO_PRESENT_POSITION);

        // Get Dynamixel moving status value
        dxl_moving = (byte)dynamixel.groupSyncReadGetData(groupread_num, DXL_ID, (short)(ADDR_PRO_INDIRECTDATA_FOR_READ + LEN_PRO_PRESENT_POSITION), LEN_PRO_MOVING);

        System.out.printf("[ID: %d] GoalPos: %d  PresPos: %d  IsMoving: %d\n", DXL_ID, dxl_goal_position[index], dxl_present_position, dxl_moving);

      } while (Math.abs(dxl_goal_position[index] - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD);

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

    // Disable Dynamixel Torque
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRO_TORQUE_ENABLE, TORQUE_DISABLE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    // Close port
    dynamixel.closePort(port_num);

    return;
  }
}
