rm $(find source/devices/ -name "adi.*" ! -name "adi.ad9081_mc.rst")
rm source/devices/modules.rst
sphinx-apidoc -T -e -o source/devices ../adi

# Remove adi. and modules strings
find source/devices -mindepth 1 -type f -exec sed -i '1 s/adi\.//g' {} \;
find source/devices -mindepth 1 -type f -exec sed -i 's/\ module//g' {} \;

# Remove classes we shouldn't document
list="obs attribute context_manager dds rx_tx sshfs"
skips=""
for val in $list; do
    echo $val
    sed -i "/$val/d" source/devices/adi.rst
    if ! $(echo $skips | grep -w -q $val) ;then
    	rm source/devices/adi.${val}.rst
    fi
done

# Remove extra text
sed -i '/Module.*/q' source/devices/adi.rst
sed -i '/Module/d' source/devices/adi.rst

sed -i 's/adi\ package/Supported\ Devices/' source/devices/adi.rst
sed -i 's/Submodules//' source/devices/adi.rst
sed -i 's/----------//' source/devices/adi.rst
sed -i 's/===========/=================/' source/devices/adi.rst
mv source/devices/adi.rst source/devices/index.rst

make html
