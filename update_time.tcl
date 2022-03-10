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


# The following script is used to adjust the min and max input/output delays for an .xdc constraint file
# Need to set $tochange and $changeto in tcl console. 
# Path file could also be changed to be set this way 


set timestamp [clock format [clock seconds] -format {%Y%m%d%H%M%S}]


set filename "path/to/constraints.xdc"
set temp $filename.new.$timestamp
set backup $filename.bak.$timestamp

set in [open $filename r]
set out [open $temp w] 



while {[gets $in line] != -1} {

	if {[string first $tochange $line] != -1} {
		set line [string map [list $tochange $changeto] $line] 	
	}
	
	puts $out $line
}
close $in
close $out

file link -hard $backup $filename
file rename -force $temp $filename 

reset_timing
read_xdc /path/to/constraints.xdc
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 100 -input_pins -routable_nets -name timing_2
