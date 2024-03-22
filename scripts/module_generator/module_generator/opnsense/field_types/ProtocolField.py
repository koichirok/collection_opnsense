import os
from pathlib import Path
import sys

if __name__ == "__main__":
    project_root = str(Path(__file__).parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.append(project_root)
# pylint: disable=wrong-import-position
from module_generator.opnsense.field_types.list_field_types import BaseListField


def update_static_option_list(source_file: Path):
    ipv6_ext = {"IPV6-ROUTE", "IPV6-FRAG", "IPV6-OPTS", "IPV6-NONXT", "MOBILITY-HEADER"}
    new_values = []
    with source_file.open(encoding="ascii") as f:
        for line in f:
            if not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 4 and int(parts[1], base=10) > 0:
                    proto = parts[0].upper()
                    # IPv6 extension headers are skipped by the packet filter, we cannot police them
                    if proto not in ipv6_ext:
                        new_values.append(f'        "{proto}": "{proto}",\n')

    # update static _option_list attribute in ProtocolField
    this_file = Path(__file__)
    with this_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    new_content = []
    in_old_values = False
    for line in lines:
        if not in_old_values:
            new_content.append(line)
        if line == "    _option_list = {\n":
            in_old_values = True
            new_content.extend(new_values)
        elif in_old_values and line == "    }\n":
            in_old_values = False
            new_content.append(line)

    this_file.write_text("".join(new_content), encoding="utf-8")


class ProtocolField(BaseListField):
    # To update the list of protocols, run this file as script with the protocol file as an argument
    _option_list = {
        "ICMP": "ICMP",
        "IGMP": "IGMP",
        "GGP": "GGP",
        "IPENCAP": "IPENCAP",
        "ST2": "ST2",
        "TCP": "TCP",
        "CBT": "CBT",
        "EGP": "EGP",
        "IGP": "IGP",
        "BBN-RCC": "BBN-RCC",
        "NVP": "NVP",
        "PUP": "PUP",
        "ARGUS": "ARGUS",
        "EMCON": "EMCON",
        "XNET": "XNET",
        "CHAOS": "CHAOS",
        "UDP": "UDP",
        "MUX": "MUX",
        "DCN": "DCN",
        "HMP": "HMP",
        "PRM": "PRM",
        "XNS-IDP": "XNS-IDP",
        "TRUNK-1": "TRUNK-1",
        "TRUNK-2": "TRUNK-2",
        "LEAF-1": "LEAF-1",
        "LEAF-2": "LEAF-2",
        "RDP": "RDP",
        "IRTP": "IRTP",
        "ISO-TP4": "ISO-TP4",
        "NETBLT": "NETBLT",
        "MFE-NSP": "MFE-NSP",
        "MERIT-INP": "MERIT-INP",
        "DCCP": "DCCP",
        "3PC": "3PC",
        "IDPR": "IDPR",
        "XTP": "XTP",
        "DDP": "DDP",
        "IDPR-CMTP": "IDPR-CMTP",
        "TP++": "TP++",
        "IL": "IL",
        "IPV6": "IPV6",
        "SDRP": "SDRP",
        "IDRP": "IDRP",
        "RSVP": "RSVP",
        "GRE": "GRE",
        "DSR": "DSR",
        "BNA": "BNA",
        "ESP": "ESP",
        "AH": "AH",
        "I-NLSP": "I-NLSP",
        "SWIPE": "SWIPE",
        "NARP": "NARP",
        "MOBILE": "MOBILE",
        "TLSP": "TLSP",
        "SKIP": "SKIP",
        "IPV6-ICMP": "IPV6-ICMP",
        "CFTP": "CFTP",
        "SAT-EXPAK": "SAT-EXPAK",
        "KRYPTOLAN": "KRYPTOLAN",
        "RVD": "RVD",
        "IPPC": "IPPC",
        "SAT-MON": "SAT-MON",
        "VISA": "VISA",
        "IPCV": "IPCV",
        "CPNX": "CPNX",
        "CPHB": "CPHB",
        "WSN": "WSN",
        "PVP": "PVP",
        "BR-SAT-MON": "BR-SAT-MON",
        "SUN-ND": "SUN-ND",
        "WB-MON": "WB-MON",
        "WB-EXPAK": "WB-EXPAK",
        "ISO-IP": "ISO-IP",
        "VMTP": "VMTP",
        "SECURE-VMTP": "SECURE-VMTP",
        "VINES": "VINES",
        "TTP": "TTP",
        "NSFNET-IGP": "NSFNET-IGP",
        "DGP": "DGP",
        "TCF": "TCF",
        "EIGRP": "EIGRP",
        "OSPF": "OSPF",
        "SPRITE-RPC": "SPRITE-RPC",
        "LARP": "LARP",
        "MTP": "MTP",
        "AX.25": "AX.25",
        "IPIP": "IPIP",
        "MICP": "MICP",
        "SCC-SP": "SCC-SP",
        "ETHERIP": "ETHERIP",
        "ENCAP": "ENCAP",
        "GMTP": "GMTP",
        "IFMP": "IFMP",
        "PNNI": "PNNI",
        "PIM": "PIM",
        "ARIS": "ARIS",
        "SCPS": "SCPS",
        "QNX": "QNX",
        "A/N": "A/N",
        "IPCOMP": "IPCOMP",
        "SNP": "SNP",
        "COMPAQ-PEER": "COMPAQ-PEER",
        "IPX-IN-IP": "IPX-IN-IP",
        "CARP": "CARP",
        "PGM": "PGM",
        "L2TP": "L2TP",
        "DDX": "DDX",
        "IATP": "IATP",
        "STP": "STP",
        "SRP": "SRP",
        "UTI": "UTI",
        "SMP": "SMP",
        "SM": "SM",
        "PTP": "PTP",
        "ISIS": "ISIS",
        "CRTP": "CRTP",
        "CRUDP": "CRUDP",
        "SPS": "SPS",
        "PIPE": "PIPE",
        "SCTP": "SCTP",
        "FC": "FC",
        "RSVP-E2E-IGNORE": "RSVP-E2E-IGNORE",
        "UDPLITE": "UDPLITE",
        "MPLS-IN-IP": "MPLS-IN-IP",
        "MANET": "MANET",
        "HIP": "HIP",
        "SHIM6": "SHIM6",
        "WESP": "WESP",
        "ROHC": "ROHC",
        "PFSYNC": "PFSYNC",
        "DIVERT": "DIVERT",
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        uname = os.uname()
        if uname.sysname == "FreeBSD":
            print("INFO: No protocol file is specified, using /etc/protocols")
            file = "/etc/protocols"
        else:
            print("A protocol file is required", file=sys.stderr)
            print(f"Usage: {sys.argv[0]} <protocol_file>", file=sys.stderr)
            sys.exit(1)
    file = Path(file)
    if not file.exists():
        print(f"File not found: {file}", file=sys.stderr)
        sys.exit(1)
    update_static_option_list(file)
