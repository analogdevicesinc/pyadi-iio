**Rx:**

./zcu\_setup.sh

./udc\_power\_on.sh



\#Run python initializatoin script: ADSY2301\_Init.py (for quad tile)



./adf4382\_init.sh

./rx\_tx\_config.sh rx\_0

./rx\_tx\_config.sh rx\_1

./rx\_tx\_config.sh rx\_2

./rx\_tx\_config.sh rx\_3

./set\_lo.sh 14.9

./set\_sw.sh 1 0 0

./set\_sw.sh 2 0 0

./set\_sw.sh 3 0 0

./set\_sw.sh 4 0 0

./admv8913\_filter.sh 6 13

systemctl restart iiod





**Tx:**

./zcu\_setup.sh

./udc\_power\_on.sh

./adf4382\_init.sh

./rx\_tx\_config.sh tx\_0

./rx\_tx\_config.sh tx\_1

./rx\_tx\_config.sh tx\_2

./rx\_tx\_config.sh tx\_3

./set\_lo.sh 14.9

./set\_sw.sh 1 0 1

./set\_sw.sh 2 0 1

./set\_sw.sh 3 0 1

./set\_sw.sh 4 0 1

./admv8913\_filter.sh 6 13

systemctl restart iiod



cd /sys/bus/iio/devices/iio:device3

echo 1 > out\_channel0\_enable 

echo 124999 > out\_channel0\_off\_raw 

echo 1 > out\_channel3\_enable 

echo 37500 > out\_channel3\_off\_raw 

echo 124999 > frame\_length\_raw 

echo 0 > burst\_count 

echo 1 > enable 

echo 1 > sync\_internal 

echo 1 > sync\_soft 



cd /sys/bus/iio/devices/iio:device4

echo 1 > reset

cd /sys/bus/iio/devices/iio:device5

echo 1 > reset

cd /sys/bus/iio/devices/iio:device6

echo 1 > reset

cd /sys/bus/iio/devices/iio:device7

echo 1 > reset



**Initialize through python here**



**PA\_ON**

cd /sys/bus/iio/devices/iio:device20

echo 1 > out\_voltage0\_raw

echo 1 > out\_voltage1\_raw

echo 1 > out\_voltage2\_raw

echo 1 > out\_voltage3\_raw



**Vdd\_PA**

cd /sys/bus/iio/devices/iio:device22

echo 1 >  out\_voltage7\_raw

