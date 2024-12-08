#!/usr/bin/env python3
import argparse
import sys
from .detector import BPMAlgorithm, analyze_bpm

def main():
    parser = argparse.ArgumentParser(description='Analyze BPM of an audio file')
    parser.add_argument('audio_file', help='Path to the audio file')
    parser.add_argument('--algorithm', 
                      choices=[algo.value for algo in BPMAlgorithm],
                      default=BPMAlgorithm.SOUNDTOUCH.value,
                      help='BPM detection algorithm to use')
    
    args = parser.parse_args()
    
    try:
        bpm = analyze_bpm(args.audio_file, BPMAlgorithm(args.algorithm))
        print(f"Detected BPM ({args.algorithm}): {bpm:.1f}")
        return 0
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 