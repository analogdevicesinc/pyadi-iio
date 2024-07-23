import pytest
import json
import re
import numpy as np
import matplotlib.pyplot as plt
import base64

@pytest.fixture(scope="session")
def graph_fixture():
    # Load the JSON data from the file
    with open('test_triton_cal.json', 'r') as file:
        json_data = json.load(file)

    # Initialize string variables
    string_8GHz_adj = ""
    string_9GHz_adj = ""
    string_10GHz_adj = ""
    string_11GHz_adj = ""
    string_12GHz_adj = ""
    string_8GHz_comb = ""
    string_9GHz_comb = ""
    string_10GHz_comb = ""
    string_11GHz_comb = ""
    string_12GHz_comb = ""
    string_combined_tx = ""
    string_combined_rx = ""

    # Initialize iteration variables
    i = 0
    j = 1
    k = 2
    l = 3
    m = 4
    n = 5
    o = 6
    p = 7
    q = 8
    r = 9
    s = 160
    t = 166


    ## Extract Adjacent Loopback data at 8 GHz
    while i < 160:
        string = json_data['report']['tests'][i]['call']['stdout']
        string_8GHz_adj += string
        i = i+10

    ## Extract Adjacent Loopback data at 9 GHz
    while j < 160:
        string = json_data['report']['tests'][j]['call']['stdout']
        string_9GHz_adj += string
        j = j+10

    ## Extract Adjacent Loopback data at 10 GHz
    while k < 160:
        string = json_data['report']['tests'][k]['call']['stdout']
        string_10GHz_adj += string
        k = k+10

    ## Extract Adjacent Loopback data at 11 GHz
    while l < 160:
        string = json_data['report']['tests'][l]['call']['stdout']
        string_11GHz_adj += string
        l = l+10

    ## Extract Adjacent Loopback data at 12 GHz
    while m < 160:
        string = json_data['report']['tests'][m]['call']['stdout']
        string_12GHz_adj += string
        m = m+10

    ## Extract Combined Loopback data at 8 GHz
    while n < 160:
        string = json_data['report']['tests'][n]['call']['stdout']
        string_8GHz_comb += string
        n = n+10

    ## Extract Combined Loopback data at 9 GHz
    while o < 160:
        string = json_data['report']['tests'][o]['call']['stdout']
        string_9GHz_comb += string
        o = o+10

    ## Extract Combined Loopback data at 10 GHz
    while p < 160:
        string = json_data['report']['tests'][p]['call']['stdout']
        string_10GHz_comb += string
        p = p+10

    ## Extract Combined Loopback data at 11 GHz
    while q < 160:
        string = json_data['report']['tests'][q]['call']['stdout']
        string_11GHz_comb += string
        q = q+10

    ## Extract Combined Loopback data at 12 GHz
    while r < 160:
        string = json_data['report']['tests'][r]['call']['stdout']
        string_12GHz_comb += string
        r = r+10

    # # Extract Tx Combined Out SMA data from 8-12 GHz
    # while s >= 160 and s <= 165:
    #     string = json_data['report']['tests'][s]['call']['stdout']
    #     string_combined_tx += string
    #     s = s+1

    # # Extract Rx Combined In SMA data from 8-12 GHz
    # while t >= 166 and t <= 170:
    #     string = json_data['report']['tests'][t]['call']['stdout']
    #     string_combined_rx += string
    #     t = t+1

    ## Pattern to find scientific notation
    pattern = r'[-+]?\d*\.\d+E[-+]?\d+'

    # Use regular expression module to find matching pattern
    adj_8GHz = re.findall(pattern, string_8GHz_adj)
    adj_9GHz = re.findall(pattern, string_9GHz_adj)
    adj_10GHz = re.findall(pattern, string_10GHz_adj)
    adj_11GHz = re.findall(pattern, string_11GHz_adj)
    adj_12GHz = re.findall(pattern, string_12GHz_adj)
    comb_8GHz = re.findall(pattern, string_8GHz_comb)
    comb_9GHz = re.findall(pattern, string_9GHz_comb)
    comb_10GHz = re.findall(pattern, string_10GHz_comb)
    comb_11GHz = re.findall(pattern, string_11GHz_comb)
    comb_12GHz = re.findall(pattern, string_12GHz_comb)
    comb_tx = re.findall(pattern, string_combined_tx)
    comb_rx = re.findall(pattern, string_combined_rx)

    # Convert scientific notation strings to floating-point 
    adj_8GHz_array = [float(num) for num in adj_8GHz]
    adj_9GHz_array = [float(num) for num in adj_9GHz]
    adj_10GHz_array = [float(num) for num in adj_10GHz]
    adj_11GHz_array = [float(num) for num in adj_11GHz]
    adj_12GHz_array = [float(num) for num in adj_12GHz]
    comb_8GHz_array = [float(num) for num in comb_8GHz]
    comb_9GHz_array = [float(num) for num in comb_9GHz]
    comb_10GHz_array = [float(num) for num in comb_10GHz]
    comb_11GHz_array = [float(num) for num in comb_11GHz]
    comb_12GHz_array = [float(num) for num in comb_12GHz]
    comb_tx_array = [float(num) for num in comb_tx]
    comb_rx_array = [float(num) for num in comb_rx]

    print(adj_8GHz_array)
    print(adj_9GHz_array)
    print(adj_10GHz_array)
    print(adj_11GHz_array)
    print(adj_12GHz_array)
    print(comb_8GHz_array)
    print(comb_9GHz_array)
    print(comb_10GHz_array)
    print(comb_11GHz_array)
    print(comb_12GHz_array)
    print(comb_tx_array)
    print(comb_rx_array)

    ## 1x16 channels array 0:15
    channels_array = np.arange(16)

    ## 1x5 frequency array
    frequency_array = [8000, 9000, 10000, 11000, 12000]

    ## 1x5 channel results array for each channel in adjacent loopback state
    ch0_adjresults_y = [adj_8GHz_array[0], adj_9GHz_array[0], adj_10GHz_array[0], adj_11GHz_array[0], adj_12GHz_array[0]]
    ch1_adjresults_y = [adj_8GHz_array[1], adj_9GHz_array[1], adj_10GHz_array[1], adj_11GHz_array[1], adj_12GHz_array[1]]
    ch2_adjresults_y = [adj_8GHz_array[2], adj_9GHz_array[2], adj_10GHz_array[2], adj_11GHz_array[2], adj_12GHz_array[2]]
    ch3_adjresults_y = [adj_8GHz_array[3], adj_9GHz_array[3], adj_10GHz_array[3], adj_11GHz_array[3], adj_12GHz_array[3]]
    ch4_adjresults_y = [adj_8GHz_array[4], adj_9GHz_array[4], adj_10GHz_array[4], adj_11GHz_array[4], adj_12GHz_array[4]]
    ch5_adjresults_y = [adj_8GHz_array[5], adj_9GHz_array[5], adj_10GHz_array[5], adj_11GHz_array[5], adj_12GHz_array[5]]
    ch6_adjresults_y = [adj_8GHz_array[6], adj_9GHz_array[6], adj_10GHz_array[6], adj_11GHz_array[6], adj_12GHz_array[6]]
    ch7_adjresults_y = [adj_8GHz_array[7], adj_9GHz_array[7], adj_10GHz_array[7], adj_11GHz_array[7], adj_12GHz_array[7]]
    ch8_adjresults_y = [adj_8GHz_array[8], adj_9GHz_array[8], adj_10GHz_array[8], adj_11GHz_array[8], adj_12GHz_array[8]]
    ch9_adjresults_y = [adj_8GHz_array[9], adj_9GHz_array[9], adj_10GHz_array[9], adj_11GHz_array[9], adj_12GHz_array[9]]
    ch10_adjresults_y = [adj_8GHz_array[10], adj_9GHz_array[10], adj_10GHz_array[10], adj_11GHz_array[10], adj_12GHz_array[10]]
    ch11_adjresults_y = [adj_8GHz_array[11], adj_9GHz_array[11], adj_10GHz_array[11], adj_11GHz_array[11], adj_12GHz_array[11]]
    ch12_adjresults_y = [adj_8GHz_array[12], adj_9GHz_array[12], adj_10GHz_array[12], adj_11GHz_array[12], adj_12GHz_array[12]]
    ch13_adjresults_y = [adj_8GHz_array[13], adj_9GHz_array[13], adj_10GHz_array[13], adj_11GHz_array[13], adj_12GHz_array[13]]
    ch14_adjresults_y = [adj_8GHz_array[14], adj_9GHz_array[14], adj_10GHz_array[14], adj_11GHz_array[14], adj_12GHz_array[14]]
    ch15_adjresults_y = [adj_8GHz_array[15], adj_9GHz_array[15], adj_10GHz_array[15], adj_11GHz_array[15], adj_12GHz_array[15]]

    ## 1x5 channel results array for each channel in combined loopback state
    ch0_combresults_y = [comb_8GHz_array[0], comb_9GHz_array[0], comb_10GHz_array[0], comb_11GHz_array[0], comb_12GHz_array[0]]
    ch1_combresults_y = [comb_8GHz_array[1], comb_9GHz_array[1], comb_10GHz_array[1], comb_11GHz_array[1], comb_12GHz_array[1]]
    ch2_combresults_y = [comb_8GHz_array[2], comb_9GHz_array[2], comb_10GHz_array[2], comb_11GHz_array[2], comb_12GHz_array[2]]
    ch3_combresults_y = [comb_8GHz_array[3], comb_9GHz_array[3], comb_10GHz_array[3], comb_11GHz_array[3], comb_12GHz_array[3]]
    ch4_combresults_y = [comb_8GHz_array[4], comb_9GHz_array[4], comb_10GHz_array[4], comb_11GHz_array[4], comb_12GHz_array[4]]
    ch5_combresults_y = [comb_8GHz_array[5], comb_9GHz_array[5], comb_10GHz_array[5], comb_11GHz_array[5], comb_12GHz_array[5]]
    ch6_combresults_y = [comb_8GHz_array[6], comb_9GHz_array[6], comb_10GHz_array[6], comb_11GHz_array[6], comb_12GHz_array[6]]
    ch7_combresults_y = [comb_8GHz_array[7], comb_9GHz_array[7], comb_10GHz_array[7], comb_11GHz_array[7], comb_12GHz_array[7]]
    ch8_combresults_y = [comb_8GHz_array[8], comb_9GHz_array[8], comb_10GHz_array[8], comb_11GHz_array[8], comb_12GHz_array[8]]
    ch9_combresults_y = [comb_8GHz_array[9], comb_9GHz_array[9], comb_10GHz_array[9], comb_11GHz_array[9], comb_12GHz_array[9]]
    ch10_combresults_y = [comb_8GHz_array[10], comb_9GHz_array[10], comb_10GHz_array[10], comb_11GHz_array[10], comb_12GHz_array[10]]
    ch11_combresults_y = [comb_8GHz_array[11], comb_9GHz_array[11], comb_10GHz_array[11], comb_11GHz_array[11], comb_12GHz_array[11]]
    ch12_combresults_y = [comb_8GHz_array[12], comb_9GHz_array[12], comb_10GHz_array[12], comb_11GHz_array[12], comb_12GHz_array[12]]
    ch13_combresults_y = [comb_8GHz_array[13], comb_9GHz_array[13], comb_10GHz_array[13], comb_11GHz_array[13], comb_12GHz_array[13]]
    ch14_combresults_y = [comb_8GHz_array[14], comb_9GHz_array[14], comb_10GHz_array[14], comb_11GHz_array[14], comb_12GHz_array[14]]
    ch15_combresults_y = [comb_8GHz_array[15], comb_9GHz_array[15], comb_10GHz_array[15], comb_11GHz_array[15], comb_12GHz_array[15]]

    # Create a new plot with adjacent loopback data
    plt.figure() 
    plt.plot(frequency_array, ch0_adjresults_y, label='Channel 0')
    plt.plot(frequency_array, ch1_adjresults_y, label='Channel 1')
    plt.plot(frequency_array, ch2_adjresults_y, label='Channel 2')
    plt.plot(frequency_array, ch3_adjresults_y, label='Channel 3')
    plt.plot(frequency_array, ch4_adjresults_y, label='Channel 4')
    plt.plot(frequency_array, ch5_adjresults_y, label='Channel 5')
    plt.plot(frequency_array, ch6_adjresults_y, label='Channel 6')
    plt.plot(frequency_array, ch7_adjresults_y, label='Channel 7')
    plt.plot(frequency_array, ch8_adjresults_y, label='Channel 8')
    plt.plot(frequency_array, ch9_adjresults_y, label='Channel 9')
    plt.plot(frequency_array, ch10_adjresults_y, label='Channel 10')
    plt.plot(frequency_array, ch11_adjresults_y, label='Channel 11')
    plt.plot(frequency_array, ch12_adjresults_y, label='Channel 12')
    plt.plot(frequency_array, ch13_adjresults_y, label='Channel 13')
    plt.plot(frequency_array, ch14_adjresults_y, label='Channel 14')
    plt.plot(frequency_array, ch15_adjresults_y, label='Channel 15')

    # Limits for y axis
    plt.ylim(-70, 0)  

    # Add labels and title
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Magnitude (dBm)')
    plt.title('Adjacent Loopback State (+15 dBm Input)')

    # # Add legend
    # plt.legend()

    plt.savefig('adjacent.png')




    # Create a new plot with adjacent loopback data
    plt.figure() 
    plt.plot(frequency_array, ch0_combresults_y, label='Channel 0')
    plt.plot(frequency_array, ch1_combresults_y, label='Channel 1')
    plt.plot(frequency_array, ch2_combresults_y, label='Channel 2')
    plt.plot(frequency_array, ch3_combresults_y, label='Channel 3')
    plt.plot(frequency_array, ch4_combresults_y, label='Channel 4')
    plt.plot(frequency_array, ch5_combresults_y, label='Channel 5')
    plt.plot(frequency_array, ch6_combresults_y, label='Channel 6')
    plt.plot(frequency_array, ch7_combresults_y, label='Channel 7')
    plt.plot(frequency_array, ch8_combresults_y, label='Channel 8')
    plt.plot(frequency_array, ch9_combresults_y, label='Channel 9')
    plt.plot(frequency_array, ch10_combresults_y, label='Channel 10')
    plt.plot(frequency_array, ch11_combresults_y, label='Channel 11')
    plt.plot(frequency_array, ch12_combresults_y, label='Channel 12')
    plt.plot(frequency_array, ch13_combresults_y, label='Channel 13')
    plt.plot(frequency_array, ch14_combresults_y, label='Channel 14')
    plt.plot(frequency_array, ch15_combresults_y, label='Channel 15')

    # Limits for y axis
    plt.ylim(-80, 0)  

    # Add labels and title
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Magnitude (dBm)')
    plt.title('Combined Loopback State (+15 dBm Input)')

    # # Add legend
    # plt.legend()

## 1x5 channel results array for each channel in combined loopback state
ch0_combresults_y = [comb_8GHz_array[0], comb_9GHz_array[0], comb_10GHz_array[0], comb_11GHz_array[0], comb_12GHz_array[0]]
ch1_combresults_y = [comb_8GHz_array[1], comb_9GHz_array[1], comb_10GHz_array[1], comb_11GHz_array[1], comb_12GHz_array[1]]
ch2_combresults_y = [comb_8GHz_array[2], comb_9GHz_array[2], comb_10GHz_array[2], comb_11GHz_array[2], comb_12GHz_array[2]]
ch3_combresults_y = [comb_8GHz_array[3], comb_9GHz_array[3], comb_10GHz_array[3], comb_11GHz_array[3], comb_12GHz_array[3]]
ch4_combresults_y = [comb_8GHz_array[4], comb_9GHz_array[4], comb_10GHz_array[4], comb_11GHz_array[4], comb_12GHz_array[4]]
ch5_combresults_y = [comb_8GHz_array[5], comb_9GHz_array[5], comb_10GHz_array[5], comb_11GHz_array[5], comb_12GHz_array[5]]
ch6_combresults_y = [comb_8GHz_array[6], comb_9GHz_array[6], comb_10GHz_array[6], comb_11GHz_array[6], comb_12GHz_array[6]]
ch7_combresults_y = [comb_8GHz_array[7], comb_9GHz_array[7], comb_10GHz_array[7], comb_11GHz_array[7], comb_12GHz_array[7]]
ch8_combresults_y = [comb_8GHz_array[8], comb_9GHz_array[8], comb_10GHz_array[8], comb_11GHz_array[8], comb_12GHz_array[8]]
ch9_combresults_y = [comb_8GHz_array[9], comb_9GHz_array[9], comb_10GHz_array[9], comb_11GHz_array[9], comb_12GHz_array[9]]
ch10_combresults_y = [comb_8GHz_array[10], comb_9GHz_array[10], comb_10GHz_array[10], comb_11GHz_array[10], comb_12GHz_array[10]]
ch11_combresults_y = [comb_8GHz_array[11], comb_9GHz_array[11], comb_10GHz_array[11], comb_11GHz_array[11], comb_12GHz_array[11]]
ch12_combresults_y = [comb_8GHz_array[12], comb_9GHz_array[12], comb_10GHz_array[12], comb_11GHz_array[12], comb_12GHz_array[12]]
ch13_combresults_y = [comb_8GHz_array[13], comb_9GHz_array[13], comb_10GHz_array[13], comb_11GHz_array[13], comb_12GHz_array[13]]
ch14_combresults_y = [comb_8GHz_array[14], comb_9GHz_array[14], comb_10GHz_array[14], comb_11GHz_array[14], comb_12GHz_array[14]]
ch15_combresults_y = [comb_8GHz_array[15], comb_9GHz_array[15], comb_10GHz_array[15], comb_11GHz_array[15], comb_12GHz_array[15]]

# Create a new plot with adjacent loopback data
plt.figure() 
plt.plot(frequency_array, ch0_adjresults_y, label='Channel 0')
plt.plot(frequency_array, ch1_adjresults_y, label='Channel 1')
plt.plot(frequency_array, ch2_adjresults_y, label='Channel 2')
plt.plot(frequency_array, ch3_adjresults_y, label='Channel 3')
plt.plot(frequency_array, ch4_adjresults_y, label='Channel 4')
plt.plot(frequency_array, ch5_adjresults_y, label='Channel 5')
plt.plot(frequency_array, ch6_adjresults_y, label='Channel 6')
plt.plot(frequency_array, ch7_adjresults_y, label='Channel 7')
plt.plot(frequency_array, ch8_adjresults_y, label='Channel 8')
plt.plot(frequency_array, ch9_adjresults_y, label='Channel 9')
plt.plot(frequency_array, ch10_adjresults_y, label='Channel 10')
plt.plot(frequency_array, ch11_adjresults_y, label='Channel 11')
plt.plot(frequency_array, ch12_adjresults_y, label='Channel 12')
plt.plot(frequency_array, ch13_adjresults_y, label='Channel 13')
plt.plot(frequency_array, ch14_adjresults_y, label='Channel 14')
plt.plot(frequency_array, ch15_adjresults_y, label='Channel 15')

# Limits for y axis
plt.ylim(-80, 0)  

# Add labels and title
plt.xlabel('Frequency (MHz)')
plt.ylabel('Magnitude (dBm)')
plt.title('Calibration Board Output Magnitude vs Frequency for Adjacent Loopback State (+15 dBm Input)')

# # Add legend
# plt.legend()
plt.savefig('adjacent_loopback_by_channel.png')

# Create a new plot with adjacent loopback data
plt.figure() 
plt.plot(frequency_array, ch0_combresults_y, label='Channel 0')
plt.plot(frequency_array, ch1_combresults_y, label='Channel 1')
plt.plot(frequency_array, ch2_combresults_y, label='Channel 2')
plt.plot(frequency_array, ch3_combresults_y, label='Channel 3')
plt.plot(frequency_array, ch4_combresults_y, label='Channel 4')
plt.plot(frequency_array, ch5_combresults_y, label='Channel 5')
plt.plot(frequency_array, ch6_combresults_y, label='Channel 6')
plt.plot(frequency_array, ch7_combresults_y, label='Channel 7')
plt.plot(frequency_array, ch8_combresults_y, label='Channel 8')
plt.plot(frequency_array, ch9_combresults_y, label='Channel 9')
plt.plot(frequency_array, ch10_combresults_y, label='Channel 10')
plt.plot(frequency_array, ch11_combresults_y, label='Channel 11')
plt.plot(frequency_array, ch12_combresults_y, label='Channel 12')
plt.plot(frequency_array, ch13_combresults_y, label='Channel 13')
plt.plot(frequency_array, ch14_combresults_y, label='Channel 14')
plt.plot(frequency_array, ch15_combresults_y, label='Channel 15')

# Limits for y axis
plt.ylim(-80, 0)  

# Add labels and title
plt.xlabel('Frequency (MHz)')
plt.ylabel('Magnitude (dBm)')
plt.title('Calibration Board Output Magnitude vs Frequency for Combined Loopback State (+15 dBm Input)')

# # Add legend
# plt.legend()

plt.savefig('combined_loopback_by_channel.png')
# Show the plots
plt.show()

