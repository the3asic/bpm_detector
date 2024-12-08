import pytest
import numpy as np
from bpm_detector.detector import BPMDetector, BPMAlgorithm

def test_bpm_detector_initialization():
    detector = BPMDetector()
    assert detector is not None

def test_detect_bpm_with_simple_signal():
    # Create a simple periodic signal at 120 BPM (2 Hz)
    sample_rate = 44100
    duration = 5  # seconds
    bpm = 120
    frequency = bpm / 60  # Convert BPM to Hz
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Create a more realistic signal with harmonics
    signal = np.sin(2 * np.pi * frequency * t) + 0.5 * np.sin(4 * np.pi * frequency * t)
    
    detector = BPMDetector()
    detected_bpm = detector.detect(signal, sample_rate, algorithm=BPMAlgorithm.ENERGY_FLUX)
    
    # Allow for some margin of error (±1 BPM)
    assert abs(detected_bpm - bpm) <= 1

def test_detect_bpm_with_soundtouch():
    # Create a simple periodic signal at 128 BPM
    sample_rate = 44100
    duration = 10  # seconds (longer duration for better accuracy)
    bpm = 128
    frequency = bpm / 60  # Convert BPM to Hz
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a more complex signal with multiple harmonics and envelope
    envelope = 1 + 0.5 * np.sin(2 * np.pi * 0.5 * t)  # Amplitude modulation
    signal = envelope * (
        np.sin(2 * np.pi * frequency * t) +  # Fundamental
        0.5 * np.sin(4 * np.pi * frequency * t) +  # 2nd harmonic
        0.25 * np.sin(6 * np.pi * frequency * t)   # 3rd harmonic
    )
    
    detector = BPMDetector()
    try:
        detected_bpm = detector.detect(signal, sample_rate, algorithm=BPMAlgorithm.SOUNDTOUCH)
        # Allow for some margin of error (±2 BPM)
        assert abs(detected_bpm - bpm) <= 2
    except RuntimeError as e:
        if "SoundTouch library not found" in str(e):
            pytest.skip("SoundTouch library not installed")
        raise

def test_detect_bpm_with_empty_signal():
    detector = BPMDetector()
    with pytest.raises(ValueError):
        detector.detect(np.array([]), 44100, algorithm=BPMAlgorithm.AUTOCORRELATION)

def test_detect_bpm_with_invalid_sample_rate():
    detector = BPMDetector()
    signal = np.array([0, 1, 0, 1])
    with pytest.raises(ValueError):
        detector.detect(signal, -1, algorithm=BPMAlgorithm.AUTOCORRELATION) 