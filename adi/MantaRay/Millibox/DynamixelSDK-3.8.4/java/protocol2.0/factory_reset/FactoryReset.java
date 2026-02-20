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
// Available Dynamixel model on this example : All models using Protocol 2.0
// This example is designed for using a Dynamixel PRO 54-200, and an USB2DYNAMIXEL.
// To use another Dynamixel model, such as X series, see their details in E-Manual(emanual.robotis.com) and edit below variables yourself.
// Be sure that Dynamixel PRO properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

// Be aware that:
// This example resets all properties of Dynamixel to default values, such as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
//

import java.util.Scanner;

public class FactoryReset
{
  public static void main(String[] args)
  {
    // Control table address
    short ADDR_PRO_BAUDRATE             = 8;                   // Control table address is different in Dynamixel model

    // Protocol version
    int PROTOCOL_VERSION                = 2;                   // See which protocol version is used in the Dynamixel

    // Default setting
    byte DXL_ID                         = 1;                   // Dynamixel ID: 1-
    int BAUDRATE                        = 57600;
    String DEVICENAME                   = "/dev/ttyUSB0";      // Check which port is being used on your controller
                                                               // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    int FACTORYRST_DEFAULTBAUDRATE      = 57600;               // Dynamixel baudrate set by factoryreset
    byte NEW_BAUDNUM                    = 3;                   // New baudnum to recover Dynamixel baudrate as it was
    byte OPERATION_MODE                 = 0x01;                // 0xFF : reset all values
                                                               // 0x01 : reset all values except ID
                                                               // 0x02 : reset all values except ID and baudrate

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

    int dxl_comm_result = COMM_TX_FAIL;                      // Communication result

    byte dxl_error = 0;                                      // Dynamixel error
    byte dxl_baudnum_read;                                   // Read baudnum

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

    // Read present baudrate of the controller
    System.out.printf("Now the controller baudrate is : %d\n", dynamixel.getBaudRate(port_num));

    // Try factoryreset
    System.out.printf("[ID: %d] Try factoryreset : \n", DXL_ID);
    dynamixel.factoryReset(port_num, PROTOCOL_VERSION, DXL_ID, OPERATION_MODE);
    if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      System.out.println("Aborted");
      System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
      return;
    }
    else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    // Wait for reset
    System.out.printf("Wait for reset...\n");
    try
    {
      Thread.sleep(2000);
    }
    catch (InterruptedException e)
    {
      System.out.println(e.getMessage());
    }

    System.out.printf("[ID: %d] factoryReset Success!\n", DXL_ID);

    // Set controller baudrate to dxl default baudrate
    if (dynamixel.setBaudRate(port_num, FACTORYRST_DEFAULTBAUDRATE))
    {
      System.out.printf("Succeed to change the controller baudrate to : %d\n", FACTORYRST_DEFAULTBAUDRATE);
    }
    else
    {
      System.out.println("Failed to change the controller baudrate");
      System.out.println("Press any key to terminate...");
      scanner.nextLine();
      return;
    }

    // Read Dynamixel baudnum
    dxl_baudnum_read = dynamixel.read1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRO_BAUDRATE);
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
      System.out.printf("[ID: %d] Dynamixel baudnum is now : %d\n", DXL_ID, dxl_baudnum_read);
    }

    // Write new baudnum
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRO_BAUDRATE, NEW_BAUDNUM);
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
      System.out.printf("[ID: %d] Set Dynamixel baudnum to : %d\n", DXL_ID, NEW_BAUDNUM);
    }

    // Set port baudrate to BAUDRATE
    if (dynamixel.setBaudRate(port_num, BAUDRATE))
    {
      System.out.printf("Succeed to change the controller baudrate to : %d\n", BAUDRATE);
    }
    else
    {
      System.out.println("Failed to change the controller baudrate");
      System.out.println("Press any key to terminate...");
      scanner.nextLine();
      return;
    }

    try
    {
      Thread.sleep(200);
    }
    catch (InterruptedException e)
    {
      System.out.println(e.getMessage());
    }

    // Read Dynamixel baudnum
    dxl_baudnum_read = dynamixel.read1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRO_BAUDRATE);
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
      System.out.printf("[ID: %d] Dynamixel Baudnum is now : %d", DXL_ID, dxl_baudnum_read);
    }

    return;
  }
}
