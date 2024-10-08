#Autor: Fabrício Nhantumbo
#Data: 24/04/2024
#email: fabrisansao@gmail.com


#costum utility to solve some vlsm exercises at school

import sys
import math



def usage(outfile):
    print("""\
Usage:
    vlsm -a <base_addr> -m <base_net_mask> -n (<necessity>  ... )
        -a        specifies the base network address for creating the subnets.
        -m        specifies the base net mask.
        -n        a space separated list of the needs for each network.
        Note: the necessities have to specify only the amount of hosts required per network (do not include network and broadcast, it is implied)""", file=outfile)


def break_out(message : str = None):
    if message is not None:
        sys.stderr.write(f"{message}\n")
    usage(sys.stderr)
    exit(1)

def int_to_str_ip(ip: int) -> str:
    repr=""
    for i in range(4):
        octect = ip & 0xFF
        ip >>= 8
        if(0 < i < 4):
            repr = "." + repr
        repr =  str(octect) + repr 
    return repr


def str_to_int_ip(ip: str) -> int:
    res=0
    for (i, v) in enumerate(ip.split('.')):
        res += int(v) * (256 ** (3 - i)) 
    return res

def ceil_log_2(val) -> int: 
    '''returns applies log2 followed by ceil in the argument'''
    l = math.log2(val)
    l = math.ceil(l)
    return l

    
class SubnetEntry:
    def __init__(self, ip: int, mask: int):
        self.ip : int = ip
        self.mask : int = mask
        self.num_of_hosts : int = 2 ** (32 - mask)

    def first_host(self) -> int :
        return self.ip + 1

    def last_host(self) -> int:
        return self.ip + self.num_of_hosts - 2 

    def broadcast_ip(self) -> int:
        return self.ip + self.num_of_hosts - 1



def get_ipv4(val: str) -> int:
    ls = val.split('.')
    result = len(ls) == 4
    for v in ls:
        result = result and str.isnumeric(v) and 0 <= int(v) < 256
    if result:
        return str_to_int_ip(val)
    break_out(f"Error: Invalid ip format: {val}")


def get_valid_num(val: str, message : str = None, min : int = 0, max : int = 0xFFFFFFFF):
    if str.isnumeric(val) and min <= int(val) <= max:
        return int(val)
    break_out(message)


#can validate base mask only here and not in parsing arguments, because all masks will pass from this function before going to final entries
def necessity_mask(necessity: int, base_mask: int = 0) -> int:
    l2 = ceil_log_2(necessity)
    error_message= f"Error: Necessity exceeds base mask /{base_mask} capacity\n\
    Necessity requires {2**l2} hosts: mask capacity = {2**(32 - base_mask)} host, necessity is {necessity}."
    mask = get_valid_num(str(32 - l2), error_message, base_mask, 32)
    return mask


def shift_list(args):
    return args[0], args[1:]

#does not check necessities agains base mask, only parses the command line arguments and returns them
def parse_args(argv : list[str]) -> tuple[int, int, list[int]]:
    #values to return
    ip   : int = 0
    mask : int = 0
    needs: list[int] = []

    #flags (to verify if command is complete)
    got_ip = False
    got_mask = False
    got_needs = False

    #parse arguments
    while len(argv) > 0:
        if len(argv) < 2:
            break_out("Error: Not enough arguments.")
        option, argv = shift_list(argv)
        match option:
            case "-a":
                if got_ip: break_out("Error: -a flag must be specified once.")
                val, argv = shift_list(argv)
                ip = get_ipv4(val)
                got_ip = True
            case "-m":
                if got_mask: break_out("Error: -m flags must be specified once.")
                val, argv = shift_list(argv)
                mask = get_valid_num(val, "Error: Invalid mask, mask mast be between 0 and 32.", 0, 32)
                got_mask = True
            case "-n":
                if got_needs: break_out("Error: -n flags must be specified once.")
                while len(argv) > 0 and (argv[0] != '-a' or argv[0] != 'm'):
                    val, argv = shift_list(argv)
                    needs.append(get_valid_num(val, "Error: Necessity must be positive."))
                got_needs = True
            case _ :
                break_out(f"Error: Unknown option {option}.")

    #incomplete command specification            
    if(not(got_ip and got_mask and got_needs)):
         break_out()
  
    #to fill the table the needs must be in descending order
    needs.sort(reverse=True) 
    #valid arguments (from here is only happy path)  
    return (ip, mask, needs)

def build_table(base_ip: int, base_mask : int, necessities : list[int]) -> list[SubnetEntry]:
    entries: list[SubnetEntry] = []
    
    necessities = [n + 2 for n in necessities] # add extra two necessities for network address and broadcast address
    amount_of_hosts : list[int] = [2 ** ceil_log_2(n) for n in necessities]  #turn all necessities into powers of 2
    current_ip : int = base_ip
    host_alloced_amount : int = 0
    for necessity, host_amount in zip(necessities, amount_of_hosts):
        entry : SubnetEntry = SubnetEntry(current_ip, necessity_mask(necessity, base_mask))
        entries.append(entry)
        current_ip += host_amount
        host_alloced_amount += host_amount 

    #check to see if allocated amount of host does not violate the mask
    mask_capacity =  2 ** (32 - base_mask)
    if host_alloced_amount > mask_capacity:
        break_out(f"Error: The base mask /{base_mask} is not enough for the necessities\n    Maximum with mask = {mask_capacity}, needed {host_alloced_amount}.")    
    return entries


#Todo: generalize the table printing method, for use in other projects
def print_table(entries: list[SubnetEntry]):
    #cw stands for column witdh
    ip_cw = 16      #for ip
    m_cw = 6       #for mask
    num_cw = 10     #for normal numbers
    horz_sep = f"+{'-'*(num_cw)}+{'-'*(ip_cw)}+{'-'*(m_cw)}+{'-'*(ip_cw)}+{'-'*(ip_cw)}+{'-'*(ip_cw)}+"
    ip_fmt = f"^{ip_cw}"
    m_fmt = f"^{m_cw}"
    num_fmt = f"^{num_cw}"

    #table header
    print(horz_sep)
    print(f"\
|{"num-hosts":{num_fmt}}\
|{"subnetwork ip":{ip_fmt}}\
|{"mask":{m_fmt}}\
|{"first valid":{ip_fmt}}\
|{"last valid":{ip_fmt}}\
|{"broadcast":{ip_fmt}}|")
    print(horz_sep)
    #table body
    for e in entries:
        print(f"\
|{str(e.num_of_hosts):{num_fmt}}\
|{int_to_str_ip(e.ip):{ip_fmt}}\
|{("/"+str(e.mask)):{m_fmt}}\
|{int_to_str_ip(e.first_host()):{ip_fmt}}\
|{int_to_str_ip(e.last_host()):{ip_fmt}}\
|{int_to_str_ip(e.broadcast_ip()):{ip_fmt}}|")
    print(horz_sep)

if __name__ == '__main__':
    program = sys.argv[0]
    argv = sys.argv[1:]
    entries = parse_args(argv)
    ip, mask, necessities = entries
    print_table(build_table(ip, mask, necessities))
    exit(0)