# A compendium of written scripts

[![Join the chat at https://gitter.im/Sage-Dallas/community](https://badges.gitter.im/Sage-Dallas/community.svg)](https://gitter.im/Sage-Dallas/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

### Script Ideas
- [x] Create a script that generates the collateral for a blackbox verilog module in Chisel
  - [ ] If the connections are AXI, making the aw, ar, b, r, and w connections to an AXI Master/Slave node 
  - [ ] If connections have ready/valid/bits and common prefix use `DecoupledIO`
- [ ] Script to control VCS runs from python shell. 
- [x] Generate `.tex` documentation from `.anno.json` files that use Chisel's `RegField` 
### `ChiselWrapper.py`
- Currently supported by [this fork](https://github.com/hdl/pyhdlparser) of HDLParse. 
- With decent accuracy, and a few known issues, produces blackbox boilerplate collateral for Chisel RTL that interfaces with Verilog. VerilogParser's regexes can be modified to include logic in the type search for some simple SV blackbox support. 
