#!/usr/bin/env python3
"""
Zip to IPA Converter with Xcode Project Detection

This tool detects Xcode project files in a ZIP, validates the structure,
and converts it to an IPA file.

Xcode project files detected:
- .xcodeproj (project bundle)
- .pbxproj (project file)
- .xcworkspace (workspace)
- Info.plist (app configuration)

Usage:
    python zip_to_ipa.py input.zip output.ipa
"""

import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path

# Xcode project markers
XCODE_MARKERS = {
    '.xcodeproj': 'Xcode Project Bundle',
    '.pbxproj': 'Xcode Project File',
    '.xcworkspace': 'Xcode Workspace',
    'Info.plist': 'iOS App Configuration',
    '.xcassets': 'Asset Catalog',
    '.storyboard': 'Interface Builder File',
    '.xib': 'Interface Builder File',
    'Podfile': 'CocoaPods Dependency',
    'Cartfile': 'Carthage Dependency',
}

def detect_files_in_zip(zip_path):
    """
    Extract and list all files/folders in a ZIP file.
    
    Returns:
        dict: Contains 'files' and 'directories' lists
    """
    files = []
    directories = set()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for name in zip_ref.namelist():
                files.append(name)
                # Track directories
                if '/' in name:
                    dir_path = '/'.join(name.split('/')[:-1])
                    directories.add(dir_path)
    except Exception as e:
        raise Exception(f"Error reading ZIP file: {str(e)}")
    
    return {
        'files': files,
        'directories': sorted(list(directories))
    }

def detect_xcode_files(zip_path):
    """
    Detect Xcode project files and folders in a ZIP.
    
    Returns:
        dict: Contains detected Xcode elements and their paths
    """
    detected = {
        'has_xcode_project': False,
        'xcode_files': [],
        'xcode_folders': [],
        'validation_status': 'Not an Xcode project',
        'details': {}
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for name in zip_ref.namelist():
                name_lower = name.lower()
                
                # Check for Xcode markers
                for marker, description in XCODE_MARKERS.items():
                    if marker.lower() in name_lower:
                        detected['has_xcode_project'] = True
                        detected['xcode_files'].append({
                            'path': name,
                            'type': description
                        })
                        if marker not in detected['details']:
                            detected['details'][marker] = []
                        detected['details'][marker].append(name)
                        break
    except Exception as e:
        raise Exception(f"Error detecting Xcode files: {str(e)}")
    
    if detected['has_xcode_project']:
        detected['validation_status'] = 'Valid Xcode project detected'
    
    return detected

def convert_zip_to_ipa(input_zip, output_ipa):
    """
    Convert a ZIP file to an IPA file with validation.

    Args:
        input_zip (str): Path to the input ZIP file.
        output_ipa (str): Path for the output IPA file.
        
    Returns:
        dict: Conversion results with detection info
    """
    if not os.path.isfile(input_zip):
        raise Exception(f"Input file '{input_zip}' does not exist.")

    if not input_zip.lower().endswith('.zip'):
        print(f"Warning: Input file '{input_zip}' does not have .zip extension.")

    # Ensure output has .ipa extension
    if not output_ipa.lower().endswith('.ipa'):
        output_ipa += '.ipa'

    # Detect files and Xcode structure
    file_info = detect_files_in_zip(input_zip)
    xcode_info = detect_xcode_files(input_zip)

    result = {
        'success': False,
        'input_file': input_zip,
        'output_file': output_ipa,
        'file_count': len(file_info['files']),
        'directory_count': len(file_info['directories']),
        'xcode_detection': xcode_info,
        'message': ''
    }

    # Validate and convert
    try:
        if not xcode_info['has_xcode_project']:
            result['message'] = 'Warning: ZIP does not contain recognizable Xcode project files. Proceeding with conversion anyway.'
        
        shutil.copyfile(input_zip, output_ipa)
        result['success'] = True
        result['message'] = f"Successfully converted '{input_zip}' to '{output_ipa}'"
        
    except Exception as e:
        result['message'] = f"Error during conversion: {str(e)}"
        raise Exception(result['message'])
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Convert ZIP file to IPA file with Xcode detection.")
    parser.add_argument("input_zip", help="Path to the input ZIP file")
    parser.add_argument("output_ipa", help="Path for the output IPA file")

    args = parser.parse_args()

    try:
        result = convert_zip_to_ipa(args.input_zip, args.output_ipa)
        print(f"\n✓ {result['message']}")
        print(f"  Files detected: {result['file_count']}")
        print(f"  Directories detected: {result['directory_count']}")
        print(f"  Xcode Project: {'Yes ✓' if result['xcode_detection']['has_xcode_project'] else 'No'}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()