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

import com.sun.jna.Library;
import com.sun.jna.Native;

interface LibFunction extends Library
{
  // PortHandler functions
  public int portHandler(String str);

  public Boolean openPort                (int port_num);
  public void    closePort               (int port_num);
  public void    clearPort               (int port_num);

  public void    setPortName             (int port_num, String port_name);
  public String  getPortName             (int port_num);

  public Boolean setBaudRate             (int port_num, int baudrate);
  public int     getBaudRate             (int port_num);

  public int     readPort                (int port_num, byte[] packet, int length);
  public int     writePort               (int port_num, byte[] packet, int length);

  public void    setPacketTimeout        (int port_num, short packet_length);
  public void    setPacketTimeoutMSec    (int port_num, double msec);
  public Boolean isPacketTimeout         (int port_num);

  // PacketHandler functions
  public void    packetHandler           ();

  public String  getTxRxResult           (int protocol_version, int result);
  public String  getRxPacketError        (int protocol_version, byte error);

  public int     getLastTxRxResult       (int port_num, int protocol_version);
  public byte    getLastRxPacketError    (int port_num, int protocol_version);

  public void    setDataWrite            (int port_num, int protocol_version, short data_length, short data_pos, int data);
  public int     getDataRead             (int port_num, int protocol_version, short data_length, short data_pos);

  public void    txPacket                (int port_num, int protocol_version);

  public void    rxPacket                (int port_num, int protocol_version);

  public void    txRxPacket              (int port_num, int protocol_version);

  public void    ping                    (int port_num, int protocol_version, byte id);

  public int     pingGetModelNum         (int port_num, int protocol_version, byte id);

  // broadcastPing
  public void    broadcastPing           (int port_num, int protocol_version);
  public Boolean getBroadcastPingResult  (int port_num, int protocol_version, int id);

  public void    reboot                  (int port_num, int protocol_version, byte id);

  public void    clearMultiTurn          (int port_num, int protocol_version, byte id);
  
  public void    factoryReset            (int port_num, int protocol_version, byte id, byte option);

  public void    readTx                  (int port_num, int protocol_version, byte id, short address, short length);
  public void    readRx                  (int port_num, int protocol_version, short length);
  public void    readTxRx                (int port_num, int protocol_version, byte id, short address, short length);

  public void    read1ByteTx             (int port_num, int protocol_version, byte id, short address);
  public byte    read1ByteRx             (int port_num, int protocol_version);
  public byte    read1ByteTxRx           (int port_num, int protocol_version, byte id, short address);

  public void    read2ByteTx             (int port_num, int protocol_version, byte id, short address);
  public short   read2ByteRx             (int port_num, int protocol_version);
  public short   read2ByteTxRx           (int port_num, int protocol_version, byte id, short address);

  public void    read4ByteTx             (int port_num, int protocol_version, byte id, short address);
  public int     read4ByteRx             (int port_num, int protocol_version);
  public int     read4ByteTxRx           (int port_num, int protocol_version, byte id, short address);

  public void    writeTxOnly             (int port_num, int protocol_version, byte id, short address, short length);
  public void    writeTxRx               (int port_num, int protocol_version, byte id, short address, short length);

  public void    write1ByteTxOnly        (int port_num, int protocol_version, byte id, short address, byte data);
  public void    write1ByteTxRx          (int port_num, int protocol_version, byte id, short address, byte data);

  public void    write2ByteTxOnly        (int port_num, int protocol_version, byte id, short address, short data);
  public void    write2ByteTxRx          (int port_num, int protocol_version, byte id, short address, short data);

  public void    write4ByteTxOnly        (int port_num, int protocol_version, byte id, short address, int data);
  public void    write4ByteTxRx          (int port_num, int protocol_version, byte id, short address, int data);

  public void    regWriteTxOnly          (int port_num, int protocol_version, byte id, short address, short length);
  public void    regWriteTxRx            (int port_num, int protocol_version, byte id, short address, short length);

  public void    syncReadTx              (int port_num, int protocol_version, short start_address, short data_length, short param_length);
  // syncReadRx   -> GroupSyncRead
  // syncReadTxRx -> GroupSyncRead

  public void    syncWriteTxOnly         (int port_num, int protocol_version, short start_address, short data_length, short param_length);

  public void    bulkReadTx              (int port_num, int protocol_version, short param_length);
  // bulkReadRx   -> GroupBulkRead
  // bulkReadTxRx -> GroupBulkRead

  public void    bulkWriteTxOnly         (int port_num, int protocol_version, short param_length);

  // GroupBulkRead
  public int     groupBulkRead               (int port_num, int protocol_version);

  public Boolean groupBulkReadAddParam       (int group_num, byte id, short start_address, short data_length);
  public void    groupBulkReadRemoveParam    (int group_num, byte id);
  public void    groupBulkReadClearParam     (int group_num);

  public void    groupBulkReadTxPacket       (int group_num);
  public void    groupBulkReadRxPacket       (int group_num);
  public void    groupBulkReadTxRxPacket     (int group_num);

  public Boolean groupBulkReadIsAvailable    (int group_num, byte id, short address, short data_length);
  public int     groupBulkReadGetData        (int group_num, byte id, short address, short data_length);

  // GroupBulkWrite
  public int     groupBulkWrite              (int port_num, int protocol_version);

  public Boolean groupBulkWriteAddParam      (int group_num, byte id, short start_address, short data_length, int data, short input_length);
  public void    groupBulkWriteRemoveParam   (int group_num, byte id);
  public Boolean groupBulkWriteChangeParam   (int group_num, byte id, short start_address, short data_length, int data, short input_length, short data_pos);
  public void    groupBulkWriteClearParam    (int group_num);

  public void    groupBulkWriteTxPacket      (int group_num);

  // GroupSyncRead
  public int     groupSyncRead               (int port_num, int protocol_version, short start_address, short data_length);

  public Boolean groupSyncReadAddParam       (int group_num, byte id);
  public void    groupSyncReadRemoveParam    (int group_num, byte id);
  public void    groupSyncReadClearParam     (int group_num);

  public void    groupSyncReadTxPacket       (int group_num);
  public void    groupSyncReadRxPacket       (int group_num);
  public void    groupSyncReadTxRxPacket     (int group_num);

  public Boolean groupSyncReadIsAvailable    (int group_num, byte id, short address, short data_length);
  public int     groupSyncReadGetData        (int group_num, byte id, short address, short data_length);

  // groupSyncWrite
  public int     groupSyncWrite              (int port_num, int protocol_version, short start_address, short data_length);

  public Boolean groupSyncWriteAddParam      (int group_num, byte id, int data, short data_length);
  public void    groupSyncWriteRemoveParam   (int group_num, byte id);
  public Boolean groupSyncWriteChangeParam   (int group_num, byte id, int data, short data_length, short data_pos);
  public void    groupSyncWriteClearParam    (int group_num);

  public void    groupSyncWriteTxPacket      (int group_num);
}

public class Dynamixel
{
  LibFunction libFunction = (LibFunction)Native.loadLibrary("dxl_x86_c", LibFunction.class);

  // PortHandler functions
  public int portHandler(String str)
  {
    return libFunction.portHandler(str);
  }

  public Boolean openPort(int port_num)
  {
    return libFunction.openPort(port_num);
  }
  public void closePort(int port_num)
  {
    libFunction.closePort(port_num);
  }
  public void clearPort(int port_num)
  {
    libFunction.clearPort(port_num);
  }

  public Boolean setBaudRate(int port_num, int baudrate)
  {
    return libFunction.setBaudRate(port_num, baudrate);
  }
  public int getBaudRate(int port_num)
  {
    return libFunction.getBaudRate(port_num);
  }

  public int readPort(int port_num, byte[] packet, int length)
  {
    return libFunction.readPort(port_num, packet, length);
  }
  public int writePort(int port_num, byte[] packet, int length)
  {
    return libFunction.writePort(port_num, packet, length);
  }

  public void setPacketTimeout(int port_num, short packet_length)
  {
    libFunction.setPacketTimeout(port_num, packet_length);
  }
  public void setPacketTimeoutMSec(int port_num, double msec)
  {
    libFunction.setPacketTimeoutMSec(port_num, msec);
  }
  public Boolean isPacketTimeout(int port_num)
  {
    return libFunction.isPacketTimeout(port_num);
  }

  // PacketHandler functions
  public void packetHandler()
  {
    libFunction.packetHandler();
  }

  public String getTxRxResult(int protocol_version, int result)
  {
    return libFunction.getTxRxResult(protocol_version, result);
  }

  public String getRxPacketError(int protocol_version, byte error)
  {
    return libFunction.getRxPacketError(protocol_version, error);
  }

  public int getLastTxRxResult(int port_num, int protocol_version)
  {
    return libFunction.getLastTxRxResult(port_num, protocol_version);
  }
  public byte getLastRxPacketError(int port_num, int protocol_version)
  {
    return libFunction.getLastRxPacketError(port_num, protocol_version);
  }

  public void setDataWrite(int port_num, int protocol_version, short data_length, short data_pos, int data)
  {
    libFunction.setDataWrite(port_num, protocol_version, data_length, data_pos, data);
  }
  public int getDataRead(int port_num, int protocol_version, short data_length, short data_pos)
  {
    return libFunction.getDataRead(port_num, protocol_version, data_length, data_pos);
  }

  public void txPacket(int port_num, int protocol_version)
  {
    libFunction.txPacket(port_num, protocol_version);
  }

  public void rxPacket(int port_num, int protocol_version)
  {
    libFunction.rxPacket(port_num, protocol_version);
  }

  public void txRxPacket(int port_num, int protocol_version)
  {
    libFunction.txRxPacket(port_num, protocol_version);
  }

  public void ping(int port_num, int protocol_version, byte id)
  {
    libFunction.ping(port_num, protocol_version, id);
  }

  public int pingGetModelNum(int port_num, int protocol_version, byte id)
  {
    return libFunction.pingGetModelNum(port_num, protocol_version, id);
  }

  public void broadcastPing(int port_num, int protocol_version)
  {
    libFunction.broadcastPing(port_num, protocol_version);
  }
  public Boolean getBroadcastPingResult(int port_num, int protocol_version, int id)
  {
    return libFunction.getBroadcastPingResult(port_num, protocol_version, id);
  }

  public void reboot(int port_num, int protocol_version, byte id)
  {
    libFunction.reboot(port_num, protocol_version, id);
  }

  public void clearMultiTurn(int port_num, int protocol_version, byte id)
  {
    libFunction.clearMultiTurn(port_num, protocol_version, id);
  }
  
  public void factoryReset(int port_num, int protocol_version, byte id, byte option)
  {
    libFunction.factoryReset(port_num, protocol_version, id, option);
  }

  public void readTx(int port_num, int protocol_version, byte id, short address, short length)
  {
    libFunction.readTx(port_num, protocol_version, id, address, length);
  }
  public void readRx(int port_num, int protocol_version, short length)
  {
    libFunction.readRx(port_num, protocol_version, length);
  }
  public void readTxRx(int port_num, int protocol_version, byte id, short address, short length)
  {
    libFunction.readTxRx(port_num, protocol_version, id, address, length);
  }

  public void read1ByteTx(int port_num, int protocol_version, byte id, short address)
  {
    libFunction.read1ByteTx(port_num, protocol_version, id, address);
  }
  public byte read1ByteRx(int port_num, int protocol_version)
  {
    return libFunction.read1ByteRx(port_num, protocol_version);
  }
  public byte read1ByteTxRx(int port_num, int protocol_version, byte id, short address)
  {
    return libFunction.read1ByteTxRx(port_num, protocol_version, id, address);
  }

  public void read2ByteTx(int port_num, int protocol_version, byte id, short address)
  {
    libFunction.read2ByteTx(port_num, protocol_version, id, address);
  }
  public short read2ByteRx(int port_num, int protocol_version)
  {
    return libFunction.read2ByteRx(port_num, protocol_version);
  }
  public short read2ByteTxRx(int port_num, int protocol_version, byte id, short address)
  {
    return libFunction.read2ByteTxRx(port_num, protocol_version, id, address);
  }

  public void read4ByteTx(int port_num, int protocol_version, byte id, short address)
  {
    libFunction.read4ByteTxRx(port_num, protocol_version, id, address);
  }
  public int read4ByteRx(int port_num, int protocol_version)
  {
    return libFunction.read4ByteRx(port_num, protocol_version);
  }
  public int read4ByteTxRx(int port_num, int protocol_version, byte id, short address)
  {
    return libFunction.read4ByteTxRx(port_num, protocol_version, id, address);
  }

  public void writeTxOnly(int port_num, int protocol_version, byte id, short address, short length)
  {
    libFunction.writeTxOnly(port_num, protocol_version, id, address, length);
  }
  public void writeTxRx(int port_num, int protocol_version, byte id, short address, short length)
  {
    libFunction.writeTxRx(port_num, protocol_version, id, address, length);
  }

  public void write1ByteTxOnly(int port_num, int protocol_version, byte id, short address, byte data)
  {
    libFunction.write1ByteTxOnly(port_num, protocol_version, id, address, data);
  }
  public void write1ByteTxRx(int port_num, int protocol_version, byte id, short address, byte data)
  {
    libFunction.write1ByteTxRx(port_num, protocol_version, id, address, data);
  }

  public void write2ByteTxOnly(int port_num, int protocol_version, byte id, short address, short data)
  {
    libFunction.write2ByteTxOnly(port_num, protocol_version, id, address, data);
  }
  public void write2ByteTxRx(int port_num, int protocol_version, byte id, short address, short data)
  {
    libFunction.write2ByteTxRx(port_num, protocol_version, id, address, data);
  }

  public void write4ByteTxOnly(int port_num, int protocol_version, byte id, short address, int data)
  {
    libFunction.write4ByteTxOnly(port_num, protocol_version, id, address, data);
  }
  public void write4ByteTxRx(int port_num, int protocol_version, byte id, short address, int data)
  {
    libFunction.write4ByteTxRx(port_num, protocol_version, id, address, data);
  }

  public void regWriteTxOnly(int port_num, int protocol_version, byte id, short address, short length)
  {
    libFunction.regWriteTxOnly(port_num, protocol_version, id, address, length);
  }
  public void regWriteTxRx(int port_num, int protocol_version, byte id, short address, short length)
  {
    libFunction.regWriteTxRx(port_num, protocol_version, id, address, length);
  }

  public void syncReadTx(int port_num, int protocol_version, short start_address, short data_length, short param_length)
  {
    libFunction.syncReadTx(port_num, protocol_version, start_address, data_length, param_length);
  }

  public void syncWriteTxOnly(int port_num, int protocol_version, short start_address, short data_length, short param_length)
  {
    libFunction.syncWriteTxOnly(port_num, protocol_version, start_address, data_length, param_length);
  }

  public void bulkReadTx(int port_num, int protocol_version, short param_length)
  {
    libFunction.bulkReadTx(port_num, protocol_version, param_length);
  }

  public void bulkWriteTxOnly(int port_num, int protocol_version, short param_length)
  {
    libFunction.bulkWriteTxOnly(port_num, protocol_version, param_length);
  }

  // GroupBulkRead
  public int groupBulkRead(int port_num, int protocol_version)
  {
    return libFunction.groupBulkRead(port_num, protocol_version);
  }

  public Boolean groupBulkReadAddParam(int group_num, byte id, short start_address, short data_length)
  {
    return libFunction.groupBulkReadAddParam(group_num, id, start_address, data_length);
  }
  public void groupBulkReadRemoveParam(int group_num, byte id)
  {
    libFunction.groupBulkReadRemoveParam(group_num, id);
  }
  public void groupBulkReadClearParam(int group_num)
  {
    libFunction.groupBulkReadClearParam(group_num);
  }

  public void groupBulkReadTxPacket(int group_num)
  {
    libFunction.groupBulkReadTxPacket(group_num);
  }
  public void groupBulkReadRxPacket(int group_num)
  {
    libFunction.groupBulkReadRxPacket(group_num);
  }
  public void groupBulkReadTxRxPacket(int group_num)
  {
    libFunction.groupBulkReadTxRxPacket(group_num);
  }

  public Boolean groupBulkReadIsAvailable(int group_num, byte id, short address, short data_length)
  {
    return libFunction.groupBulkReadIsAvailable(group_num, id, address, data_length);
  }
  public int groupBulkReadGetData(int group_num, byte id, short address, short data_length)
  {
    return libFunction.groupBulkReadGetData(group_num, id, address, data_length);
  }

  // GroupBulkWrite
  public int groupBulkWrite(int port_num, int protocol_version)
  {
    return libFunction.groupBulkWrite(port_num, protocol_version);
  }

  public Boolean groupBulkWriteAddParam(int group_num, byte id, short start_address, short data_length, int data, short input_length)
  {
    return libFunction.groupBulkWriteAddParam(group_num, id, start_address, data_length, data, input_length);
  }
  public void groupBulkWriteRemoveParam(int group_num, byte id)
  {
    libFunction.groupBulkWriteRemoveParam(group_num, id);
  }
  public Boolean groupBulkWriteChangeParam(int group_num, byte id, short start_address, short data_length, int data, short input_length, short data_pos)
  {
    return libFunction.groupBulkWriteChangeParam(group_num, id, start_address, data_length, data, input_length, data_pos);
  }
  public void groupBulkWriteClearParam(int group_num)
  {
    libFunction.groupBulkWriteClearParam(group_num);
  }

  public void groupBulkWriteTxPacket(int group_num)
  {
    libFunction.groupBulkWriteTxPacket(group_num);
  }

  // GroupSyncRead
  public int groupSyncRead(int port_num, int protocol_version, short start_address, short data_length)
  {
    return libFunction.groupSyncRead(port_num, protocol_version, start_address, data_length);
  }

  public Boolean groupSyncReadAddParam(int group_num, byte id)
  {
    return libFunction.groupSyncReadAddParam(group_num, id);
  }
  public void groupSyncReadRemoveParam(int group_num, byte id)
  {
    libFunction.groupSyncReadRemoveParam(group_num, id);
  }
  public void groupSyncReadClearParam(int group_num)
  {
    libFunction.groupSyncReadClearParam(group_num);
  }

  public void groupSyncReadTxPacket(int group_num)
  {
    libFunction.groupSyncReadTxPacket(group_num);
  }
  public void groupSyncReadRxPacket(int group_num)
  {
    libFunction.groupSyncReadRxPacket(group_num);
  }
  public void groupSyncReadTxRxPacket(int group_num)
  {
    libFunction.groupSyncReadTxRxPacket(group_num);
  }

  public Boolean groupSyncReadIsAvailable(int group_num, byte id, short address, short data_length)
  {
    return libFunction.groupSyncReadIsAvailable(group_num, id, address, data_length);
  }
  public int groupSyncReadGetData(int group_num, byte id, short address, short data_length)
  {
    return libFunction.groupSyncReadGetData(group_num, id, address, data_length);
  }

  // groupSyncWrite
  public int groupSyncWrite(int port_num, int protocol_version, short start_address, short data_length)
  {
    return libFunction.groupSyncWrite(port_num, protocol_version, start_address, data_length);
  }

  public Boolean groupSyncWriteAddParam(int group_num, byte id, int data, short data_length)
  {
    return libFunction.groupSyncWriteAddParam(group_num, id, data, data_length);
  }
  public void groupSyncWriteRemoveParam(int group_num, byte id)
  {
    libFunction.groupSyncWriteRemoveParam(group_num, id);
  }
  public Boolean groupSyncWriteChangeParam(int group_num, byte id, int data, short data_length, short data_pos)
  {
    return libFunction.groupSyncWriteChangeParam(group_num, id, data, data_length, data_pos);
  }
  public void groupSyncWriteClearParam(int group_num)
  {
    libFunction.groupSyncWriteClearParam(group_num);
  }

  public void groupSyncWriteTxPacket(int group_num)
  {
    libFunction.groupSyncWriteTxPacket(group_num);
  }
}
