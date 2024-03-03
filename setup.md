# Setup for the machine pve01

This document aims to enumerate different steps followed to install and setup *Proxmox* as a home-lab.

The author hopes to thank many people that shared their experiences, and that he found valuable to write this document.

The *proxmox* is installed on a dedicated server on Internet, but it could be also hosting in a local network.

## 1 - Installing Proxmox 8

We aim to install **Prxomox 8** on a **HP Proliant BL460c** machine. The processor is relatively old, and the only install way that was successful out of the box is the **Proxmox 6.4**. Else, the system will be extremely slow and will generate many issues on the screen. Indeed, the last kernel that supports the processor **Intel Xeon E5-2651v2** is **Linux 5.4**.

After *googling*, we found that the **Proxmox 8** and any newer Linux kernels based oses could be install by adding the boot loader parameter `intremap=off`. This parameter will has no effect on the system unless we would like to work with GPU-Passthrough (in particular for Windows VMs). In the install phase, just edit the bootloader with that parameter (*e* for edit the boot loader, and then *F10* to boot).

Somme error messages could then raise, but still harmless:
- DMAR: [Firmware Bug]: No firmware reserved region can cover this RMRR [0x000000008d800000-0x000000008fffffff], contact BIOS vendor for fixes
- firmware bug: the BIOS has corrupted hw-PMU resources We can ignore this bug (linux problem)
- ACPI WARNING (BUG): INVALID LENGTH FOR FAST/PM1aCONTROLBLOCK: 32 using default 16

In the install phase, we considered using **193.110.81.0** DNS from DNS0.EU (https://www.dns0.eu/zero).

Then, and after the reboot, we make an update for the system, and we install some useful tools:

    apt update && apt upgrade -y
    apt install --no-install-recommends sudo nano htop iotop zip unzip neofetch -y

Finally, we update the bootloader so it will boot with the parameter `intremap=off`:

    nano /etc/default/grub # and add intremap=off in GRUB_CMDLINE_LINUX_DEFAULT
    echo "options vfio_iommu_type1 allow_unsafe_interrupts=1" > /etc/modprobe.d/iommu_unsafe_interrupts.conf
    update-grub
    reboot

## 2 - Test the system performances

In this section, we are focusing on testing the system performances in term of disk write/read speed, and memory read/write speed, and finally the CPU single/multiple speed.

In **Proxmox** documentation, they talked about the **sysbench** tool. But here, I prefer to get speed value that I can understand rather that get a score to be compared to other machines.

First, we install the **ioping** and **pigz** tools:

    apt install -y ioping pigz

Second, we test the disk write and read speed:

    ioping -S64M -L -s4k -W -c 10 . # for write speed
    ioping -A -D -s16k -c 10 . # for read speed

For the memory speed test, we proceed as the disk test, but with creating a temporary RAM disk:

    mkdir -p /tmp/ram
    mount -t tmpfs -o size=512M tmpfs /tmp/ram/

Then, we test the RAM write and read speed:

    ioping -S64M -L -s4k -W -c 10 /tmp/ram/ # for write speed
    ioping -A -s16k -c 10 /tmp/ram/ # for read speed

We test now the CPU in single-core and multi-cores setups. This test simply compute 
how much time the CPU will spend for a compression task:

    time cat </dev/urandom | head -c 1G | gzip >/dev/null # sigle-core setup
    time cat </dev/urandom | head -c 1G | pigz >/dev/null # multi-core setup

Finally, we clean up and remove the installed tools:

    apt remove --purge -y ioping pigz
    umount /tmp/ram
    rm -rf /tmp/ram

## 3 - Proxmox Post-Install

This section concerns making some tweaks for the Proxmox system. The website https://tteck.github.io/Proxmox/ provides many useful tools for such a purpose.

    bash -c "$(wget -qLO - https://github.com/tteck/Proxmox/raw/main/misc/post-pve-install.sh)"

This above shell command provides some options for managing Proxmox VE repositories, including disabling the Enterprise Repo, adding or correcting PVE sources, enabling the No-Subscription Repo, adding the test Repo, disabling the subscription nag, updating Proxmox VE, and rebooting the system.

For our case, we are **not** motivated by adding the **Test Repo**, nor disabling the **HA** service (HIGH AVAILABILITY).

## 4 - Optimisation of the Proxmox system

The optimization of the **Proxmox** system is important since the Linux kernel is configured to work with a classical computer. In this section, we focus on configuring the system to deal with a number of VMs.

> This section is based on information and codes provided in : https://github.com/ehlesp/smallab-k8s-pve-guide/blob/main/G015%20-%20Host%20optimization%2001%20~%20Adjustments%20through%20sysctl.md

We will work on optimizing the network, then the memory and finally the kernel. This will be done through **sysctl**.
The, we address to alleviate the **Proxmox** system by disabling some useless services.

### 4.1 Network optimization

    cat << EOF | sudo tee -a /etc/sysctl.d/85_network_optimizations.conf

    ## NETWORK optimizations

    # TCP Fast Open is an extension to the transmission control protocol (TCP)
    # that helps reduce network latency by enabling data to be exchanged during
    # the sender’s initial TCP SYN [3]. Using the value 3 instead of the default 1
    # allows TCP Fast Open for both incoming and outgoing connections.
    net.ipv4.tcp_fastopen = 3

    # Wait a maximum of 5 * 2 = 10 seconds in the TIME_WAIT state after a FIN,
    # to handle any remaining packets in the network.
    # Load module nf_conntrack if needed.
    # BEWARE: this parameter won't be available if the firewall hasn't been enabled first!
    # Value is an INTEGER.
    net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 5

    # Keepalive optimizations
    #
    # TCP keepalive is a mechanism for TCP connections that help to determine whether
    # the other end has stopped responding or not. TCP will send the keepalive probe
    # that contains null data to the network peer several times after a period of idle
    # time. If the peer does not respond, the socket will be closed automatically.
    #
    # By default, the keepalive routines wait for two hours (7200 secs)
    # before sending the first keepalive probe, and then resend it every 75 seconds.
    # If no ACK response is received for 9 consecutive times, the connection
    # is marked as broken. As long as there is TCP/IP socket communications going on
    # and active, no keepalive packets are needed.
    #
    # The default values are:
    # tcp_keepalive_time = 7200, tcp_keepalive_intvl = 75, tcp_keepalive_probes = 9
    #
    # We would decrease the default values for tcp_keepalive_* params as follow:
    #
    # Disconnect dead TCP connections after 10 minutes
    # https://sysctl-explorer.net/net/ipv4/tcp_keepalive_time/
    # Value in SECONDS.
    net.ipv4.tcp_keepalive_time = 60
    #
    # Determines the wait time between isAlive interval probes.
    # https://sysctl-explorer.net/net/ipv4/tcp_keepalive_intvl/
    # Value in SECONDS.
    net.ipv4.tcp_keepalive_intvl = 10
    #
    # Determines the number of probes before timing out.
    # https://sysctl-explorer.net/net/ipv4/tcp_keepalive_probes/
    net.ipv4.tcp_keepalive_probes = 6

    # The longer the maximum transmission unit (MTU) the better for performance,
    # but the worse for reliability. This is because a lost packet means more data
    # to be retransmitted and because many routers on the Internet cannot deliver
    # very long packets.
    net.ipv4.tcp_mtu_probing = 1

    # Maximum number of connections that can be queued for acceptance.
    net.core.somaxconn = 256000

    # How many half-open connections for which the client has not yet
    # sent an ACK response can be kept in the queue or, in other words,
    # the maximum queue length of pending connections 'Waiting Acknowledgment'.
    # SYN cookies only kick in when this number of remembered connections is surpassed.
    # Handle SYN floods and large numbers of valid HTTPS connections.
    net.ipv4.tcp_max_syn_backlog = 40000

    # Maximal number of packets in the receive queue that passed through the network
    # interface and are waiting to be processed by the kernel.
    # Increase the length of the network device input queue.
    net.core.netdev_max_backlog = 50000

    # Huge improve Linux network performance by change TCP congestion control to BBR
    # (Bottleneck Bandwidth and RTT).
    # BBR congestion control computes the sending rate based on the delivery
    # rate (throughput) estimated from ACKs.
    # https://djangocas.dev/blog/huge-improve-network-performance-by-change-tcp-congestion-control-to-bbr/
    net.core.default_qdisc = fq
    net.ipv4.tcp_congestion_control = bbr

    # Increase ephemeral IP ports available for outgoing connections.
    # The ephemeral port is typically used by the Transmission Control Protocol (TCP),
    # User Datagram Protocol (UDP), or the Stream Control Transmission Protocol (SCTP)
    # as the port assignment for the client end of a client–server communication.
    # https://www.cyberciti.biz/tips/linux-increase-outgoing-network-sockets-range.html
    net.ipv4.ip_local_port_range = 30000 65535

    # This is a setting for large networks (more than 128 hosts), and this includes
    # having many virtual machines or containers running in the Proxmox VE platform.
    # https://www.serveradminblog.com/2011/02/neighbour-table-overflow-sysctl-conf-tunning/
    net.ipv4.neigh.default.gc_thresh1 = 1024
    net.ipv4.neigh.default.gc_thresh2 = 4096
    # The gc_thresh3 is already set at /usr/lib/sysctl.d/10-pve-ct-inotify-limits.conf

    # Limits number of Challenge ACK sent per second, as recommended in RFC 5961.
    # Improves TCP’s Robustness to Blind In-Window Attacks.
    # https://sysctl-explorer.net/net/ipv4/tcp_challenge_ack_limit/
    net.ipv4.tcp_challenge_ack_limit = 9999

    # Sets whether TCP should start at the default window size only for new connections
    # or also for existing connections that have been idle for too long.
    # This setting kills persistent single connection performance and could be turned off.
    # https://sysctl-explorer.net/net/ipv4/tcp_slow_start_after_idle/
    # https://github.com/ton31337/tools/wiki/tcp_slow_start_after_idle---tcp_no_metrics_save-performance
    net.ipv4.tcp_slow_start_after_idle = 0

    # Maximal number of sockets in TIME_WAIT state held by the system simultaneously.
    # After reaching this number, the system will start destroying the sockets
    # that are in this state. Increase this number to prevent simple DOS attacks.
    # https://sysctl-explorer.net/net/ipv4/tcp_max_tw_buckets/
    net.ipv4.tcp_max_tw_buckets = 500000

    # Sets whether TCP should reuse an existing connection in the TIME-WAIT state
    # for a new outgoing connection, if the new timestamp is strictly bigger than
    # the most recent timestamp recorded for the previous connection.
    # This helps avoid from running out of available network sockets
    # https://sysctl-explorer.net/net/ipv4/tcp_tw_reuse/
    net.ipv4.tcp_tw_reuse = 1

    # Increase Linux autotuning TCP buffer limits.
    # The default the Linux network stack is not configured for high speed large
    # file transfer across WAN links (i.e. handle more network packets) and setting
    # the correct values may save memory resources.
    # Values in BYTES.
    net.core.rmem_default = 1048576
    net.core.rmem_max = 16777216
    net.core.wmem_default = 1048576
    net.core.wmem_max = 16777216
    net.core.optmem_max = 65536
    net.ipv4.tcp_rmem = 4096 1048576 2097152
    net.ipv4.tcp_wmem = 4096 65536 16777216

    # In case UDP connections are used, these limits should also be raised.
    # Values in BYTES.
    # https://sysctl-explorer.net/net/ipv4/udp_rmem_min/
    net.ipv4.udp_rmem_min = 8192
    # https://sysctl-explorer.net/net/ipv4/udp_wmem_min/
    net.ipv4.udp_wmem_min = 8192

    # The maximum length of dgram socket receive queue.
    net.unix.max_dgram_qlen = 1024
    
    EOF

### 4.2 Memory optimization

    cat << EOF | sudo tee -a /etc/sysctl.d/85_memory_optimizations.conf

    ## Memory optimizations

    # Define how aggressive the kernel will swap memory pages.
    # The value represents the percentage of the free memory remaining
    # in the system's RAM before activating swap.
    # https://sysctl-explorer.net/vm/swappiness/
    # Value is a PERCENTAGE.
    vm.swappiness = 2

    # Allow application request allocation of virtual memory
    # more than real RAM size (or OpenVZ/LXC limits).
    # https://sysctl-explorer.net/vm/overcommit_memory/
    vm.overcommit_memory = 1

    # Controls the tendency of the kernel to reclaim the memory
    # which is used for caching of directory and inode objects.
    # Adjusting this value higher than the default one (100) should
    # help in keeping the caches down to a reasonable level.
    # Value is a PERCENTAGE.
    # https://sysctl-explorer.net/vm/vfs_cache_pressure/
    vm.vfs_cache_pressure = 500

    # How the kernel will deal with old data on memory.
    #
    # The kernel flusher threads will periodically wake up and write
    # `old’ data out to disk.
    # Value in CENTISECS (100 points = 1 second)
    # https://sysctl-explorer.net/vm/dirty_writeback_centisecs/
    vm.dirty_writeback_centisecs = 3000
    #
    # Define when dirty data is old enough to be eligible for
    # writeout by the kernel flusher threads.
    # https://sysctl-explorer.net/vm/dirty_expire_centisecs/
    # Value in CENTISECS (100 points = 1 second)
    vm.dirty_expire_centisecs = 18000

    # Adjustment of vfs cache to decrease dirty cache, aiming for a faster flush on disk.
    # 
    # Percentage of system memory that can be filled with “dirty” pages
    # — memory pages that still need to be written to disk — before the
    # pdflush/flush/kdmflush background processes kick in to write it to disk.
    # https://sysctl-explorer.net/vm/dirty_background_ratio/
    # Value is a PERCENTAGE.
    vm.dirty_background_ratio = 5
    #
    # Absolute maximum percentage amount of system memory that can be filled with
    # dirty pages before everything must get committed to disk.
    # https://sysctl-explorer.net/vm/dirty_ratio/
    # Value is a PERCENTAGE.
    vm.dirty_ratio = 10

    # Indicates the current number of "persistent" huge pages in the
    # kernel's huge page pool.
    # https://sysctl-explorer.net/vm/nr_hugepages/
    # https://www.kernel.org/doc/Documentation/vm/hugetlbpage.txt
    vm.nr_hugepages = 1
    EOF

### 4.3 Kernel optimization

    cat << EOF | sudo tee -a /etc/sysctl.d/85_kernel_optimizations.conf

    ## Kernel optimizations

    # Controls whether unprivileged users can load eBPF programs.
    # For most scenarios this is recommended to be set as 1 (enabled).
    # This is a kernel hardening concern rather than a optimization one, but
    # is left here since its just this value. 
    kernel.unprivileged_bpf_disabled=1

    # Process Scheduler related settings
    #
    # Determines how long a migrated process has to be running before the kernel
    # will consider migrating it again to another core. So, a higher value makes
    # the kernel take longer before migrating again an already migrated process.
    # Value in MILLISECONDS.
    kernel.sched_migration_cost_ns = 5000000
    #
    # This setting groups tasks by TTY, to improve perceived responsiveness on an
    # interactive system. On a server with a long running forking daemon, this will
    # tend to keep child processes from migrating away as soon as they should.
    # So in a server it's better to leave it disabled.
    kernel.sched_autogroup_enabled = 0

    EOF

### 4.3 Disabling unused services

Since we do not use ZFS, CEPH, SPCICE PROXY and high availability, we can disable them to optimize used memory:

    # disable zfs (if the main filesystem is different)
    sudo systemctl disable --now zfs-mount.service zfs-share.service zfs-volume-wait.service zfs-zed.service zfs-import.target zfs-volumes.target zfs.target

    # disable ceph
    sudo systemctl disable --now ceph-fuse.target ceph.target
    sudo systemctl mask --now ceph.target

    # disable spice proxy
    sudo systemctl mask --now spiceproxy

    # disable cluster and high availability 
    sudo systemctl disable --now pve-ha-crm pve-ha-lrm corosync

    # rebooting so the modification will be applied
    sudo reboot

### 4.4 Improve ZFS filesystem performances

We can activate `zstd` compression on ZFS in order to gain some performance increase.

    zfs set compression=zstd rpool
    zfs get compression rpool

Then, we disable the `atime` only on rpool/ROOT/pve-1 and rpool/data:
    
    zfs set atime=off rpool
    zfs get atime rpool

Then, we `xattr` and `dnodesize` only for the data volume only:

    zfs set xattr=sa dnodesize=auto rpool/data
    zfs set xattr=sa rpool
    zfs get xattr rpool/data
    zfs get xattr rpool
    zfs get dnodesize rpool/data

Finally, we activate `autotrim` option:

    zpool set autotrim=on rpool
    zpool get autotrim rpool

### 4.5 Improve BTRFS filesystem performances

#### SSD TRIM

> source https://btrfs.readthedocs.io/en/latest/ch-mount-options.html
> https://wiki.archlinux.org/title/Btrfs

Trim or discard is an operation on a storage device based on flash technology (like ssd SSD and NVMe), a thin-provisioned device or could be emulated on top of other block device types. 

We could enable the asynchronous trim in the /etc/fstab file through adding the option: `discard=async`.
We can also apply fstrim manually through the command: `fstrim`.

to make a manual defragmentation:

    btrfs filesystem defragment -r /

to apply the compression option to the current files:

    btrfs filesystem defragment -r -v -czstd /



## 3 - Proxmox hardening

### 3.1 Create an alternative administrator user (mgrsys)

> This section is based on information and codes provided in : https://github.com/ehlesp/smallab-k8s-pve-guide/blob/main/G008%20-%20Host%20hardening%2002%20~%20Alternative%20administrator%20user.md

Since **root** is the superuser with all the privileges, using it directly on any Linux server has always the potential for creating all sorts of problems (security related or of any other kind). To mitigate those problems, the recommended thing to do is to create an alternative administrator user with sudo privileges and use it instead of root.

    adduser mgrsys  # create the new user
    adduser mgrsys sudo # add the new user to the sudo group
    pveum groupadd pvemgrs -comment "PVE System Managers" # add a new group in proxmox
    pveum aclmod / -group pvemgrs -role Administrator # adjust the new group roles
    pveum user add mgrsys@pam -comment "PVE System Manager" -email "medzarka@gmail.com" -firstname "PVE" -lastname "SysManager" -groups pvemgrs # add the new user to the new created proxmox group

Now connect to the new created user and type:

    ssh-keygen -P "" -m PEM -t rsa -b 4096 -C "mgrsys@pve"  # create ssh key pair for the new user
    > /home/mgrsys/.ssh/authorized_keys # clear the authorized keys
    cat /home/mgrsys/.ssh/id_rsa.pub >> /home/mgrsys/.ssh/authorized_keys
    chmod -R go= /home/mgrsys/.ssh
    chown -R mgrsys:mgrsys /home/mgrsys/.ssh

Finally, create a TAF for the new created user, and we save the created ssh keys in a save place.


### 3.2 Manage the root user

The **root** user will be kept, but the access to it will be more complicated. For the **Proxmox** user interface, the new created user **mgrsys** will be enough. And the access to root shell, will be through **sudo**.

In this section, we aim to install the **pass** password manager (which will be synchronized with git). Then, we will update the root password with a hard one, and we create ssh key pair for it.

#### 3.2.1 Create the root ssh keys

First, we create a ssh key for the **root** user. This will be mandatory for the following steps.

    ssh-keygen -P "" -m PEM -t rsa -b 4096 -C "root@pve"  # create ssh key pair for the new user
    > /root/.ssh/authorized_keys # clear the authorized keys
    cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
    chmod -R go= /root/.ssh
    chown -R root:root /root/.ssh

#### 3.2.2 Install GPG and PASS

    apt install gnupg2
    rm -rf ~/.gnupg
    mkdir -m 0700 ~/.gnupg
    touch ~/.gnupg/gpg.conf
    chmod 600 ~/.gnupg/gpg.conf
    
    cat << EOF > ~/.gnupg/gpg.conf
    # Prohibit the inclusion of the version string in the ASCII armored output
    no-emit-version
    # disallow including a comment line in plain text signatures and ASCII armored messages
    no-comments
    # Display long keyid-formats
    keyid-format 0xlong
    # Do not include key id's in encrypted packets
    throw-keyids
    EOF

    gpg --list-keys # to list the available keys

    cat << EOF > ~/.gnupg/keydetails
    %echo Generating a basic OpenPGP key
    %echo More configuration are avaiable at https://www.gnupg.org/documentation/manuals/gnupg/Unattended-GPG-key-generation.html
    Key-Type: RSA
    Key-Length: 4096
    Subkey-Type: RSA
    Subkey-Length: 4096
    Name-Real: mzarka
    Name-Comment: mzarka gpg keys
    Name-Email: medzarka@gmail.com
    Expire-Date: 0
    %ask-passphrase
    # %no-ask-passphrase
    # %no-protection
    # %pubring pubring.kbx
    # %secring trustdb.gpg
    # Do a commit here, so that we can later print "done" :-)
    %commit
    %echo done
    EOF

    gpg --verbose --batch --gen-key ~/.gnupg/keydetails
    echo -e "5\ny\n" |  gpg --command-fd 0 --expert --edit-key medzarka@gmail.com trust;
    gpg --list-keys

    echo "install and configure pass (password manager) ..."
    apt install --no-install-recommends pass scdaemon -y
    pass init medzarka@gmail.com

    ## To generate a password, display it, and finally delete it:
    #pass generate path/to/key 100 
    #pass path/to/key
    #pass rm path/to/key

    apt install --no-install-recommends git -y
    # on github, create a new repository, and upload the public ssh key.
    pass git init
    pass git remote add origin <<THE GIT REPOSITORY>>
    pass git push -u --all
    # No, every stored password will be saved on git.

#### 3.2.3 Update the root password with pass

Since **PASSS** is installed, we can create now a secure root password.

    pass generate system/root 100
    ROOT_PASS=`pass system/root`
    echo "root:$ROOT_PASS" | chpasswd

Finally, create a TAF for the **root** user, and we save the created ssh keys in a save place.

### 3.3 Hardening the ssh access

In this section, we will make the access to the **Proxmox** server through **ssh** more complex:

    # Disable the dns usage for more speed,
    sed -r -i 's/^#?UseDNS.*/UseDNS no/g' /etc/ssh/sshd_config

    #Diable accessing ssh through password
    sed -r -i 's/^#?PermitEmptyPasswords.*/PermitEmptyPasswords no/g' /etc/ssh/sshd_config
    
    #Disabling X11Forwarding
    sed -r -i 's/^#?X11Forwarding.*/X11Forwarding no/g' /etc/ssh/sshd_config
    
    #Enabling accessing ssh through ssk keys
    sed -r -i 's/^#?PubkeyAuthentication.*/PubkeyAuthentication yes/g' /etc/ssh/sshd_config
    
    #Enabling accessing ssh through passwords
    sed -r -i 's/^#?PasswordAuthentication.*/PasswordAuthentication no/g' /etc/ssh/sshd_config

    #Disabling the root login
    sed -r -i 's/^#?PermitRootLogin.*/PermitRootLogin no/g' /etc/ssh/sshd_config

Then, we tweak the ssh connections to keep them working even after some minutes of inactivity:

    sed -r -i 's/^#?ClientAliveInterval.*/ClientAliveInterval 60/g' /etc/ssh/sshd_config
    sed -r -i 's/^#?TCPKeepAlive.*/TCPKeepAlive yes/g' /etc/ssh/sshd_config
    sed -r -i 's/^#?ClientAliveCountMax.*/ClientAliveCountMax 10000/g' /etc/ssh/sshd_config

On the client side, the *~/.ssh/config* file should contains the follwing instructions:

    Host *
        ServerAliveInterval 240
        ClientAliveCountMax 10000

After creating the ssh key pairs, we can connect to the server from the client side by one of the following commands:

    ssh-copy-id root@SERVER_IP
    cat ~/.ssh/id_rsa.pub | ssh root@SERVER_IP "mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && chmod -R go= ~/.ssh && cat >> ~/.ssh/authorized_keys"

Finally, restart the **ssh** server.

    sudo systemctl restart ssh
    sudo systemctl restart sshd

## 4 - Configuring the proxmox Firewall

> More information could be gathered on the Proxmox system on the website https://pve.proxmox.com/wiki/Firewall

To configure the firewall, we will consider two zones (Security Group):

- WAN: to handle connections from the Internet,
- HOST: to handle connections from internal machines (VMs).

For the **WAN** zone, we will accept only the following connections:

- ICMP from the server hosting service only (so that the server will be seen as alive),
- 22/TCP to access to the server through ssh,
- 8006/TCP to access to the server through the Proxmox Admin GUI.

> To get the IP address of the hosting server, we open the ICMP access and we put the firewall logging on for that rule.

For the **HOST** zone, we will accept only the following connections:

- ICMP from the all the VMs,
- 8006/TCP to access to the server through the Proxmox Admin GUI from the VMs,
- 22/TCP to access ssh through the VMs.

By default, all the outgoing connections are allowed, and the rest of incoming connections are denied.

## 5 - Proxmox LXC templates

Proxmox provide a wide list of LXC images for many Linux ditributions (Ubuntu, Debian, Opensuse, Centos, Turnkey, ...). To update this list, type the following command in the shell:

    pveam update

## 6 - Misc

### 6.1 - Daily System update

    cat << EOF > /etc/cron.daily/system-update
    #!/bin/bash
    sudo apt update
    sudo apt upgrade -y
    sudo apt-get -y clean 
    sudo apt-get -y autoclean 
    sudo apt-get -y autoremove 
    EOF

    chmod a+x /etc/cron.daily/system-update
    run-parts --test /etc/cron.daily/ # to check

### 6.2 - Daily System backup

The backup of the **Proxmox** system will be done through **rclone**. In this section, we will install **rclone** configure it. Then, we will create a script that will be called after each dump operation.

    apt install --no-install-recommends rclone
    pass generate system/rclone/config 100
    rclone config # configure the backup server, and protect the configuration a generated password
    mkdir -p /root/bin

    cat << EOF > /etc/cron.daily/backup-rclone
    #!/bin/bash

    ############ /START CONFIG
    dumpdir="/var/lib/vz/dump/" # Set this to where the vzdump files are stored
    confdir="/var/lib/vz/configs/" # Set this to where the config files are stored
    MAX_AGE=7 # This is the age in days to keep local backup copies.
    export PASSWORD_STORE_DIR=/root/.password-store
    export RCLONE_PASSWORD_COMMAND='/bin/bash -l -c "/usr/bin/pass system/rclone/config"'
    export RCLONE_CONFIG_PASS=$(/bin/bash -l -c "/usr/bin/pass system/rclone/config")
    LOGFILE="/var/log/backup-rclone.log"
    ############ /END CONFIG

    mkdir -p  /var/log/rclone
    mkdir -p  "$confdir"

    echo " ######## Deleting backups and configs older than $MAX_AGE days." >> $LOGFILE 2>&1
    find $dumpdir -type f -mtime +$MAX_AGE -exec /bin/rm -f {} \; >> $LOGFILE 2>&1
    find $confdir -type f -mtime +$MAX_AGE -exec /bin/rm -f {} \; >> $LOGFILE 2>&1
    echo " ######## Done." >> $LOGFILE 2>&1

    echo " ######## Backing up $dumpdir to remote storage ..." >> $LOGFILE 2>&1

    echo " ----- > create the remote dir (myServers/pve01/dumps)" >> $LOGFILE 2>&1
    /usr/bin/rclone mkdir -v --ask-password=false \
    --config /root/.config/rclone/rclone.conf \
    --log-file /var/log/rclone/rclone.log \
    pcloud:/SyncCloud/myServers/pve01/dumps >> $LOGFILE 2>&1

    echo " ----- > Synchronize remote files" >> $LOGFILE 2>&1
    /usr/bin/rclone sync -v --ask-password=false --ignore-size --create-empty-src-dirs \
    --config /root/.config/rclone/rclone.conf --delete-during \
    --log-file /var/log/rclone/rclone.log \
    $dumpdir pcloud:/SyncCloud/myServers/pve01/dumps >> $LOGFILE 2>&1

    echo " ######## Done." >> $LOGFILE 2>&1


    echo " ######## Backing up main PVE configs" >> $LOGFILE 2>&1

    echo " ----- > Warming up" >> $LOGFILE 2>&1
    _tdir=${TMP_DIR:-/var/tmp} 
    _tdir=$(mktemp -d $_tdir/proxmox-XXXXXXXX)
    function clean_up {
        echo "Cleaning up"
        rm -rf $_tdir
    }
    trap clean_up EXIT
    _now=$(date +%Y-%m-%d.%H.%M.%S)
    _HOSTNAME=$(hostname -f)
    _filename1="$_tdir/proxmoxetc.$_now.tar"
    _filename2="$_tdir/proxmoxpve.$_now.tar"
    _filename3="$_tdir/proxmoxroot.$_now.tar"
    _filename4="$confdir/proxmox_backup_"$_HOSTNAME"_"$_now".tar.gz"

    echo " ----- > Create tar files" >> $LOGFILE 2>&1
    # copy key system files
    tar --warning='no-file-ignored' -cPf "$_filename1" /etc/. >> $LOGFILE 2>&1
    tar --warning='no-file-ignored' -cPf "$_filename2" /var/lib/pve-cluster/. >> $LOGFILE 2>&1
    tar --warning='no-file-ignored' -cPf "$_filename3" /root/. >> $LOGFILE 2>&1

    echo " ----- > Compressing files" >> $LOGFILE 2>&1
    tar -cvzPf "$_filename4" $_tdir/*.tar >> $LOGFILE 2>&1

    echo " ----- > create the remote dir (myServers/pve01/configs)" >> $LOGFILE 2>&1
    /usr/bin/rclone mkdir -v --ask-password=false \
    --config /root/.config/rclone/rclone.conf \
    --log-file /var/log/rclone/rclone.log \
    pcloud:/SyncCloud/myServers/pve01/configs >> $LOGFILE 2>&1

    echo " ----- > Synchronize remote files from $confdir" >> $LOGFILE 2>&1
    /usr/bin/rclone sync -v --ask-password=false --ignore-size --create-empty-src-dirs \
    --config /root/.config/rclone/rclone.conf --delete-during \
    --log-file /var/log/rclone/rclone.log \
    $confdir pcloud:/SyncCloud/myServers/pve01/configs >> $LOGFILE 2>&1
    echo " ######## Done." >> $LOGFILE 2>&1
    EOF

    #chmod a+x /root/bin/backup-rclone.sh
    #sed -r -i 's/^#?script.*/script:\/root\/bin\/vzbackup-rclone.sh/g' /etc/vzdump.conf 

    chmod a+x /etc/cron.daily/backup-rclone
    run-parts --test /etc/cron.daily/ # to check

After this step, the system will call the above script daily. Please to consider to schedule a fill backup (for all the VMs) for each Sunday at 1am.

### 6.2 - Other

The website https://tteck.github.io/Proxmox/ provides valuable scripts to install and configure many things on the Proxmox system.

## 7 - VM and network organization

### 7.1 Vlans

| VLAN           | NAME  | IP addresses     |
|----------------|:-----:|-----------------:|
| vmbr0          | WAN   | -                |
| vmbr1.10       | DMZ   | 192.168.10.0/24  |
| vmbr1.20       | HOST  | 192.168.20.0/24  |
| vmbr1.30       | VMs   | 192.168.30.0/24  |
| vmbr1.40       | LXCs  | 192.168.40.0/24  |
| vmbr1.50       | TEMP  | 192.168.50.0/24  |


### 7.2 VM IDs and IPs

| Description       | ID range                 |IP range                  |
|-------------------|:------------------------:|:------------------------:|
| WAN               | 100  -- 999              |                          |
| DMZ               | 1000 -- 1999             | 192.168.10.1 --> 254     |
| HOST              | 2000 -- 2999             | 192.168.20.1 --> 254     |
| VMs               | 3000 -- 3999             | 192.168.30.1 --> 254     |
| LXCs              | 4000 -- 4999             | 192.168.40.1 --> 254     |
| TEMP              | 5000 -- 5999             | 192.168.50.1 --> 254     |

### 7.3 Templates IDs and IPs

| Description       | ID range                 |IP range                  |
|-------------------|:------------------------:|:------------------------:|
| Templates:Alpine  | 5000 -- 5099             | 192.168.50.1  --> 9      |
| Templates:Ubuntu  | 5100 -- 5199             | 192.168.50.10 --> 19     |
| Templates:Debian  | 5200 -- 5299             | 192.168.50.20 --> 29     |
| Templates:Openwrt | 5300 -- 5399             | 192.168.50.30 --> 39     |
| Templates:Rocky   | 5400 -- 5499             | 192.168.50.40 --> 49     |