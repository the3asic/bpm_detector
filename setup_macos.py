"""
This is a setup.py script specifically for creating a macOS app using py2app.
Usage:
    python setup_macos.py py2app
"""

from setuptools import setup
import os

APP = ['src/bpm_detector/main.py']
DATA_FILES = []
OPTIONS = {
    'packages': [
        'PyQt6',
        'numpy',
        'scipy',
        'soundfile',
        'cffi',
        'bpm_detector',
    ],
    'includes': [
        'numpy.core._methods',
        'numpy.lib.format',
        'scipy.signal',
        'scipy.stats',
    ],
    'excludes': ['tkinter', 'PySide6', 'PyQt5'],
    'frameworks': [
        '/opt/homebrew/lib/libsndfile.1.dylib',
    ],
    'plist': {
        'CFBundleName': 'BPM Detector',
        'CFBundleDisplayName': 'BPM Detector',
        'CFBundleIdentifier': 'com.bpmdetector.app',
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': 'Copyright © 2024',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13',
        'NSAppleEventsUsageDescription': 'This app needs to access files for BPM detection.',
        'NSMicrophoneUsageDescription': 'This app needs access to audio files for BPM detection.',
        'LSEnvironment': {
            'DYLD_LIBRARY_PATH': '@executable_path/../Frameworks',
            'DYLD_FRAMEWORK_PATH': '@executable_path/../Frameworks',
            'QT_MAC_WANTS_LAYER': '1',
        },
    },
    'resources': [
        'src/bpm_detector',
    ],
    'site_packages': True,
    'strip': False,
    'semi_standalone': False,
    'arch': 'arm64',
    'qt_plugins': [
        'platforms/libqmacnative.dylib',
        'platforms/libqcocoa.dylib',
        'styles/libqmacstyle.dylib'
    ],
}

# Add icon if it exists
icon_path = 'resources/icon.icns'
if os.path.exists(icon_path):
    OPTIONS['iconfile'] = icon_path

setup(
    name="BPM Detector",
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'PyQt6>=6.7.0',
        'numpy>=1.24.3',
        'scipy>=1.11.3',
        'soundfile>=0.12.1',
        'cffi>=1.15.0',
    ],
) 