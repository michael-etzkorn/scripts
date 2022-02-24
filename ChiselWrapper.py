#    Copyright 2022 Michael Etzkorn

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import hdlparse.verilog_parser as vlog 
import sys 

def snake_to_camel(name):
    name = ''.join(word.title() for word in name.split('_')) 
    return name 

def main():
    #todo: option args for supplying location of resources.
    fname = sys.argv[1]
    package_name = []
    if len(sys.argv) == 3:
        package_name = sys.argv[2]
    if not sys.argv[1]:
      print("Supply a filename from the command line")
      return
                      
    vlog_ex = vlog.VerilogExtractor()
    vlog_mods = vlog_ex.extract_objects(fname)
    # assumes directory path name does not contain "." outside of ".v" or ".sv"
    #TODO: use pathlib? 
    fname_noext = fname.split(".")[0].split("/")[-1]
    # assumes file's first module declaration is top level
    mod = vlog_mods[0]              
    camelMod = snake_to_camel(mod.name.title())
       

    with open(f"{fname_noext}.scala", "w") as f:
        if not package_name: 
            f.write("// package ReplaceMe\n")
        else: 
            f.write(f"package {package_name}\n")
        f.write("import chisel3._ \n")
        f.write("import chisel3.util._ \n")
        # Could probably import on an "as needed" basis for Params.
        f.write("import chisel3.experimental.{IntParam, StringParam, Analog, BaseModule}\n") 

        if mod.generics: # Parameters exist
            f.write(f"case class {camelMod}Params(\n")
            # TODO: A conversion of snake case to camel case for param names would be good for the Scala syntax tool.
            # Shouldn't affect compilation
            for param in mod.generics:
                param_scaltype = "Int" 
                use_x = ""
                use_L = ""
                comma = ","

                if param == mod.generics[-1]: 
                    comma = ""         # No comma for last parameter
                param_value = param.default_value 
                isString    = param_value.find('"')

                h_index     = param_value.find('h')
                if isString != -1:
                    param_scaltype = "String"
                elif h_index != -1:      # Hex number - Set 0x and L prefix and suffix - Use BigInt. 
                    param_scaltype = "BigInt" 
                    use_x = "0x"
                    use_L = "L"
                    param_value = param_value[h_index + 1:]
                
                camelParam = snake_to_camel(param.name)
                f.write(f"\t{camelParam}: {param_scaltype} = {use_x}{param_value}{use_L}{comma}\n")
            f.write(")\n\n")

                
            # Probably a way to inline a conditional concatenation of (val c: NameParams)
            f.write(f"class {mod.name}(val c: {camelMod}Params) extends BlackBox(Map(\n") 
            
            for param in mod.generics: 
                camelParam = snake_to_camel(param.name)
                comma = ","
                if param == mod.generics[-1]:
                    comma = ""
                if param.default_value.find('"') == -1:
                    # NOTE: if we convert name from snake_case to camelCase, this line needs to change
                    f.write(f"\t\"{param.name}\" -> IntParam(c.{camelParam}){comma}\n") 
                else:
                    f.write(f"\t\"{param.name}\" -> StringParam(c.{camelParam}){comma}\n")
            f.write("))")
        else:  
            f.write(f"class {mod.name} extends BlackBox")
        f.write(f" with HasBlackBoxResource with Has{camelMod}IO\n")
        f.write("{\n")

        # TODO: Refactor to allow a directory to be given containing all files to be included 
        #         with option of placing under directory name
        # If contained within a folder with other necessary modules. These will need to be added manually. 
        # Unless we do something clever.
        f.write(f"\taddResource(\"/vsrc/{fname}\")\n") 
        f.write("// IF YOU HAVE MORE RESOURCES ADD THEM HERE \n")
        f.write("}\n")

        # Process ports
        if mod.generics:
            f.write(f"class {camelMod}IO(val c: {camelMod}Params) extends Bundle{{\n")
        else: 
            f.write(f"class {camelMod}IO extends Bundle{{\n")
        
        # WARNING: This assumes clocks have clk (or clock) in their name. 
        # They don't always. Double check input file and output file for correct clock reset names.
        for port in mod.ports:
            direction = ""
            if port.mode == "input":
                direction = "Input"
            elif port.mode == "output":
                direction = "Output"
            else: 
                direction = "Analog" # I assume "inout" is the only other type
            if "clk" in port.name or "clock" in port.name:
                f.write(f"\t val {port.name} = {direction}(Clock())\n")
            else:
                # process datatype
                # TODO: add multidimension port support
                # TODO: don't assume msb:lsb 
                # TODO: don't assume (param math) - 1 for msb
                # TODO: support for structs ?
                    # Need a script to wrap verilog in struct-free verilog. 

                start = port.data_type.find("[") + 1
                middle = port.data_type.find(":")
                msb = port.data_type[start:middle].replace(" ", "")
                end = port.data_type.find("]")

                lsb = port.data_type[middle+1:end].replace(" ", "")
                msb_param_flag = any(c.isalpha() for c in msb)
                # lsb_param_flag = any(c.isalpha() for c in lsb)      # TODO: Support param in second half     
                # portCamel = snake_to_camel(port.name)   
                if end == -1:
                    if direction == "Analog": 
                        f.write(f"\t val {port.name} = {direction}(1.W)\n")
                    else: 
                        f.write(f"\t val {port.name} = {direction}(Bool())\n")
                elif msb_param_flag:
                    # WARNING: I just assume param math is followed by minus one because that's usually the case.
                    # It's easier to find "-" than reparse a parameter name
                    # TODO: should check for $clog2 and replace with log2Ceil
                    minus_idx = port.data_type.find("-")
                    paramName = snake_to_camel(port.data_type[start:minus_idx])

                    #TODO: resolve parentheses bug
                    if paramName[0] == "(":
                        paramName.find(")")

                    
                    if direction == "Analog":
                        f.write(f"\t val {port.name} = {direction}((c.{paramName}).W)\n")
                    else: 
                        f.write(f"\t val {port.name} = {direction}(UInt((c.{paramName}).W))\n")
                else: 
                    if direction == "Analog":
                        f.write(f"\t val {port.name} = {direction}({abs(int(msb) - int(lsb)) + 1}.W)\n")
                    else: 
                        f.write(f"\t val {port.name} = {direction}(UInt({abs(int(msb) - int(lsb)) + 1}.W))\n")
        f.write("\n}\n")
        f.write(f"trait Has{camelMod}IO extends BaseModule {{\n")
        pass_arg = ""
        if mod.generics:
            f.write(f"\tval c: {camelMod}Params\n")
            pass_arg = "(c)"
        f.write(f"\tval io = IO(new {camelMod}IO{pass_arg})\n")
        f.write("}")
                
          

        

                                        


if __name__ == "__main__":
    main()     
