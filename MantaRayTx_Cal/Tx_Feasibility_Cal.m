instrreset
clear
close all
clc;

%Connect to instruments
cxa = N9000A('CXA', 'TCPIP0::A-N9000A-30136.local::hislip0::INSTR');
psg = E8267D('SigGen1', 'TCPIP0::192.169.10.24::inst0::INSTR');


centerFreq_MHz = 10000;    %Set equipment center frequency
TonePower = -48;            %Set sig gen power accounting for OTA loss
IQ_BW = 10;             %Set IQ bandwidth for spec an - 10MHz max on CXA
ResBW = 15e3;           %Set ResBW in kHz - limits #samples in fft
DigIFBW = 10;           %Set digital IF bandwidth for spec an - 10MHz max on CXA

psg.Set_Freq_MHz(centerFreq_MHz);
psg.Set_Power_dBm(TonePower);
 

currentFreq_Hz = psg.Get_Freq_Hz();
currentFreq_MHz = currentFreq_Hz / 1e6;

cxa.Select_IQModeMode                   %Set IQMode for spec an
cxa.Reset()                             %Perform initialization reset
cxa.Set_InitiateContinuousSweep('ON')   %Continuous sweep condition
cxa.Set_IQ_Spectrum_Span(IQ_BW)         
cxa.Set_IQMode_Spec_Bandwidth(ResBW)
cxa.Set_Center_Freq(centerFreq_MHz)
cxa.Set_IQMode_Bandwidth(DigIFBW)
cxa.bursttrig('POS', -1, -55, 0)        %Set trigger parameters for spec an
cxa.trigger()
cxa.waveyscale(0, 25, 'CENT', 'ON')     %Set y-scale of IQ window
cxa.wavexscale(0, 4000, 'LEFT', 'OFF')  %Set x-scale of IQ window

currentPower_dBm = psg.Get_Power_dBm();

psg.Set_OutputState('ON')               %Turn on sig gen
Data = cxa.IQ_Complex_Data();           %Collect IQ data from spec an
pause(0.01)
psg.Set_OutputState('OFF')              %Turn off sig gen

%%%%%%%%%%%%%    Post Processing Section    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

I = real(Data);         %Variables for real/imaginary portions of complex data
Q = imag(Data);

%ComplexMag = abs(Data)

%Plot I and Q waveforms
figure          
subplot(2,1,1)
plot(abs(I))
title('I component')
subplot(2,1,2)
plot(abs(Q))
title('Q component')

% %Find samples in IQ > 0.0005V
[RealPk, RealLocs] = findpeaks(abs(I), 'MinPeakHeight',0.00055);

[ImagPk, ImagLocs] = findpeaks(abs(Q), 'MinPeakHeight', 0.00055);

% %Select I or Q waveform for calibration based on #vals above 0.00055V
if(length(RealPk) > length(ImagPk))
    ProcessArray = I;
elseif(length(RealPk) < length(ImagPk))
    ProcessArray = Q;
else
    ProcessArray = I;
end
% 
% %Find rising edge of first pulse
% SampleThreshold = 0.00055;          %Set sample threshold to find first pulse

numChannels = 4;

% function phaseValues = pulseOffset(pulsedData,numChannels)
%     % pulseOffset Returns the phase values in a numChannels x 1
%     % row vector using the Spectrum Analyzer IQ Demodulator. 
% 
%     if numChannels ~= 4 && numChannels ~= 2
%          error('numChannels arugment must be integer value of 2 or 4')               
%     end
% 
    minCodeValue = 0.00055;
    % Align All Tx Channels
    % Now Find The Pulse Corresponding To Tx0
    if ((abs((I(1,1)))>minCodeValue) || (abs((Q(1,1)))>minCodeValue) || ...
            ((abs(I(150,1)))>minCodeValue) || ((abs(Q(150,1)))>minCodeValue)) %Check if signal is present at start of capture
        [separation,initialCross,finalCross,nextCross,midLev] = ...
            pulsesep(double(abs(real(Data(:,1)))>minCodeValue));
        [maxVal, maxLoc] = max(separation);
        channel0Start = ceil(nextCross(maxLoc)); %The Tx0 pulse location
    else %Correct if signal is zero at start of capture
        [period,initialCross,finalCross,nextCross,midLev] = ...
            pulseperiod(double(abs(ProcessArray(:,1))>minCodeValue));
        channel0Start = ceil(initialCross(1));
    end
    timeZeroAlignedFirstRx = circshift(Data(:,1),-channel0Start);
    timeZeroAligned = circshift(Data,-channel0Start);

    figure          
    plot(abs(timeZeroAligned))
    title('Zero Aligned Samples')
    % Now Determine the Phase Offsets for Each Tx Channel
    for i=1:1:numChannels
        phaseValues(i,1) = angle(timeZeroAlignedFirstRx(15+(i-1)*150))*180/pi;
    end
%     phaseValues = wrapTo180(txPhaseOffsets - txPhaseOffsets(size(txPhaseOffsets,2),1))';
% end