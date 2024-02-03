echo "Shutdown for the VM with ID "$1
ps aux | grep "/usr/bin/kvm -id "$1 | awk '{print $2}' | head --line=1 | xargs kill -9
echo "Done."