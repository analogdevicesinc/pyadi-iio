function spec_est(x, fs, fullscale)

Nfft = length( x );
win = kaiser(Nfft,100);
win = win/sum(win);
win = win*Nfft;
x = x.*win;

spec = fft( x ) / Nfft;

spec_db = 20*log10(abs(spec)/fullscale+10^-20);

df = fs/Nfft;  freqRangeRx = (-fs/2:df:fs/2-df).';
plot(freqRangeRx,fftshift(spec_db));
xlabel('Frequency (Hz)');
ylabel('Magnitude (dBFS)');
