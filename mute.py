from scapy.all import ARP, Ether, srp

target = "192.168.1.1/24"
arp = ARP(pdst=target)
ether = Ether(dst="ff:ff:ff:ff:ff:ff")
packet = ether / arp

result = srp(packet, timeout=3, verbose=0)[0]

devices = []
for sent, received in result:
    devices.append({'ip': received.psrc, 'mac': received.hwsrc})

print("Found:", len(devices), "devices")
for dev in devices:
    print(f"  {dev['ip']} → {dev['mac']}")
    