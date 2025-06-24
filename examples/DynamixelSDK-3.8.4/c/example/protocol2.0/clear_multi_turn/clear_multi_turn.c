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

//
// *********     Clear Multi-Turn Example      *********
//
//
// Available Dynamixel model on this example : MX with Protocol 2.0 (firmware v42 or above), Dynamixel X-series (firmware v42 or above)
// This example is designed for using a Dynamixel XM430-W350-R, and an U2D2.
// To use another Dynamixel model, such as MX series, see their details in E-Manual(emanual.robotis.com) and edit below "#define"d variables yourself.
// Be sure that Dynamixel properties are already set as %% ID : 1 / Baudnum : 1 (Baudrate : 57600)
//

#if defined(__linux__) || defined(__APPLE__)
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#define STDIN_FILENO 0
#elif defined(_WIN32) || defined(_WIN64)
#include <conio.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include "dynamixel_sdk.h"                                  // Uses Dynamixel SDK library

// Control table address
#define ADDR_OPERATING_MODE             11                  // Control table address is different in Dynamixel model
#define ADDR_TORQUE_ENABLE              64
#define ADDR_GOAL_POSITION              116
#define ADDR_PRESENT_POSITION           132

// Protocol version
#define PROTOCOL_VERSION                2.0                 // See which protocol version is used in the Dynamixel

// Default setting
#define DXL_ID                          1                   // Dynamixel ID: 1
#define BAUDRATE                        57600
#define DEVICENAME                      "/dev/ttyUSB0"      // Check which port is being used on your controller
                                                            // ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

#define TORQUE_ENABLE                   1                   // Value for enabling the torque
#define TORQUE_DISABLE                  0                   // Value for disabling the torque
#define MAX_POSITION_VALUE              1048575
#define DXL_MOVING_STATUS_THRESHOLD     20                  // Dynamixel moving status threshold
#define EXT_POSITION_CONTROL_MODE       4                   // Value for extended position control mode (operating mode)

#define ESC_ASCII_VALUE                 0x1b
#define SPACE_ASCII_VALUE               0x20

int getch()
{
#if defined(__linux__) || defined(__APPLE__)
  struct termios oldt, newt;
  int ch;
  tcgetattr(STDIN_FILENO, &oldt);
  newt = oldt;
  newt.c_lflag &= ~(ICANON | ECHO);
  tcsetattr(STDIN_FILENO, TCSANOW, &newt);
  ch = getchar();
  tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
  return ch;
#elif defined(_WIN32) || defined(_WIN64)
  return _getch();
#endif
}

int kbhit(void)
{
#if defined(__linux__) || defined(__APPLE__)
  struct termios oldt, newt;
  int ch;
  int oldf;

  tcgetattr(STDIN_FILENO, &oldt);
  newt = oldt;
  newt.c_lflag &= ~(ICANON | ECHO);
  tcsetattr(STDIN_FILENO, TCSANOW, &newt);
  oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);

  ch = getchar();

  tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
  fcntl(STDIN_FILENO, F_SETFL, oldf);

  if (ch != EOF)
  {
    ungetc(ch, stdin);
    return 1;
  }

  return 0;
#elif defined(_WIN32) || defined(_WIN64)
  return _kbhit();
#endif
}

void msecSleep(int waitTime)
{
#if defined(__linux__) || defined(__APPLE__)
    usleep(waitTime * 1000);
#elif defined(_WIN32) || defined(_WIN64)
    _sleep(waitTime);
#endif
}

int main()
{
  // Initialize PortHandler Structs
  // Set the port path
  // Get methods and members of PortHandlerLinux or PortHandlerWindows
  int port_num = portHandler(DEVICENAME);

  // Initialize PacketHandler Structs
  packetHandler();

  int dxl_comm_result = COMM_TX_FAIL;             // Communication result

  uint8_t dxl_error = 0;                          // Dynamixel error
  int32_t dxl_present_position = 0;               // Present position

  // Open port
  if (openPort(port_num))
  {
    printf("Succeeded to open the port!\n");
  }
  else
  {
    printf("Failed to open the port!\n");
    printf("Press any key to terminate...\n");
    getch();
    return 0;
  }

  // Set port baudrate
  if (setBaudRate(port_num, BAUDRATE))
  {
    printf("Succeeded to change the baudrate!\n");
  }
  else
  {
    printf("Failed to change the baudrate!\n");
    printf("Press any key to terminate...\n");
    getch();
    return 0;
  }

  // Set operating mode to extended position control mode
  write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_OPERATING_MODE, EXT_POSITION_CONTROL_MODE);
  if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
  {
    printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
  }
  else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
  {
    printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
  }
  else
  {
    printf("Operating mode changed to extended position control mode. \n");
  }

  // Enable Dynamixel Torque
  write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE);
  if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
  {
    printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
  }
  else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
  {
    printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
  }
  else
  {
    printf("Dynamixel has been successfully connected \n");
  }

  while (1)
  {
    printf("\nPress any key to continue! (or press ESC to quit!)\n");
    if (getch() == ESC_ASCII_VALUE)
      break;

    printf("  Press SPACE key to clear multi-turn information! (or press ESC to stop!)\n");

    // Write goal position
    write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, MAX_POSITION_VALUE);
    if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
    {
      printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
    }
    else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
    {
      printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
    }

    do
    {
      // Read present position
      dxl_present_position = read4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRESENT_POSITION);
      if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
      {
        printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
      }
      else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
      {
        printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
      }

      printf("  [ID:%03d] GoalPos:%03d  PresPos:%03d\r", DXL_ID, MAX_POSITION_VALUE, dxl_present_position);

      if (kbhit())
      {
        char c = getch();
        if (c == SPACE_ASCII_VALUE)
        {
          printf("\n  Stop & Clear Multi-Turn Information! \n");

          // Write the present position to the goal position to stop moving
          write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, dxl_present_position);
          if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          {
            printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
          }
          else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
          {
            printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
          }

          msecSleep(300);

          // Clear Multi-Turn Information
          clearMultiTurn(port_num, PROTOCOL_VERSION, DXL_ID);
          if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          {
            printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
          }
          else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
          {
            printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
          }

          // Read present position
          dxl_present_position = read4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_PRESENT_POSITION);
          if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          {
            printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
          }
          else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
          {
            printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
          }

          printf("  Present Position has been reset. : %03d \n", dxl_present_position);

          break;
        }
        else if (c == ESC_ASCII_VALUE)
        {
          printf("\n  Stopped!! \n");

          // Write the present position to the goal position to stop moving
          write4ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_GOAL_POSITION, dxl_present_position);
          if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
          {
            printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
          }
          else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
          {
            printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
          }

          break;
        }
      }

    } while ((abs(MAX_POSITION_VALUE - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD));

    printf("\n");
  }

  // Disable Dynamixel Torque
  write1ByteTxRx(port_num, PROTOCOL_VERSION, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE);
  if ((dxl_comm_result = getLastTxRxResult(port_num, PROTOCOL_VERSION)) != COMM_SUCCESS)
  {
    printf("%s\n", getTxRxResult(PROTOCOL_VERSION, dxl_comm_result));
  }
  else if ((dxl_error = getLastRxPacketError(port_num, PROTOCOL_VERSION)) != 0)
  {
    printf("%s\n", getRxPacketError(PROTOCOL_VERSION, dxl_error));
  }

  // Close port
  closePort(port_num);

  return 0;
}
