from distutils.log import error
from mimetypes import init
from statistics import harmonic_mean
import numpy as np
import matplotlib.pyplot as plt

def print_cal_plots(primary_angles, angle_error, error_mag, corrected_angle_error, corrected_error_mag):
    fig = plt.figure()
    plt.subplots_adjust(hspace=1)  # Adjust the vertical space between subplots
    plt.subplot(5, 1, 1)
    plt.plot(primary_angles, label='Primary Angles')
    plt.title('Primary Angles Captured')
    plt.xlabel('Sample')
    plt.ylabel('Angle (degrees)')
    plt.xlim(0, len(primary_angles))
    # plt.legend()
    
    plt.subplot(5, 1, 2)
    plt.plot(angle_error, label='Angle Error', color='orange')
    plt.title('Angle Error')
    plt.xlabel('Sample')
    plt.ylabel('Error (degrees)')
    plt.xlim(0, len(angle_error))
    #plt.ylim(np.min(angle_error) * 1.5, np.max(angle_error) * 1.5)  # Set limits to fit peaks
    # plt.legend()

    plt.subplot(5, 1, 3)
    plt.semilogy(error_mag)
    plt.title('FFT Angle Error')
    plt.xlabel('Bin')
    plt.ylabel('Magnitude')
    plt.xlim(0, len(error_mag))
    plt.annotate('H1 (11, ' + str(round(error_mag[11], 4)) + ')', xy=(11, error_mag[11]), xytext=(0, 1.1), textcoords='axes fraction', arrowprops=dict(facecolor='black', width=1, headwidth=3), fontsize=8, color='red')
    plt.annotate('H2 (22, ' + str(round(error_mag[22], 4)) + ')', xy=(22, error_mag[22]), xytext=(0.2, 1.1), textcoords='axes fraction', arrowprops=dict(facecolor='black', width=1, headwidth=3), fontsize=8, color='red')
    #plt.ylim(np.min(error_mag) * 1.5, np.max(error_mag) * 1.5)  # Set limits to fit peaks
    # plt.ylim(10e-4, 10e0)  # Adjust the limits as necessary
    # plt.legend()

    plt.subplot(5, 1, 4)
    plt.plot(corrected_angle_error, label='Corrected Error', color='orange')
    plt.title('Corrected Error')
    plt.xlabel('Sample')
    plt.ylabel('Error (degrees)')
    plt.xlim(0, len(corrected_angle_error))
    #plt.ylim(np.min(corrected_angle_error) * 1.5, np.max(corrected_angle_error) * 1.5)
    # plt.legend()

    plt.subplot(5, 1, 5)
    plt.semilogy(corrected_error_mag)
    plt.title('Corrected FFT Angle Error')
    plt.xlabel('Bin')
    plt.ylabel('Magnitude')
    plt.xlim(0, len(corrected_error_mag))
    #plt.ylim(np.min(corrected_error_mag) * 1.5, np.max(corrected_error_mag) * 1.5)

    #plt.legend()

    plt.show()

def calculate_angle_error(angles):
    # convert and scale the angle in radians
    # in Rad - specific for MT4000 part
    angle_scale_factor_rad = 2*np.pi / (2^16)
    angle_raw = angles * angle_scale_factor_rad

    angles = np.unwrap(angle_raw)

    angles = angles - angles[0]

    angles_fit = np.polyfit(np.arange(len(angles)), angles, 1)
    alin_angle = angles_fit[0]* np.arange(len(angles))
    angle_error = angles - alin_angle

    angle_error_offset = (max(angle_error) + min(angle_error)) / 2
    angle_error = angle_error - angle_error_offset
    angle_error = angle_error * 180 / np.pi

    max_error = max(abs(angle_error))

    return angle_error, max_error

def calculate_corrections(angle_error, harmonic_error, ref_angles):
    hx_correction = 0
    for index in harmonic_error.keys():
        hx_correction = hx_correction + harmonic_error[index]["magnitude"] * np.sin(index * np.radians(ref_angles) + np.radians(harmonic_error[index]["phase"]))

    corrected_angle_error = angle_error - hx_correction
    angle_error_len = len(angle_error)
    corrected_error_fft = np.fft.fft(angle_error - hx_correction) / (angle_error_len / 2)
    corrected_error_mag = np.abs(corrected_error_fft[:angle_error_len // 2])

    return corrected_angle_error, corrected_error_mag

def admt4000_calibration(primary_angles, ref_angles, cycles = 11, circulat_shift = 0, CCW = 0):
    if CCW == 1:
        primary_angles = primary_angles[::-1]
        ref_angles = ref_angles[::-1]
    
    if circulat_shift == 1:
        shift_index = np.random.randint(0, len(primary_angles))
        primary_angles = np.roll(primary_angles, shift_index)
        ref_angles = np.roll(ref_angles, shift_index)

    resolution = 360 / (2^16)
    angle_error, _ = calculate_angle_error(primary_angles / resolution)

    angle_error_len = len(angle_error)
    error_fft = np.fft.fft(angle_error) / angle_error_len
    error_mag = 2 * np.abs(error_fft[:angle_error_len // 2])
    error_phase = np.angle(error_fft)

    harmonic_errors = {
        1: {"magnitude": 0, "phase": 0},
        2: {"magnitude": 0, "phase": 0},
        3: {"magnitude": 0, "phase": 0},
        8: {"magnitude": 0, "phase": 0}
    }

    scaled_harmonic_errors = {
        1: {"magnitude": 0, "phase": 0},
        2: {"magnitude": 0, "phase": 0},
        3: {"magnitude": 0, "phase": 0},
        8: {"magnitude": 0, "phase": 0}
    }

    init_error = 0
    for index in harmonic_errors.keys():
        harmonic_errors[index]["magnitude"] = error_mag[index * cycles]
        hx_phase = np.degrees(error_phase[index * cycles])
        harmonic_errors[index]["phase"] = hx_phase
        
        init_error = init_error + harmonic_errors[index]["magnitude"] * np.cos(np.radians(hx_phase))

    init_angle = primary_angles[0] - init_error

    rot_dir = 1
    if CCW == 1:
        rot_dir = -1

    for index in harmonic_errors.keys():
        harmonic_errors[index]["phase"] = (rot_dir * harmonic_errors[index]["phase"] - (index * init_angle - 90)) % 360

    # scaling for ADMT4000
    mag_scale = 0.6072
    mag_resolution = 360 / (2**16)  # ADMT4000 resolution in degrees
    phase_resolution = 0.0878

    for index in harmonic_errors.keys():
        scaled_harmonic_errors[index]["magnitude"] = round(harmonic_errors[index]["magnitude"] * mag_scale / mag_resolution)
        scaled_harmonic_errors[index]["phase"] = round(harmonic_errors[index]["phase"] / phase_resolution)
    
    return scaled_harmonic_errors, harmonic_errors, angle_error, error_mag

if __name__ == "__main__":
    # Example usage
    
    primary_angles = np.array([359.63745,15.07874,30.58594,46.01624,61.47400,76.99768,92.34009,107.70447,123.34900,138.72437,154.34143,170.01343,185.48767,201.18713,216.79871,232.11914,247.71973,263.23792,278.42102,293.72498,309.33655,324.54712,339.94446,355.48462,10.73914,26.35071,41.88538,57.21680,72.88879,88.13782,103.47473,119.14673,134.59351,150.05127,165.71228,181.30737,196.93542,212.56897,227.94434,243.44604,258.96423,274.24072,289.58313,305.09583,320.32288,335.84656,351.24939,6.58630,22.07703,37.62268,52.91565,68.49976,83.89709,99.21204,114.76318,130.31982,145.79407,161.44958,177.09412,192.55188,208.35022,223.79700,239.19983,254.85535,270.13733,285.38635,300.89355,316.15906,331.50696,347.02515,2.42798,17.87476,33.43140,48.74084,64.24255,79.81567,94.95483,110.57190,126.13953,141.54785,157.26379,172.88635,188.28369,203.92273,219.68811,234.96460,250.49927,265.98999,281.14014,296.70227,312.06665,327.30469,342.90527,358.22021,13.58459,29.21265,44.60449,60.02380,75.54199,90.94482,106.25427,121.92627,137.36755,152.94617,168.53027,184.07593,199.72046,215.37598,230.77881,246.39587,261.82617,276.98181,292.40112,307.88635,323.08594,338.59863,354.14429,9.33838,24.92798,40.48462,55.75012,71.32324,86.75903,102.06299,117.68005,133.15430,148.66699,164.39392,179.81873,195.41931,211.17371,226.63147,242.13318,257.67883,272.84546,288.28125,303.70056,318.93860,334.36890,349.85962,5.19653,20.70923,36.22192,51.55884,67.10999,82.65015,97.86072,113.31848,129.00696,144.29443,159.98291,175.66589,191.18408,206.85608,222.40173,237.85950,253.39417,268.75305,284.03503,299.59167,314.77478,330.09521,345.66833,1.06018,16.46301,31.95374,47.34009,62.92969,78.42041,93.69690,109.16016,124.76074,140.16907,155.70923,171.43616,186.81152,202.52197,218.22144,233.55835,249.13147,264.63318,279.78333,295.20264,310.75378,325.93140,341.40564,356.81396,12.17834,27.77893,43.20923,58.57361,74.18518,89.56604,104.81506,120.51453,135.94482,151.61682,167.20642,182.71912,198.30872,213.99170,229.39453,244.94019,260.47485,275.66895,291.08826,306.51855,321.68518,337.19238,352.70508,7.90466,23.44482,39.16077,54.36584,69.88403,85.37476,100.56885,116.27930,131.81396,147.28821,162.90527,178.43445,194.03503,209.64661,225.16479,240.71045,256.25610,271.50513,286.85303,302.28882,317.49390,332.92969,348.51929,3.82324,19.25903,34.85962,50.18005,65.68176,81.22192,96.47644,111.91223,127.55127,142.83325,158.55469,174.27063,189.68445,205.41138,221.04492,236.39282,252.07581,267.42920,282.57935,298.09753,313.40698,328.69446,344.27307])
    ref_angles = np.array([0.00000,15.46875,30.93750,46.40625,61.87500,77.34375,92.81250,108.28125,123.75000,139.21875,154.68750,170.15625,185.62500,201.09375,216.56250,232.03125,247.50000,262.96875,278.43750,293.90625,309.37500,324.84375,340.31250,355.78125,11.25000,26.71875,42.18750,57.65625,73.12500,88.59375,104.06250,119.53125,135.00000,150.46875,165.93750,181.40625,196.87500,212.34375,227.81250,243.28125,258.75000,274.21875,289.68750,305.15625,320.62500,336.09375,351.56250,7.03125,22.50000,37.96875,53.43750,68.90625,84.37500,99.84375,115.31250,130.78125,146.25000,161.71875,177.18750,192.65625,208.12500,223.59375,239.06250,254.53125,270.00000,285.46875,300.93750,316.40625,331.87500,347.34375,2.81250,18.28125,33.75000,49.21875,64.68750,80.15625,95.62500,111.09375,126.56250,142.03125,157.50000,172.96875,188.43750,203.90625,219.37500,234.84375,250.31250,265.78125,281.25000,296.71875,312.18750,327.65625,343.12500,358.59375,14.06250,29.53125,45.00000,60.46875,75.93750,91.40625,106.87500,122.34375,137.81250,153.28125,168.75000,184.21875,199.68750,215.15625,230.62500,246.09375,261.56250,277.03125,292.50000,307.96875,323.43750,338.90625,354.37500,9.84375,25.31250,40.78125,56.25000,71.71875,87.18750,102.65625,118.12500,133.59375,149.06250,164.53125,180.00000,195.46875,210.93750,226.40625,241.87500,257.34375,272.81250,288.28125,303.75000,319.21875,334.68750,350.15625,5.62500,21.09375,36.56250,52.03125,67.50000,82.96875,98.43750,113.90625,129.37500,144.84375,160.31250,175.78125,191.25000,206.71875,222.18750,237.65625,253.12500,268.59375,284.06250,299.53125,315.00000,330.46875,345.93750,1.40625,16.87500,32.34375,47.81250,63.28125,78.75000,94.21875,109.68750,125.15625,140.62500,156.09375,171.56250,187.03125,202.50000,217.96875,233.43750,248.90625,264.37500,279.84375,295.31250,310.78125,326.25000,341.71875,357.18750,12.65625,28.12500,43.59375,59.06250,74.53125,90.00000,105.46875,120.93750,136.40625,151.87500,167.34375,182.81250,198.28125,213.75000,229.21875,244.68750,260.15625,275.62500,291.09375,306.56250,322.03125,337.50000,352.96875,8.43750,23.90625,39.37500,54.84375,70.31250,85.78125,101.25000,116.71875,132.18750,147.65625,163.12500,178.59375,194.06250,209.53125,225.00000,240.46875,255.93750,271.40625,286.87500,302.34375,317.81250,333.28125,348.75000,4.21875,19.68750,35.15625,50.62500,66.09375,81.56250,97.03125,112.50000,127.96875,143.43750,158.90625,174.37500,189.84375,205.31250,220.78125,236.25000,251.71875,267.18750,282.65625,298.12500,313.59375,329.06250,344.53125])
    
    scaled_harmonic_errors, harmonic_errors, angle_error, error_mag = admt4000_calibration(primary_angles, ref_angles)
    corrected_angle_error, corrected_error_mag = calculate_corrections(angle_error, harmonic_errors, ref_angles)

    print("Harmonic Errors (raw):", harmonic_errors)
    print("Scaled Harmonic Errors:", scaled_harmonic_errors)

    print_cal_plots(primary_angles, angle_error, error_mag, corrected_angle_error, corrected_error_mag)