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

import json 
import itertools
import sys

def parse_json_to_regpack_tex():
    with open("RocketSystemTop.anno.json", "r") as json_file: 
        json_string = json_file.read() 
        parsed_json = json.loads(json_string)
    regmap_anno = [x for x in parsed_json if x["class"] == "freechips.rocketchip.util.RegFieldDescMappingAnnotation"]

    # sortkeyfn = itemgetter("group")
    for entry in regmap_anno:
        if entry["regMappingSer"]["displayName"] == sys.argv[1]:
            # print(entry["regMappingSer"]) 
            reg_fields = entry["regMappingSer"]["regFields"]
            curr_group = ""

            # for k,g in itertools.groupby(reg_fields, key= lambda x: x["group"]):
            #     for member in g: 
            #         print(f"{member} is a {k}")
            #             # print("test")

            for reg_field in reg_fields:
                group_name  = reg_field["group"].replace("_","\_")
                reg_name    = reg_field["name"].replace("_","\_")
                byte_offset = reg_field["byteOffset"]
                bitwidth    = reg_field["bitWidth"]
                bit_offset  = reg_field["bitOffset"]
                reset_value = reg_field["resetValue"]
                # Different register group
                if curr_group != "" and group_name != curr_group:
                    print("\\end{register}")
                elif curr_group == "None":
                    print("\\end{register}")

                if group_name == "None":
                    print(f"\\begin{{register}}{{H}}{{{reg_name}}}{{{byte_offset}}}")
                elif group_name != curr_group:
                    print(f"\\begin{{register}}{{H}}{{{group_name}}}{{{byte_offset}}}")

                curr_group = group_name
                print(f"\\regfield{{{reg_name}}}{{{bitwidth}}}{{{bit_offset}}}{{{reset_value}}}")

            print("\\end{register}")
            

    # print(regmap_anno)

# Parsed to produce custom registers similar to RISC-V debug spec:
# https://github.com/riscv/riscv-debug-spec/blob/master/registers.py 
# Still uses register package for floating register list

def parse_json_to_table_tex():
    with open("RocketSystemTop.anno.json", "r") as json_file: 
        json_string = json_file.read() 
        parsed_json = json.loads(json_string)
    regmap_anno = [x for x in parsed_json if x["class"] == "freechips.rocketchip.util.RegFieldDescMappingAnnotation"]

    for entry in regmap_anno:
        if entry["regMappingSer"]["displayName"] == sys.argv[1]: # If display name matches argument, generate .TeX
            reg_fields = entry["regMappingSer"]["regFields"]
            groups = []
            unique_keys = []
            for k,g in itertools.groupby(reg_fields, key= lambda x: x["group"]):
                list_g = list(g)
                if list_g[0]["group"] != "None":
                    groups.append(list_g[::-1])
                else: 
                    groups.append(list_g)
                unique_keys.append(k)


            for group in groups:
                
                tabular_cols = ""
                group_name  = group[0]["group"].replace("_","\_")
                byte_offset = group[0]["byteOffset"]
            
                if group_name != "None":
                    print("\\begin{register}{H}{%s}{%s}" % ( group_name, byte_offset ))
                    print("\\begin{center}")
                for field in group: 

                    # TODO: move these to class attributes of register and field
                        # construct register objects that contain field objects
                    
                    reg_name    = field["name"].replace("_","\_")
                    bit_width    = field["bitWidth"]
                    bit_offset   = field["bitOffset"]

                    high_bit = bit_offset + bit_width - 1
                    low_bit  = bit_offset 
                    
                    # print("%s %s" % (high_bit, low_bit))

                    # assuming no 128-bit or greater registers
                    # assuming no variables in bit width or bit offset
                    high_len = 2.0 if high_bit >= 10 else 1.0 
                    low_len  = 2.0 if low_bit  >= 10 else 1.0

                    # reset_value = field["resetValue"]
                    tabular_cols += "p{%.1f ex}" % ( bit_width * high_len / ( low_len + high_len ) )
                    tabular_cols += "p{%.1f ex}" % ( bit_width * high_len / ( low_len + high_len ) )
                    
                    # This assumes group has no fields.
                    if group_name == "None":
                        print("\\begin{register}{H}{%s}{%s}" % ( reg_name, field["byteOffset"] ))
                        print("\\begin{center}")
                        print("\\begin{tabular}{%s}" % tabular_cols)
                        if high_bit == low_bit: 
                            print("\\multicolumn{2}{c}{\\scriptsize %s}" % high_bit)
                        else: 
                            print("{\\scriptsize %s} &" % high_bit)
                            print("\\multicolumn{1}{r}{\\scriptsize %s}" % low_bit)
                        tabular_cols = "" 
                        print("\\\\")
                        print("         \hline")
                        first = True 
                        cols = "|c|"
                        print("\\multicolumn{2}{%s}{%s}" % ( cols, reg_name))
                        print("\\\\")
                        print("         \hline")
                        print("\\multicolumn{2}{c}{\\scriptsize 32}")
                        print("\\\\")

                        print("   \\end{tabular}")
                        print("\\end{center}")
                        print("\\end{register}")

                        # Create field description table. 
                        print("\\tabletail{\\hline \\multicolumn{4}{|r|}")
                        print("   {{Continued on next page}} \\\\ \\hline}")
                        print("\\begin{longtable}{|l|p{0.5\\textwidth}|c|l|}")
                        print("   \\hline")
                        print("   Field & Description & Access & Reset\\\\")
                        print("   \\hline")
                        print("   \\endhead")

                        print("   \\multicolumn{4}{r}{\\textit{Continued on next page}} \\\\")
                        print("   \\endfoot")
                        print("   \\endlastfoot")
                        reg_name    = field["name"].replace("_","\_")
                        field_desc  = field["desc"]
                        group_desc  = field["groupDesc"]
                        access_type = field["accessType"]
                        reset_value = field["resetValue"]

                        # Can add labels and indexes using the register's name here. 
                        # print("\\label{}")
                        # print("\\index{}")
                        
                        # FIXME: field_desc when using Blocking/NonBlocking Enqueue-Dequeue needs override
                        if field_desc == "Transmit data" or field_desc == "Receive Data":
                            print("%s & %s & %s & %s \\\\" % (reg_name,group_desc,access_type,reset_value))
                        else: 
                            print("%s & %s & %s & %s \\\\" % (reg_name,field_desc,access_type,reset_value))
                        print("\\hline")

                        print("    \\end{longtable}")

                if group_name != "None":
                    print("\\begin{tabular}{%s}" % tabular_cols)
                    pass
                
                first = True
                for field in group: 
                    if group_name == "None":
                        break
                    # reg_name    = field["name"].replace("_","\_")
                    # byte_offset = field["byteOffset"]
                    bit_width    = field["bitWidth"]
                    bit_offset   = field["bitOffset"]
                    high_bit = bit_offset + bit_width - 1
                    low_bit  = bit_offset 
                    high_len = 2.0 if high_bit >= 10 else 1.0 
                    low_len  = 2.0 if low_bit  >= 10 else 1.0

                    if not first and group_name != "None":
                        print("&")
                        
                    first = False 
                    if high_bit == low_bit: 
                        print("\\multicolumn{2}{c}{\\scriptsize %s}" % high_bit)
                    else: 
                        print("{\\scriptsize %s} &" % high_bit)
                        print("\\multicolumn{1}{r}{\\scriptsize %s}" % low_bit)
                if group_name != "None":
                    print("\\\\")
                    print("         \hline")
                    first = True 
                    for field in group:
                        reg_name    = field["name"].replace("_","\_")
                        if first:
                            cols = "|c|"
                        else:
                            cols = "c|"
                            print("&")
                        first = False 
                        print("\\multicolumn{2}{%s}{%s}" % ( cols, reg_name))
                    print("\\\\")
                    print("         \hline")
                    print(" & ".join( "\\multicolumn{2}{c}{\\scriptsize %s}" % field["bitWidth"] for field in group))
                    print("\\\\")

                    print("   \\end{tabular}")
                    print("\\end{center}")
                    print("\\end{register}")
                if group_name != "None":
                    print("\\tabletail{\\hline \\multicolumn{4}{|r|}")
                    print("   {{Continued on next page}} \\\\ \\hline}")
                    print("\\begin{longtable}{|l|p{0.5\\textwidth}|c|l|}")
                    print("   \\hline")
                    print("   Field & Description & Access & Reset\\\\")
                    print("   \\hline")
                    print("   \\endhead")

                    print("   \\multicolumn{4}{r}{\\textit{Continued on next page}} \\\\")
                    print("   \\endfoot")
                    print("   \\endlastfoot")

                for field in group:
                    if group_name != "None":

                        reg_name    = field["name"].replace("_","\_")
                        field_desc  = field["desc"]
                        group_desc  = field["groupDesc"]
                        access_type = field["accessType"]
                        reset_value = field["resetValue"]

                        # Can add labels and indexes using the register's name here. 
                        # print("\\label{}")
                        # print("\\index{}")
                        
                        # FIXME: field_desc when using Blocking/NonBlocking Enqueue-Dequeue needs override
                        if field_desc == "Transmit data" or field_desc == "Receive Data":
                            print("%s & %s & %s & %s \\\\" % (reg_name,group_desc,access_type,reset_value))
                        else: 
                            print("%s & %s & %s & %s \\\\" % (reg_name,field_desc,access_type,reset_value))
                        print("\\hline")

                if group_name != "None":
                    print("  \\end{longtable}")
                



 



if __name__ == "__main__":
    # parse_json_to_regpack_tex()
    parse_json_to_table_tex() 