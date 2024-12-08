#!/usr/bin/env python3
"""
Example script demonstrating how to use the BPM detector package.
"""

from bpm_detector import analyze_bpm, BPMAlgorithm

def analyze_with_all_algorithms(audio_file):
    """Analyze an audio file with all available algorithms"""
    print(f"Analyzing file: {audio_file}")
    print("-" * 50)
    
    for algorithm in BPMAlgorithm:
        try:
            bpm = analyze_bpm(audio_file, algorithm)
            print(f"{algorithm.value}: {bpm:.1f} BPM")
        except Exception as e:
            print(f"{algorithm.value}: Error - {e}")
    
    print("-" * 50)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_audio.py <audio_file>")
        sys.exit(1)
    
    analyze_with_all_algorithms(sys.argv[1]) 