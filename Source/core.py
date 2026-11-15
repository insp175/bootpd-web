import ipaddress
import re

DEFAULT = dict(
    interface="",
    subnet="192.168.50.0/24",
    server="192.168.50.1",
    start="192.168.50.100",
    end="192.168.50.200",
    lease=3600,
)


def validate(data):
    if not isinstance(data, dict) or set(data) != set(DEFAULT):
        raise ValueError("Expected interface, subnet, server, start, end and lease")
    c = dict(data)
    labels = {
        "interface": "Ethernet interface",
        "subnet": "Subnet (CIDR)",
        "server": "Mac IPv4 address",
        "start": "Pool start",
        "end": "Pool end",
    }
    for key, label in labels.items():
        if not isinstance(c[key], str) or not c[key].strip():
            raise ValueError(label + " is required")
        c[key] = c[key].strip()
    if not isinstance(c["interface"], str) or not re.fullmatch(
        "en[0-9]+", c["interface"]
    ):
        raise ValueError("Select an Ethernet interface (enN)")
    net = ipaddress.IPv4Network(c["subnet"], strict=True)
    if (
        not 16 <= net.prefixlen <= 30
        or not net.is_private
        or net.is_loopback
        or net.is_link_local
    ):
        raise ValueError("Use a private IPv4 subnet with a /16 to /30 prefix")
    if not any(
        (
            net.subnet_of(ipaddress.IPv4Network(n))
            for n in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
        )
    ):
        raise ValueError("Only RFC1918 subnets are allowed")
    ips = [ipaddress.IPv4Address(c[k]) for k in ("server", "start", "end")]
    if any(
        (x not in net or x in (net.network_address, net.broadcast_address) for x in ips)
    ):
        raise ValueError("All addresses must be valid hosts in the subnet")
    (server, start, end) = ips
    if start > end or start <= server <= end:
        raise ValueError("Invalid range or server IP overlaps the pool")
    if type(c["lease"]) is not int or not 120 <= c["lease"] <= 604800:
        raise ValueError("Lease must be an integer between 120 and 604800 seconds")
    c["subnet"] = str(net)
    for key, ip in zip(("server", "start", "end"), ips):
        c[key] = str(ip)
    return c


def plist_config(c):
    c = validate(c)
    net = ipaddress.IPv4Network(c["subnet"])
    return dict(
        dhcp_enabled=[c["interface"]],
        bootp_enabled=False,
        relay_enabled=False,
        netboot_enabled=False,
        Subnets=[
            dict(
                name="Bootpd Panel",
                net_address=str(net.network_address),
                net_mask=str(net.netmask),
                net_range=[c["start"], c["end"]],
                allocate=True,
                lease_min=c["lease"],
                lease_max=c["lease"],
                dhcp_router=[],
                dhcp_domain_name_server=[],
            )
        ],
    )


def parse_leases(raw):
    result = []
    for block in re.findall("\\{([^{}]*)\\}", raw):
        fields = dict(
            (line.strip().split("=", 1) for line in block.splitlines() if "=" in line)
        )
        try:
            ip = str(ipaddress.IPv4Address(fields["ip_address"]))
            hw = fields.get("hw_address", "").split(",")[-1].lower()
            parts = hw.split(":")
            if len(parts) != 6 or any(
                (not re.fullmatch("[0-9a-f]{1,2}", p) for p in parts)
            ):
                continue
            mac = ":".join((p.zfill(2) for p in parts))
            expiry = (
                int(fields["lease"], 0)
                if fields["lease"].startswith("0x")
                else int(fields["lease"])
            )
            result.append(
                dict(
                    ip=ip, mac=mac, hostname=fields.get("name", "")[:255], expiry=expiry
                )
            )
        except (KeyError, ValueError):
            continue
    return result


def parse_arp(raw, interface):
    result = []
    for line in raw.splitlines():
        m = re.search("\\(([^)]+)\\) at ([0-9a-fA-F:]+) on (\\S+)", line)
        if not m or m[3] != interface:
            continue
        try:
            ip = ipaddress.IPv4Address(m[1])
            parts = m[2].split(":")
            if len(parts) != 6 or any(
                (not re.fullmatch("[0-9a-fA-F]{1,2}", x) for x in parts)
            ):
                continue
            mac = ":".join((x.zfill(2).lower() for x in parts))
            if (
                int(parts[0], 16) & 1
                or int(mac.replace(":", ""), 16) == 0
                or ip.is_multicast
            ):
                continue
            result.append(dict(ip=str(ip), mac=mac))
        except ValueError:
            continue
    return result
