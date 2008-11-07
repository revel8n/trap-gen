/***************************************************************************\
 *
 *
 *            ___        ___           ___           ___
 *           /  /\      /  /\         /  /\         /  /\
 *          /  /:/     /  /::\       /  /::\       /  /::\
 *         /  /:/     /  /:/\:\     /  /:/\:\     /  /:/\:\
 *        /  /:/     /  /:/~/:/    /  /:/~/::\   /  /:/~/:/
 *       /  /::\    /__/:/ /:/___ /__/:/ /:/\:\ /__/:/ /:/
 *      /__/:/\:\   \  \:\/:::::/ \  \:\/:/__\/ \  \:\/:/
 *      \__\/  \:\   \  \::/~~~~   \  \::/       \  \::/
 *           \  \:\   \  \:\        \  \:\        \  \:\
 *            \  \ \   \  \:\        \  \:\        \  \:\
 *             \__\/    \__\/         \__\/         \__\/
 *
 *
 *
 *
 *   This file is part of TRAP.
 *
 *   TRAP is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU Lesser General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Lesser General Public License for more details.
 *
 *   You should have received a copy of the GNU Lesser General Public License
 *   along with this program; if not, write to the
 *   Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 *   or see <http://www.gnu.org/licenses/>.
 *
 *
 *
 *   (c) Luca Fossati, fossati@elet.polimi.it
 *
\***************************************************************************/

/**
 * Class used to manage connections with the GDB server.
 */

#ifndef GDBCONNECTIONMANAGER_HPP
#define GDBCONNECTIONMANAGER_HPP

#include <string>
#include <vector>
#include <iostream>
#include <boost/asio.hpp>

using namespace boost;

/**
 * High level repesentation of a GDB request packet
 */
struct GDBRequest{
    enum Type {QUEST=0, EXCL, c, C, D, g, G, H, i, I, k, m, M, p, P, q, s, S, t, T, X, z, Z, UNK, ERROR, INTR};
    Type type;
    unsigned int address;
    unsigned int length;
    unsigned int reg;
    unsigned int signal;
    int value;
    std::string command;
    std::string extension;
    std::vector<char> data;
    GDBRequest(){
        address = 0;
        length = 0;
        reg = 0;
        signal = 0;
        value = 0;
        command = "";
        extension = "";
    }
};

/**
 * High level repesentation of a GDB response packet
 */
struct GDBResponse{
    enum Type {S=0, T, W, X, OUTPUT, OK, ERROR, MEM_READ, REG_READ, NOT_SUPPORTED};
    Type type;
    unsigned int payload;
    std::string message;
    unsigned int size;
    std::vector<char> data;
    std::vector<std::pair<std::string, unsigned int> > info;
    GDBResponse(){
        payload = 0;
        message = "";
        size = 0;
    }
};

/**
 * Manages the connection among the GDB debugger and the stub which communicates with
 * the processor; it is responsible of handling socket connection and
 * of the coding and decoding of the messages.
 * For more details on the internal workings of GDB look at http://sourceware.org/gdb/current/onlinedocs/gdb_33.html
 */
class GDBConnectionManager{
  private:
   ///Represents the currently open connection
   asio::ip::tcp::socket * socket;
   ///Specifies the endianess of the current processor; true means
   ///that it is the same endianess of the host, false, otherwise
   bool endianess;
   ///Computes the checksum for the data
   unsigned char computeChecksum(std::string &data);
   ///Checks that the checksum included in the packet is correct
   bool checkChecksum(std::string &data, char checkSum[2]);
   ///Converts a generic numeric value into a string of hex numbers;
   ///each hex number of the string is in the same order of the endianess
   ///of the processor linked to this stub
   std::string toHexString(unsigned int value, int numChars = -1);
   ///Converts an hexadecimal number expressed with a string
   ///into its correspondent integer number
   ///each hex number of the string is in the same order of the endianess
   ///of the processor linked to this stub
   unsigned int toIntNum(std::string &toConvert);
   ///Converts a hexadecimal number into the corresponding character string
   std::string toStr(std::string &toConvert);
   ///Converts a hex character to an int representing it
   int chToHex(unsigned char ch);
   ///Converts and integer hex to a char representing it
   unsigned char hexToInt(unsigned int num);
   ///Map used to convert hex strings in integers
   std::map<char, unsigned int> HexMap;
   ///Specifis whether communication has been coled by the other endpoint or not
   bool killed;
  public:
   GDBConnectionManager(bool endianess);
   ~GDBConnectionManager();
   ///Creates a socket connection waiting on the specified port;
   ///this will be later used to communicate with GDB
   void initialize(unsigned int port);
   ///Sends the response to the GDB debugger connected
   void sendResponse(GDBResponse &response);
   ///Waits for the sending of a packet from GDB; it then parses it and
   ///translates it into the correct request
   GDBRequest processRequest();
   ///Closes the connection with the GDB debugger
   void disconnect();
   ///Sends and interrupt message to the GDB debugger signaling that
   ///the execution of the program halted: this way the GDB
   ///debugger becomes responsive and it is possible to debug the
   ///program under test
   void sendInterrupt();
};

#endif
