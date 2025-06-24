import time
import importlib
from calibration import *

import genalyzer as gn
import adi
from adi.sshfs import sshfs
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import adar_functions
import re
import json
import os

url = "ip:192.168.0.1" 


sray = adi.adar1000_array(
    uri = url,

    chip_ids = ["adar1000_csb_0_2_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
                "adar1000_csb_0_1_4", "adar1000_csb_0_1_3", "adar1000_csb_0_1_2", "adar1000_csb_0_1_1",
                "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
                "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
   
    device_map = [[1, 5, 2, 6], [3, 7, 4, 8],[9, 13, 10, 14], [11, 15, 12, 16]],

    element_map = np.array([[1, 9,  17, 25, 33, 41, 49, 57],
                            [2, 10, 18, 26, 34, 42, 50, 58],
                            [3, 11, 19, 27, 35, 43, 51, 59],
                            [4, 12, 20, 28, 36, 44, 52, 60],

                            [5, 13, 21, 29, 37, 45, 53, 61],
                            [6, 14, 22, 30, 38, 46, 54, 62],
                            [7, 15, 23, 31, 39, 47, 55, 63],
                            [8, 16, 24, 32, 40, 48, 56, 64]]),
    
    device_element_map = {

        1:  [9, 1, 2, 10],      3:  [25, 17, 18, 26],
        2:  [11, 3, 4, 12],     4:  [27, 19, 20, 28],
        5:  [41, 33, 34, 42],   7:  [57, 49, 50, 58],
        6:  [43, 35, 36, 44],   8:  [59, 51, 52, 60],
        
        9:  [6, 14, 13, 5],     11: [22, 30, 29, 21],
        10: [8, 16, 15, 7],     12: [24, 32, 31, 23],
        13: [38, 46, 45, 37],   15: [54, 62, 61, 53],
        14: [40, 48, 47, 39],   16: [56, 64, 63, 55],
    },
)

# enable_stingray_channel(sray, elements=list(range(1,65)), man_input=False)
disable_stingray_channel(sray, elements=list(range(1,65)), man_input=False)

# # print(list(range(57,65)))
# enable_stingray_channel(sray, elements=list(range(12,17)), man_input=False)
enable_stingray_channel(sray, elements=None, man_input=True)
# sray = adi.adar1000_array(
#     uri = url,


#         #Iteration 1
#         # chip_ids = ["adar1000_csb_0_1_1", "adar1000_csb_0_1_2", "adar1000_csb_0_1_3", "adar1000_csb_0_1_4",
#         #         "adar1000_csb_0_2_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",

#         #         "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
#         #         "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

#         #Iteration 2
#         chip_ids = ["adar1000_csb_0_2_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
#                 "adar1000_csb_0_1_4", "adar1000_csb_0_1_3", "adar1
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############################################################################000_csb_0_1_2", "adar1000_csb_0_1_1",
#                 "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
#                 "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],
   
#     device_map = [[1, 5, 2, 6], [3, 7, 4, 8],[9, 13, 10, 14], [11, 15, 12, 16]],

#     element_map = np.array([[1, 9,  17, 25, 33, 41, 49, 57],
#                             [2, 10, 18, 26, 34, 42, 50, 58],
#                             [3, 11, 19, 27, 35, 43, 51, 59],
#                             [4, 12, 20, 28, 36, 44, 52, 60],

#                             [5, 13, 21, 29, 37, 45, 53, 61],
#                             [6, 14, 22, 30, 38, 46, 54, 62],
#                             [7, 15, 23, 31, 39, 47, 55, 63],
#                             [8, 16, 24, 32, 40, 48, 56, 64]]),
    
#     device_element_map = {
#     #     # Iteration 1
#     #     1: [2, 10, 9, 1],
#     #     2: [4, 12, 11, 3],
#     #     3: [6, 14, 13, 5],
#     #     4: [8, 16, 15, 7],
#     #     5: [18, 26, 25, 17],
#     #     6: [20, 28, 27, 19],
#     #     7: [22, 30, 29, 21],
#     #     8: [24, 32, 31, 23],
#     #     9:  [34, 42, 41, 33],
#     #     10: [36, 44, 43, 35],
#     #     11: [38, 46, 45, 37],
#     #     12: [40, 48, 47, 39],
#     #     13: [50, 58, 57, 49],
#     #     14: [52, 60, 59, 51],
#     #     15: [54, 62, 61, 53],
#     #     16: [56, 64, 63, 55],

#         #     # Iteration 2
#         # 1: [9, 1, 2, 10], #CLEAR
#         # 2: [11, 3, 4, 12],#CLEAR

#         # 3: [6, 14, 13, 5], #FAIL
#         # 4: [8, 16, 15, 7], StingRay+MantaRay July Dem

#         # 5: [25, 17, 18, 26],
#         # 6: [27, 19, 20, 28],

#         # 7: [22, 30, 29, 21],
#         # 8: [24, 32, 31, 23],

#         # 9:  [41, 33, 34, 42],
#         # 10: [43, 35, 36, 44],

#         # 11: [38, 46, 45, 37],
#         # 12: [40, 48, 47, 39],

#         # 13: [57, 49, 50, 58],
#         # 14: [59, 51, 52, 60],

#         # 15: [54, 62, 61, 53],
#         # 16: [56, 64, 63, 55],

#         # Iteration 3
#         1: [9, 1, 2, 10], #CLEAR
#         2: [11, 3, 4, 12],#CLEAR

#         9: [6, 14, 13, 5], #FAIL
#         10: [8, 16, 15, 7], 

#         3: [25, 17, 18, 26],
#         4: [27, 19, 20, 28],

#         11: [22, 30, 29, 21],
#         12: [24, 32, 31, 23],

#         5:  [41, 33, 34, 42],
#         6: [43, 35, 36, 44],

#         13: [38, 46, 45, 37],
#         14: [40, 48, 47, 39],

#         7: [57, 49, 50, 58],
#         8: [59, 51, 52, 60],

#         15: [54, 62, 61, 53],
#         16: [56, 64, 63, 55],
#     },

    
# )
