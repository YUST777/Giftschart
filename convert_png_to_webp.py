#!/usr/bin/env python3
"""
Convert all PNG images to WebP format to save space.
This script converts images in downloaded_images/ and sticker_collections/
"""

import os
from PIL import Image
import sys

def convert_png_to_webp(input_path, output_path=None, quality=85):
    """Convert a PNG image to WebP format"""
    try:
        img = Image.open(input_path)
        
        # Convert RGBA to RGB if needed (WebP supports both)
        if img.mode == 'RGBA':
            # Keep alpha channel for WebP
            pass
        elif img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        
        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '.webp'
        
        # Save as WebP
        img.save(output_path, 'WEBP', quality=quality, method=6)
        
        # Get file sizes
        png_size = os.path.getsize(input_path)
        webp_size = os.path.getsize(output_path)
        savings = ((png_size - webp_size) / png_size) * 100
        
        print(f"Converted: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        print(f"  Size: {png_size:,} bytes -> {webp_size:,} bytes ({savings:.1f}% smaller)")
        
        return True, savings
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False, 0

def is_png_file(filepath):
    """Check if a file is a PNG image by extension or actual format"""
    # Check by extension
    if filepath.lower().endswith('.webp'):
        return True
    # Check for _png suffix (common in sticker_collections)
    if filepath.endswith('_png') or filepath.endswith('_PNG'):
        return True
    # Check actual file format
    try:
        img = Image.open(filepath)
        if img.format == 'PNG':
            return True
    except:
        pass
    return False

def convert_directory(directory, recursive=True):
    """Convert all PNG files in a directory to WebP"""
    converted = 0
    failed = 0
    total_savings = 0
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return converted, failed, total_savings
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            input_path = os.path.join(root, file)
            
            # Check if it's a PNG file
            if not is_png_file(input_path):
                continue
            
            # Generate output path
            if file.lower().endswith('.webp'):
                output_path = input_path.rsplit('.', 1)[0] + '.webp'
            elif file.endswith('_png') or file.endswith('_PNG'):
                # Replace _png with .webp
                output_path = input_path.rsplit('_png', 1)[0] + '.webp'
            else:
                # Try to detect format and add .webp
                output_path = input_path + '.webp'
            
            # Skip if WebP already exists
            if os.path.exists(output_path):
                print(f"Skipping {file} (WebP already exists)")
                continue
            
            success, savings = convert_png_to_webp(input_path, output_path)
            if success:
                converted += 1
                total_savings += savings
                # Optionally remove PNG after conversion
                # os.remove(input_path)
            else:
                failed += 1
        
        if not recursive:
            break
    
    return converted, failed, total_savings

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Directories to convert
    directories = [
        os.path.join(script_dir, "downloaded_images"),
        os.path.join(script_dir, "sticker_collections"),
        os.path.join(script_dir, "pregenerated_backgrounds"),
    ]
    
    total_converted = 0
    total_failed = 0
    total_savings = 0
    
    for directory in directories:
        print(f"\n{'='*60}")
        print(f"Converting images in: {directory}")
        print(f"{'='*60}")
        
        converted, failed, savings = convert_directory(directory, recursive=True)
        total_converted += converted
        total_failed += failed
        total_savings += savings
    
    print(f"\n{'='*60}")
    print(f"Conversion Summary:")
    print(f"  Converted: {total_converted} files")
    print(f"  Failed: {total_failed} files")
    if total_converted > 0:
        avg_savings = total_savings / total_converted
        print(f"  Average space savings: {avg_savings:.1f}%")
    print(f"{'='*60}")

