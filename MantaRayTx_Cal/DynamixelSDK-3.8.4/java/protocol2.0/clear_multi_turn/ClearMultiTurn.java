/*******************************************************************************
* Copyright 2018 ROBOTIS CO., LTD.
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
// Available Dynamixel model on this example : MX with Protocol 2.0 (firmware v42 or above), Dynamixel X-series (firmware v42 or above)
// This example is designed for using a Dynamixel XM430-W350-R, and an U2D2.
// To use another Dynamixel model, such as MX series, see their details in E-Manual(emanual.robotis.com) and edit below "#define"d variables yourself.
// Be sure that Dynamixel properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

import java.io.IOException;
import java.util.Scanner;

public class ClearMultiTurn
{	
  public static void main(String[] args) throws InterruptedException, IOException
  {  
    // Control table address
    short ADDR_OPERATING_MODE           = 11;				   // Control table address is different in Dynamixel model
    short ADDR_TORQUE_ENABLE            = 64;                
    short ADDR_GOAL_POSITION            = 116;
    short ADDR_PRESENT_POSITION         = 132;

    // Protocol version
    int PROTOCOL_VERSION                = 2;                   // See which protocol version is used in the Dynamixel

    // Default setting
    byte DXL_ID                         = 1;                   // Dynamixel ID: 1
    int BAUDRATE                        = 57600;
    String DEVICENAME                   = "COM1";              // Check which port is being used on your controller
                                                               // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

    byte TORQUE_ENABLE                  = 1;                   // Value for enabling the torque
    byte TORQUE_DISABLE                 = 0;                   // Value for disabling the torque
    int MAX_POSITION_VALUE              = 1048575;             
    int DXL_MOVING_STATUS_THRESHOLD     = 20;                  // Dynamixel moving status threshold
    byte EXT_POSITION_CONTROL_MODE      = 4;                   //  Value for extended position control mode (operating mode)
    

    String KEY_FOR_ESCAPE               = "e";                 // Key for escape
    String KEY_FOR_CONTINUE             = " ";				   // key for continue
    
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

    int dxl_comm_result = COMM_TX_FAIL;                        // Communication result
    
    byte dxl_error = 0;                                        // Dynamixel error
    int dxl_present_position = 0;                              // Present position

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
    
    // Set operating mode to extended position control mode
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_OPERATING_MODE, EXT_POSITION_CONTROL_MODE);
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
      System.out.println("Operating mode changed to extended position control mode. \n");
    }   
    
    // Enable Dynamixel Torque
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE);
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

    while (true)
    {
      System.out.println("\nPress enter to continue! (or press e then enter to quit!)");
          
      String ch = scanner.nextLine();
      if (ch.equals("e"))
        break;
      
	  System.out.println("\nPress SPACE key to clear multi-turn information! (or press ESC to stop!)\n");

	  // Write goal position
      dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, MAX_POSITION_VALUE);
      if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
      }
      else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
      }

      do
      {
        // Read present position
        dxl_present_position = dynamixel.read4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRESENT_POSITION);
        if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
        {
          System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
        }
        else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
        {
          System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
        }
        
        System.out.printf("  [ID: %d] GoalPos:%d  PresPos:%d\n", DXL_ID, MAX_POSITION_VALUE, dxl_present_position);

        if (System.in.available() > 0)
        {
    	 
          String c = scanner.nextLine(); 	
          if(c.equals(KEY_FOR_CONTINUE))
          {
            System.out.printf("  Stop & Clear Multi-Turn Information! \n");   
            
            // Write the present position to the goal position to stop moving 
            dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, dxl_present_position);
            if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            {
              System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
            }
            else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
            {
              System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
            }
            
            Thread.sleep(300);
            
            // Clear Multi-Turn Information
            dynamixel.clearMultiTurn(port_num, PROTOCOL_VERSION, DXL_ID);
            if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            {
              System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
            }
            else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
            {
              System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
            }
            
            // Read present position
            dxl_present_position = dynamixel.read4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRESENT_POSITION);
            if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            {
              System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
            }
            else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
            {
              System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
            }
            
            System.out.printf("  Present Position has been reset. : %03d \n", dxl_present_position); 
            
            break;
          }
          
          else if (c.equals(KEY_FOR_ESCAPE))
          {
        	System.out.printf("\n  Stopped!! ");
        	  
        	// Write the present position to the goal position to stop moving
        	dynamixel.write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, dxl_present_position);
            if ((dxl_comm_result = dynamixel.getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
            {
              System.out.println(dynamixel.getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
            }
            else if ((dxl_error = dynamixel.getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
            {
              System.out.println(dynamixel.getRxPacketError(PROTOCOL_VERSION, dxl_error));
            }
              
            break;
          }
        }
        
      } while ((Math.abs(MAX_POSITION_VALUE - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD));
    }

    // Disable Dynamixel Torque
    dynamixel.write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE);
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