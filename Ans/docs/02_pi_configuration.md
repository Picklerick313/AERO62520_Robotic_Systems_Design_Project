# Raspberry Pi Configuration (LeoOS)

## 1. Discover Pi

```bash
sudo arp -a
sudo nmap -sn 192.168.12.0/24
```

SSH in:

```bash
ssh pi@<detected_ip>
```

---

## 2. Find Ethernet interface

```bash
ip link
```

Record `<PI_INTERFACE>`.

---

## 3. Configure Static IP

```bash
sudo nano /etc/netplan/01-pi-eth.yaml
```

Paste:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    <PI_INTERFACE>:
      addresses:
        - 192.168.12.1/24
      dhcp4: no
```

Apply:

```bash
sudo chmod 600 /etc/netplan/*.yaml
sudo netplan apply
```

Verify:

```bash
ip addr show <PI_INTERFACE>
```

