#!/usr/bin/env python3
"""
Main entry point for the BPM Detector macOS app
"""

import os
import sys
from bpm_detector.gui import main

if __name__ == '__main__':
    # Set up any environment variables needed
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    
    # If we're in a bundle, add the bundle's Contents/Frameworks to dyld search path
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        frameworks_path = os.path.join(bundle_dir, 'Frameworks')
        if 'DYLD_LIBRARY_PATH' in os.environ:
            os.environ['DYLD_LIBRARY_PATH'] = f"{frameworks_path}:{os.environ['DYLD_LIBRARY_PATH']}"
        else:
            os.environ['DYLD_LIBRARY_PATH'] = frameworks_path
    
    # Run the app
    main() 