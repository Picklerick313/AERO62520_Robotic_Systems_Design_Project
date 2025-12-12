# Intel NUC Configuration

## 1. Install Ubuntu (22.04 or 24.04)

Follow official instructions:  
https://ubuntu.com/tutorials/install-ubuntu-desktop

---

## 2. Install ROS2 Jazzy

```bash
sudo apt update
sudo apt install ros-jazzy-desktop
```

---

## 3. Configure Networking

Edit netplan:

```bash
sudo nano /etc/netplan/01-nuc-eth.yaml
```

Paste:

```yaml
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    enp114s0:
      addresses:
        - 192.168.12.2/24
      dhcp4: no
```

Apply:

```bash
sudo chmod 600 /etc/netplan/*.yaml
sudo netplan apply
```

Verify:

```bash
ip addr show enp114s0
```

---

## 4. Setup ROS Environment

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=10" >> ~/.bashrc
echo "export ROS_LOCALHOST_ONLY=0" >> ~/.bashrc
source ~/.bashrc
```

