import soundfile as sf
import numpy as np
from scipy import signal
from enum import Enum
from dataclasses import dataclass
from typing import Dict
from scipy import stats

class BPMAlgorithm(Enum):
    AUTOCORRELATION = "autocorrelation"
    ENERGY_FLUX = "energy flux"
    WEB_STYLE = "web style"

@dataclass
class BPMResult:
    bpm: float
    confidence: float  # 0-1 scale

class BPMDetector:
    def __init__(self, min_bpm=92, max_bpm=184):
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm

    def detect_all(self, audio_data, sample_rate) -> Dict[BPMAlgorithm, BPMResult]:
        """
        Run all BPM detection algorithms and return their results.
        
        Args:
            audio_data (numpy.ndarray): Audio signal data
            sample_rate (int): Sample rate of the audio
            
        Returns:
            Dict[BPMAlgorithm, BPMResult]: Results from all algorithms
        """
        if len(audio_data) == 0:
            raise ValueError("Empty audio data")
        if sample_rate <= 0:
            raise ValueError("Invalid sample rate")
            
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Run all algorithms
        results = {}
        valid_bpms = []
        
        # First pass: collect all BPM values
        for algo in BPMAlgorithm:
            bpm = self.detect(audio_data, sample_rate, algo)
            if bpm > 0:  # Only consider valid BPM values
                valid_bpms.append(bpm)
            results[algo] = BPMResult(bpm=bpm, confidence=0.0)  # Initial confidence
        
        # Calculate confidence by comparing with other algorithms
        if len(valid_bpms) >= 2:  # Need at least 2 valid results
            for algo in BPMAlgorithm:
                if results[algo].bpm <= 0:  # Skip invalid results
                    continue
                
                this_bpm = results[algo].bpm
                nearest_int = round(this_bpm)
                
                # Calculate how close this result is to the nearest integer
                diff_from_int = abs(this_bpm - nearest_int)
                int_factor = 1.0 - min(diff_from_int, 0.5) / 0.5  # 0.5 BPM max difference
                
                # Compare with other algorithms
                other_bpms = [bpm for bpm in valid_bpms if abs(bpm - this_bpm) > 0.001]  # Exclude self
                if not other_bpms:
                    results[algo] = BPMResult(bpm=this_bpm, confidence=int_factor)
                    continue
                
                # Find how many other results are near the same integer
                near_same_int = sum(1 for bpm in other_bpms 
                                  if abs(round(bpm) - nearest_int) <= 1)  # Allow ±1 BPM difference
                agreement_factor = near_same_int / len(other_bpms)
                
                # Calculate final confidence
                # 60% weight on integer proximity, 40% on agreement with other algorithms
                confidence = int_factor * 0.6 + agreement_factor * 0.4
                
                results[algo] = BPMResult(bpm=this_bpm, confidence=confidence)
        
        return results

    def detect(self, audio_data, sample_rate, algorithm=BPMAlgorithm.AUTOCORRELATION):
        """Single algorithm detection method"""
        if algorithm == BPMAlgorithm.AUTOCORRELATION:
            return analyze_bpm_autocorrelation(audio_data, sample_rate, self.min_bpm, self.max_bpm)
        elif algorithm == BPMAlgorithm.ENERGY_FLUX:
            return analyze_bpm_energy_flux(audio_data, sample_rate, self.min_bpm, self.max_bpm)
        elif algorithm == BPMAlgorithm.WEB_STYLE:
            return analyze_bpm_web_style(audio_data, sample_rate, self.min_bpm, self.max_bpm)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

def analyze_bpm_autocorrelation(audio_data, sample_rate, min_bpm=92, max_bpm=184):
    """BPM detection using autocorrelation method"""
    # Convert to mono and normalize
    audio_data = audio_data / np.max(np.abs(audio_data))
    
    # Parameters
    hop_length = 512
    win_length = 2048
    
    # Compute onset envelope
    onset_env = onset_strength(audio_data, sample_rate, hop_length=hop_length)
    
    # Convert to lag values
    min_lag = int(60.0 * sample_rate / (hop_length * max_bpm))
    max_lag = int(60.0 * sample_rate / (hop_length * min_bpm))
    
    # Compute autocorrelation
    ac = signal.correlate(onset_env, onset_env, mode='full')
    ac = ac[len(ac)//2:]  # Keep only positive lags
    
    # Restrict to tempo range
    ac = ac[min_lag:max_lag]
    
    # Find peaks in autocorrelation
    peaks = signal.find_peaks(ac, distance=min_lag)[0]
    if len(peaks) == 0:
        return 0
    
    # Convert peak positions to BPM
    lag_peaks = peaks + min_lag
    bpms = 60.0 * sample_rate / (hop_length * lag_peaks)
    
    # Weight by peak height
    peak_heights = ac[peaks]
    if len(peak_heights) > 0:
        best_peak = peaks[np.argmax(peak_heights)]
        bpm = 60.0 * sample_rate / (hop_length * (best_peak + min_lag))
        if min_bpm <= bpm <= max_bpm:
            return float(bpm)
    
    return 0

def analyze_bpm_energy_flux(audio_data, sample_rate, min_bpm=92, max_bpm=184):
    """BPM detection using energy flux method"""
    # Parameters
    frame_size = 1024
    hop_size = 512
    n_fft = 2048  # Fixed FFT size
    
    # Compute energy flux
    flux = np.zeros(len(audio_data) // hop_size - 1)
    for i in range(len(flux)):
        frame1 = audio_data[i * hop_size:i * hop_size + frame_size]
        frame2 = audio_data[(i + 1) * hop_size:(i + 1) * hop_size + frame_size]
        
        # Zero-pad frames to n_fft
        frame1 = np.pad(frame1, (0, n_fft - len(frame1)))
        frame2 = np.pad(frame2, (0, n_fft - len(frame2)))
        
        # Compute spectral flux
        spec1 = np.abs(np.fft.rfft(frame1))
        spec2 = np.abs(np.fft.rfft(frame2))
        flux[i] = np.sum(np.maximum(0, spec2 - spec1))
    
    # Find peaks in energy flux
    peaks = signal.find_peaks(flux, distance=int(0.3 * sample_rate / hop_size))[0]
    
    if len(peaks) < 2:
        return 0
    
    # Calculate average time between peaks
    peak_times = peaks * hop_size / sample_rate
    intervals = np.diff(peak_times)
    avg_interval = np.median(intervals)
    
    # Convert to BPM
    bpm = 60.0 / avg_interval
    
    # Ensure result is in reasonable range
    if min_bpm <= bpm <= max_bpm:
        return float(bpm)
        
    return 0

def analyze_bpm_web_style(audio_data, sample_rate, min_bpm=92, max_bpm=184):
    """BPM detection using an approach similar to web-audio-beat-detector"""
    # Convert to mono and normalize
    audio_data = audio_data / np.max(np.abs(audio_data))
    
    # Parameters
    frame_size = 2048
    hop_size = 512
    
    # Split audio into frames
    num_frames = (len(audio_data) - frame_size) // hop_size + 1
    frames = np.array([audio_data[i * hop_size:i * hop_size + frame_size] 
                      for i in range(num_frames)])
    
    # Apply Hanning window
    window = np.hanning(frame_size)
    frames = frames * window
    
    # Calculate energy for each frame
    energies = np.sum(frames ** 2, axis=1)
    
    # Calculate energy flux (difference between consecutive frames)
    energy_flux = np.diff(energies)
    energy_flux = np.maximum(energy_flux, 0)  # Keep only positive changes
    
    # Normalize energy flux
    energy_flux = energy_flux / np.max(energy_flux)
    
    # Find peaks (beat candidates)
    # Use dynamic thresholding
    threshold = np.mean(energy_flux) + 0.1 * np.std(energy_flux)
    peaks = signal.find_peaks(energy_flux, height=threshold, distance=int(0.35 * sample_rate / hop_size))[0]
    
    if len(peaks) < 2:
        return 0
    
    # Convert peaks to time domain
    peak_times = peaks * hop_size / sample_rate
    
    # Calculate intervals between peaks
    intervals = np.diff(peak_times)
    
    # Convert intervals to BPM
    bpms = 60 / intervals
    
    # Filter BPMs to the specified range
    valid_bpms = bpms[(bpms >= min_bpm) & (bpms <= max_bpm)]
    
    if len(valid_bpms) == 0:
        return 0
    
    # Use kernel density estimation to find the most common BPM
    kde = stats.gaussian_kde(valid_bpms)
    bpm_range = np.linspace(min_bpm, max_bpm, 200)
    bpm_probs = kde(bpm_range)
    
    # Get the BPM with highest probability
    best_bpm = bpm_range[np.argmax(bpm_probs)]
    
    return float(best_bpm)

def onset_strength(y, sr, hop_length=512):
    """Compute onset strength envelope with improved parameters"""
    # Parameters
    n_fft = 2048
    
    # Compute spectrogram with mel scaling
    freqs = np.linspace(0, sr/2, n_fft//2 + 1)
    mel_f = 2595 * np.log10(1 + freqs/700)
    mel_weights = np.exp(-0.5 * ((mel_f[:, np.newaxis] - mel_f) / (mel_f[1] - mel_f[0])) ** 2)
    mel_weights = mel_weights / mel_weights.sum(axis=1, keepdims=True)
    
    # Compute STFT
    D = np.abs(signal.stft(y, nperseg=n_fft, noverlap=n_fft-hop_length)[2])
    
    # Apply mel weighting
    D = np.dot(mel_weights, D)
    
    # Convert to log-magnitude
    D = np.log1p(D)
    
    # Compute first-order difference
    onset_env = np.diff(D, axis=1)
    onset_env = np.maximum(0, onset_env)
    
    # Apply high-pass filter to remove DC
    b, a = signal.butter(2, 0.1, btype='high', fs=sr/hop_length)
    onset_env = signal.filtfilt(b, a, onset_env, axis=1)
    
    # Normalize
    onset_env = onset_env - onset_env.mean(axis=1, keepdims=True)
    onset_env = onset_env / onset_env.std(axis=1, keepdims=True)
    onset_env = np.mean(onset_env, axis=0)
    onset_env = onset_env / np.max(np.abs(onset_env))
    
    return onset_env