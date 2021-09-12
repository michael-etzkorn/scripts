import hdlparse.verilog_parser as vlog 



def main():
    fname = ""                         # Insert your file name here TODO: move this to command line
    vlog_ex = vlog.VerilogExtractor()
    vlog_mods = vlog_ex.extract_objects(fname)
    given_class_name = ""              # TODO: Add CLI parser
    fname_noext = fname.split(".")[0]  # assumes file name does not contain "." outside of ".v" or ".sv"
    # given_class_name = pass
    if given_class_name == "":
        given_class_name = fname_noext 
    
    mod = vlog_mods[0]                 # assumes file contains only a top level module (unclear on how Chisel's Blackbox API handles multiple modules in top)

    with open(f"{given_class_name}.scala", "w") as f: # TODO: allow naming of output .scala file from command line with given_class_name
        f.write("// package ReplaceMe\n")
        f.write("import chisel3._ \n")
        f.write("import chisel3.util._ \n")
        f.write("import chisel3.experimental.{IntParam, BaseModule}\n")

        if mod.generics: # Parameters exist
            f.write(f"case class {given_class_name}Params(\n")
            for param in mod.generics: # TODO: A conversion of snake case to camel case for param names would be good for the Scala syntax tool, but shouldn't affect compilation
                param_scaltype = "Int" 
                use_x = ""
                use_L = ""
                comma = ","
                #if param == next(reversed(mod.generics)) # I thought mod.generics was an ordered dict. Not sure if a list is worse for run time or not. Something to look into if improving/maintaing hdlparse at all
                if param == mod.generics[-1]: 
                    comma = ""         # No comma for last parameter
                param_value = param.default_value 
                h_index     = param_value.find('h')
                if h_index != -1:      # Hex number - Set 0x and L prefix and suffix - Use BigInt. 
                    param_scaltype = "BigInt" 
                    use_x = "0x"
                    use_L = "L"
                    param_value = param_value[h_index + 1:]
                f.write(f"\t{param.name}: {param_scaltype} = {use_x}{param_value}{use_L}{comma}\n")
            f.write(")\n\n")

                

            f.write(f"class {given_class_name}BlackBox(val c: {given_class_name}Params) extends BlackBox(Map(\n") # Probably a way to inline a conditional concatenation of (val c: NameParams)
            
            for param in mod.generics: 
                comma = ","
                if param == mod.generics[-1]:
                    comma = ""
                f.write(f"\t\"{param.name}\" -> IntParam(c.{param.name}){comma}\n") # NOTE: if we convert name from snake_case to camelCase, this line needs to change
            f.write("))")
        else:  
            f.write(f"class {given_class_name}BlackBox extends BlackBox")
        f.write(f" with HasBlackBoxResource with Has{given_class_name}IO\n")
        f.write("{\n")

         # TODO: Refactor to allow a directory to be given containing all files to be included with option of placing under directory name
        f.write(f"\taddResource(\"/vsrc/{fname}\")\n") # If contained within a folder with other necessary modules. These will need to be added manually. Unless we do something clever.
        f.write("// IF YOU HAVE MORE RESOURCES ADD THEM HERE \n")
        f.write("}\n")

        # Process ports
        if mod.generics:
            f.write(f"class {given_class_name}(val c: {given_class_name}Params) extends Bundle{{\n")
        else: 
            f.write(f"class {given_class_name} extends Bundle{{\n")
        
        # NOTE: The snake_case to camelCase idea is tricky here. We need to parse for param names within the data_type then call a function to convert to camelCase. 
        # WARNING: This assumes clock and resets have clk and rst in their name. They don't always. Double check input file and output file for correct clock reset names.
        for port in mod.ports:
            direction = ""
            if port.mode == "input":
                direction = "Input"
            elif port.mode == "output":
                direction = "Output"
            else: 
                direction = "Analog" # I assume "inout" is the only other type
            if "clk" in port.name:
                f.write(f"\t val {port.name} = {direction}(Clock())\n")
            elif "rst" in port.name and "burst" not in port.name:  # WARNING: there are 490+ words in the English language that contain 'rst' ... 
                f.write(f"\t val {port.name} = {direction}(Bool())\n")
            else:
                # process datatype
                # TODO: add multidimension port support
                # TODO: don't assume msb:lsb 
                # TODO: don't assume (param math) - 1 for msb
                # TODO: support for structs ?  - I don't know how that works in chisel 

                start = port.data_type.find("[") + 1
                middle = port.data_type.find(":")
                msb = port.data_type[start:middle].replace(" ", "")
                end = port.data_type.find("]")

                lsb = port.data_type[middle+1:end].replace(" ", "")
                msb_param_flag = any(c.isalpha() for c in msb)
                # lsb_param_flag = any(c.isalpha() for c in lsb)      # TODO: Support param in second half
                                      
                if end == -1:
                    f.write(f"\t val {port.name} = {direction}(Bool())\n")
                elif msb_param_flag:
                    # WARNING: I just assume param math is followed by minus one because that's usually the case and it's easier to find "-" than parse a parameter name
                    minus_idx = port.data_type.find("-")
                    f.write(f"\t val {port.name} = {direction}(UInt(({port.data_type[start:minus_idx]}).W))\n")
                else: 
                    f.write(f"\t val {port.name} = {direction}(UInt({abs(int(msb) - int(lsb) + 1)}.W))\n")
        f.write("\n}\n")
        f.write(f"trait Has{given_class_name}IO extends BaseModule {{\n")
        pass_arg = ""
        if mod.generics:
            f.write(f"\tval c: {given_class_name}Params\n")
            pass_arg = "(c)"
        f.write(f"\tval io = IO(new {given_class_name}IO{pass_arg})\n")
        f.write("}")
                
          

        

                                        


if __name__ == "__main__":
    main()     