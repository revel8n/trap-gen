# -*- coding: iso-8859-1 -*-
####################################################################################
#         ___        ___           ___           ___
#        /  /\      /  /\         /  /\         /  /\
#       /  /:/     /  /::\       /  /::\       /  /::\
#      /  /:/     /  /:/\:\     /  /:/\:\     /  /:/\:\
#     /  /:/     /  /:/~/:/    /  /:/~/::\   /  /:/~/:/
#    /  /::\    /__/:/ /:/___ /__/:/ /:/\:\ /__/:/ /:/
#   /__/:/\:\   \  \:\/:::::/ \  \:\/:/__\/ \  \:\/:/
#   \__\/  \:\   \  \::/~~~~   \  \::/       \  \::/
#        \  \:\   \  \:\        \  \:\        \  \:\
#         \  \ \   \  \:\        \  \:\        \  \:\
#          \__\/    \__\/         \__\/         \__\/
#
#   This file is part of TRAP.
#
#   TRAP is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this TRAP; if not, write to the
#   Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA.
#   or see <http://www.gnu.org/licenses/>.
#
#   (c) Luca Fossati, fossati@elet.polimi.it
#
####################################################################################


import trap
import cxx_writer

#-------------------------------------------------------
# Miscellaneous operations which can be used and
# accessed by any instruction
#-------------------------------------------------------
# *******
# Here we define some helper methods, which are not directly part of the
# instructions, but which can be called by the instruction body
# *******

# Method used to move to the next register window; this simply consists in
# the check that there is an empty valid window and in the update of
# the window aliases
IncrementRegWindow_code = """
newCwp = ((unsigned int)(PSR[key_CWP] + 1)) % NUM_REG_WIN;
if(((0x01 << (newCwp)) & WIM) != 0){
    // There is a window underflow exception: TODO
}
PSR[key_CWP] = newCwp;
"""
for i in range(8, 32):
    IncrementRegWindow_code += 'REGS[' + str(i) + '].updateAlias(WINREGS[(PSR[key_CWP]*16 + ' + str(i) + ') % (16*NUM_REG_WIN)]);\n'
opCode = cxx_writer.writer_code.Code(IncrementRegWindow_code)
IncrementRegWindow_method = trap.HelperMethod('IncrementRegWindow', opCode, 'execute')
IncrementRegWindow_method.addVariable(('newCwp', 'BIT<32>'))
# Method used to move to the previous register window; this simply consists in
# the check that there is an empty valid window and in the update of
# the window aliases
DecrementRegWindow_code = """
newCwp = ((unsigned int)(PSR[key_CWP] - 1)) % NUM_REG_WIN;
if(((0x01 << (newCwp)) & WIM) != 0){
    // There is a window overflow exception: TODO
}
PSR[key_CWP] = newCwp;
"""
for i in range(8, 32):
    DecrementRegWindow_code += 'REGS[' + str(i) + '].updateAlias(WINREGS[(PSR[key_CWP]*16 + ' + str(i) + ') % (16*NUM_REG_WIN)]);\n'
opCode = cxx_writer.writer_code.Code(DecrementRegWindow_code)
DecrementRegWindow_method = trap.HelperMethod('DecrementRegWindow', opCode, 'execute')
DecrementRegWindow_method.addVariable(('newCwp', 'BIT<32>'))

# Sign extends the input bitstring
opCode = cxx_writer.writer_code.Code("""
if((bitSeq & (1 << (bitSeq_length - 1))) != 0)
    bitSeq |= (((unsigned int)0xFFFFFFFF) << bitSeq_length);
return bitSeq;
""")
SignExtend_method = trap.HelperMethod('SignExtend', opCode, 'execute')
SignExtend_method.setSignature(('BIT<32>'), [('bitSeq', 'BIT<32>'), cxx_writer.writer_code.Parameter('bitSeq_length', cxx_writer.writer_code.uintType)])

# Normal PC increment, used when not in a branch instruction; in a branch instruction
# I will directly modify both PC and nPC in case we are in a the cycle accurate model,
# while just nPC in case we are in the functional one; if the branch has the annulling bit
# set, then also in the functional model both the PC and nPC will be modified
opCode = cxx_writer.writer_code.Code("""PC = NPC;
NPC += 4;
""")
IncrementPC = trap.HelperOperation('IncrementPC', opCode)

# Code used to jump to the trap handler address. This code modifies the PC and the NPC
# so that the next instruction fetched is the one of the trap handler.

# Write back of the result of most operations, expecially ALUs;
# such operations do not modify the PSR
opCode = cxx_writer.writer_code.Code("""
rd = result;
""")
WB_plain = trap.HelperOperation('WB_plain', opCode)
WB_plain.addInstuctionVar(('result', 'BIT<32>'))
WB_plain.addUserInstructionElement('rd')

# Write back of the result of most operations, expecially ALUs;
# such operations also modify the PSR
opCode = cxx_writer.writer_code.Code("""
rd = result;
PSR = PSRbp;
""")
WB_icc = trap.HelperOperation('WB_icc', opCode)
WB_icc.addInstuctionVar(('result', 'BIT<32>'))
WB_icc.addUserInstructionElement('rd')

# Write back of the result of mutiplication operations
# which modify the ICC conditions codes and the Y register
opCode = cxx_writer.writer_code.Code("""
rd = result;
PSR = PSRbp;
Y = Ybp;
""")
WB_yicc = trap.HelperOperation('WB_yicc', opCode)
WB_yicc.addInstuctionVar(('result', 'BIT<32>'))
WB_yicc.addUserInstructionElement('rd')

# Write back of the result of MAC operations
# which modify the ICC conditions codes, the Y register, and ASR[18]
opCode = cxx_writer.writer_code.Code("""
rd = result;
PSR = PSRbp;
Y = Ybp;
ASR[18] = ASR18bp;
""")
WB_yiccasr = trap.HelperOperation('WB_yiccasr', opCode)
WB_yiccasr.addInstuctionVar(('result', 'BIT<32>'))
WB_yiccasr.addUserInstructionElement('rd')

# Write back of the result of MAC operations
# which modify the Y register, and ASR[18]
opCode = cxx_writer.writer_code.Code("""
rd = result;
Y = Ybp;
ASR[18] = ASR18bp;
""")
WB_yasr = trap.HelperOperation('WB_yasr', opCode)
WB_yasr.addInstuctionVar(('result', 'BIT<32>'))
WB_yasr.addUserInstructionElement('rd')

# Write back of the normal of mutiplication operations
# which modify the Y register
opCode = cxx_writer.writer_code.Code("""
rd = result;
Y = Ybp;
""")
WB_y = trap.HelperOperation('WB_y', opCode)
WB_y.addInstuctionVar(('result', 'BIT<32>'))
WB_y.addUserInstructionElement('rd')

# Modification of the Integer Condition Codes of the Processor Status Register
# after an logical operation or after the multiply operation
opCode = cxx_writer.writer_code.Code("""
PSRbp = PSR;
PSRbp[key_ICC_n] = ((result & 0x80000000) >> 31);
PSRbp[key_ICC_z] = (result == 0);
PSRbp[key_ICC_v] = 0;
PSRbp[key_ICC_c] = 0;
""")
ICC_writeLogic = trap.HelperOperation('ICC_writeLogic', opCode)
ICC_writeLogic.addInstuctionVar(('result', 'BIT<32>'))

# Modification of the Integer Condition Codes of the Processor Status Register
# after an addition operation
opCode = cxx_writer.writer_code.Code("""
PSRbp = PSR;
PSRbp[key_ICC_n] = ((result & 0x80000000) >> 31);
PSRbp[key_ICC_z] = (result == 0);
PSRbp[key_ICC_v] = ((unsigned int)((rs1_op & rs2_op & (~result)) | ((~rs1_op) & (~rs2_op) & result))) >> 31;
PSRbp[key_ICC_c] = ((unsigned int)((rs1_op & rs2_op) | ((rs1_op | rs2_op) & (~result)))) >> 31;
""")
ICC_writeAdd = trap.HelperOperation('ICC_writeAdd', opCode)
ICC_writeAdd.addInstuctionVar(('result', 'BIT<32>'))
ICC_writeAdd.addInstuctionVar(('rs1_op', 'BIT<32>'))
ICC_writeAdd.addInstuctionVar(('rs2_op', 'BIT<32>'))

# Modification of the Integer Condition Codes of the Processor Status Register
# after an subtraction operation
opCode = cxx_writer.writer_code.Code("""
PSRbp = PSR;
PSRbp[key_ICC_n] = ((result & 0x80000000) >> 31);
PSRbp[key_ICC_z] = (result == 0);
PSRbp[key_ICC_v] = ((unsigned int)((rs1_op & (~rs2_op) & (~result)) | ((~rs1_op) & rs2_op & result))) >> 31;
PSRbp[key_ICC_c] = ((unsigned int)(((~rs1_op) & rs2_op) | (((~rs1_op) | rs2_op) & result))) >> 31;
""")
ICC_writeSub = trap.HelperOperation('ICC_writeSub', opCode)
ICC_writeSub.addInstuctionVar(('result', 'BIT<32>'))
ICC_writeSub.addInstuctionVar(('rs1_op', 'BIT<32>'))
ICC_writeSub.addInstuctionVar(('rs2_op', 'BIT<32>'))
