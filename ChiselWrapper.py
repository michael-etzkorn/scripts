import hdlparse.verilog_parser as vlog 
import sys 


def main():
    #todo: option args for supplying location of resources.
    fname = sys.argv[1]
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

    with open(f"{fname_noext}.scala", "w") as f:
        f.write("// package ReplaceMe\n")
        f.write("import chisel3._ \n")
        f.write("import chisel3.util._ \n")
        # Could probably import on an "as needed" basis for Params.
        f.write("import chisel3.experimental.{IntParam, StringParam, BaseModule}\n") 

        if mod.generics: # Parameters exist
            f.write(f"case class {fname_noext}Params(\n")
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
                
                
                f.write(f"\t{param.name}: {param_scaltype} = {use_x}{param_value}{use_L}{comma}\n")
            f.write(")\n\n")

                
            # Probably a way to inline a conditional concatenation of (val c: NameParams)
            f.write(f"class {fname_noext}(val c: {fname_noext}Params) extends BlackBox(Map(\n") 
            
            for param in mod.generics: 
                comma = ","
                if param == mod.generics[-1]:
                    comma = ""
                if param.default_value.find('"') == -1:
                    # NOTE: if we convert name from snake_case to camelCase, this line needs to change
                    f.write(f"\t\"{param.name}\" -> IntParam(c.{param.name}){comma}\n") 
                else:
                    f.write(f"\t\"{param.name}\" -> StringParam(c.{param.name}){comma}\n")
            f.write("))")
        else:  
            f.write(f"class {fname_noext} extends BlackBox")
        f.write(f" with HasBlackBoxResource with Has{fname_noext}IO\n")
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
            f.write(f"class {fname_noext}IO(val c: {fname_noext}Params) extends Bundle{{\n")
        else: 
            f.write(f"class {fname_noext}IO extends Bundle{{\n")
        
        # NOTE: The snake_case to camelCase idea is tricky here.
        # We need to parse for param names within the data_type then call a function to convert to camelCase. 
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
                    if direction == "Analog":
                        f.write(f"\t val {port.name} = {direction}((c.{port.data_type[start:minus_idx]}).W)\n")
                    else: 
                        f.write(f"\t val {port.name} = {direction}(UInt((c.{port.data_type[start:minus_idx]}).W))\n")
                else: 
                    if direction == "Analog":
                        f.write(f"\t val {port.name} = {direction}({abs(int(msb) - int(lsb)) + 1}.W)\n")
                    else: 
                        f.write(f"\t val {port.name} = {direction}(UInt({abs(int(msb) - int(lsb)) + 1}.W))\n")
        f.write("\n}\n")
        f.write(f"trait Has{fname_noext}IO extends BaseModule {{\n")
        pass_arg = ""
        if mod.generics:
            f.write(f"\tval c: {fname_noext}Params\n")
            pass_arg = "(c)"
        f.write(f"\tval io = IO(new {fname_noext}IO{pass_arg})\n")
        f.write("}")
                
          

        

                                        


if __name__ == "__main__":
    main()     
