import os
import shutil
import argparse
import subprocess
import math
import tempfile
import tarfile
import platform
import sys
from pathlib import Path

WIDTH = 1920
HEIGHT = 1080
PIXELS_PER_FRAME = WIDTH * HEIGHT
BYTES_PER_FRAME = PIXELS_PER_FRAME * 3  # RGB24


def get_tool_name(tool):
    """Get platform-specific tool name"""
    if platform.system() == 'Windows':
        # On Windows, executables might have .exe extension
        if tool == 'ffmpeg':
            return 'ffmpeg.exe'
        elif tool == 'zstd':
            return 'zstd.exe'
    return tool


def check_tools():
    """Check if required tools are available, with platform-specific handling"""
    required_tools = ['ffmpeg', 'zstd']
    missing_tools = []
    
    for tool in required_tools:
        tool_name = get_tool_name(tool)
        if shutil.which(tool_name) is None:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing required tools: {', '.join(missing_tools)}")
        print("\nInstallation instructions:")
        
        system = platform.system()
        if system == 'Windows':
            print("Windows:")
            print("  - Install via chocolatey: choco install ffmpeg zstd")
            print("  - Install via scoop: scoop install ffmpeg zstd")
            print("  - Or download from official websites")
        elif system == 'Darwin':  # macOS
            print("macOS:")
            print("  - Install via homebrew: brew install ffmpeg zstd")
            print("  - Or install via MacPorts: sudo port install ffmpeg zstd")
        elif system == 'Linux':
            print("Linux:")
            print("  - Ubuntu/Debian: sudo apt install ffmpeg zstd")
            print("  - CentOS/RHEL: sudo yum install ffmpeg zstd")
            print("  - Arch: sudo pacman -S ffmpeg zstd")
        
        raise RuntimeError(f"Required tools not found: {', '.join(missing_tools)}")


def compress_folder_to_zst(folder_path, output_file):
    """Compress folder using Python's tarfile module and zstd"""
    folder_path = Path(folder_path)
    output_file = Path(output_file)
    
    # Create temporary tar file - delete=False but we'll manage it ourselves
    temp_tar_fd, temp_tar_name = tempfile.mkstemp(suffix='.tar')
    temp_tar_path = Path(temp_tar_name)
    
    try:
        # Close the file descriptor since we just need the path
        os.close(temp_tar_fd)
        
        print(f"[📦] Creating TAR archive from folder '{folder_path}'")
        
        # Use Python's tarfile module for cross-platform compatibility
        with tarfile.open(temp_tar_path, 'w') as tar:
            # Add all files in the folder
            for item in folder_path.rglob('*'):
                if item.is_file():
                    # Calculate relative path for cross-platform compatibility
                    arcname = item.relative_to(folder_path)
                    tar.add(item, arcname=arcname)
        
        print(f"[🗜️] Compressing TAR with zstd to '{output_file}'")
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use zstd to compress - force overwrite with -f flag
        zstd_cmd = [get_tool_name('zstd'), '-19', '--long=31', '-T0', str(temp_tar_path), '-o', str(output_file), '-f']
        subprocess.run(zstd_cmd, check=True)
        
    finally:
        # Clean up temporary tar file
        if temp_tar_path.exists():
            temp_tar_path.unlink()


def decompress_zst_to_folder(zst_file, output_folder):
    """Decompress zst file to folder using cross-platform methods"""
    zst_file = Path(zst_file)
    output_folder = Path(output_folder)
    
    # Create temporary tar file - delete=False but we'll manage it ourselves
    temp_tar_fd, temp_tar_name = tempfile.mkstemp(suffix='.tar')
    temp_tar_path = Path(temp_tar_name)
    
    try:
        # Close the file descriptor since we just need the path
        os.close(temp_tar_fd)
        
        print(f"[🗜️] Decompressing '{zst_file}' to TAR")
        
        # Decompress with zstd - force overwrite with -f flag
        zstd_cmd = [get_tool_name('zstd'), '--long=31', '-d', str(zst_file), '-o', str(temp_tar_path), '-f']
        subprocess.run(zstd_cmd, check=True)
        
        print(f"[📂] Extracting TAR to folder '{output_folder}'")
        
        # Create output directory
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Extract using Python's tarfile module
        with tarfile.open(temp_tar_path, 'r') as tar:
            tar.extractall(output_folder)
            
    finally:
        # Clean up temporary tar file
        if temp_tar_path.exists():
            temp_tar_path.unlink()


def encode_zst_to_video(zst_file, video_file, meta_file):
    """Encode zst file to video using cross-platform paths"""
    zst_file = Path(zst_file)
    video_file = Path(video_file)
    meta_file = Path(meta_file)
    
    with open(zst_file, 'rb') as f:
        data = f.read()

    original_size = len(data)
    num_frames = math.ceil(original_size / BYTES_PER_FRAME)
    padded = data + b'\x00' * (BYTES_PER_FRAME * num_frames - original_size)

    # Create temporary raw file
    with tempfile.NamedTemporaryFile(suffix='.rgb', delete=False) as temp_raw:
        raw_file = Path(temp_raw.name)
        temp_raw.write(padded)

    try:
        # Write metadata
        with open(meta_file, 'w') as meta:
            meta.write(f"{original_size}\n{num_frames}\n")

        print(f"[🎞️] Encoding {num_frames} frames to video '{video_file}'")
        
        # Ensure output directory exists
        video_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command with cross-platform paths
        ffmpeg_cmd = [
            get_tool_name('ffmpeg'),
            '-f', 'rawvideo',
            '-pixel_format', 'rgb24',
            '-video_size', f'{WIDTH}x{HEIGHT}',
            '-framerate', '30',
            '-i', str(raw_file),
            '-c:v', 'ffv1',
            '-level', '3',
            '-g', '1',
            '-coder', '1',
            '-context', '1',
            '-slices', '4',
            str(video_file),
            '-y'
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"[✅] Video written to {video_file}")
        
    finally:
        # Clean up temporary raw file
        if raw_file.exists():
            raw_file.unlink()


def decode_video_to_zst(video_file, meta_file, output_zst):
    """Decode video to zst file using cross-platform paths"""
    video_file = Path(video_file)
    meta_file = Path(meta_file)
    output_zst = Path(output_zst)
    
    # Create temporary raw file
    with tempfile.NamedTemporaryFile(suffix='.rgb', delete=False) as temp_raw:
        raw_file = Path(temp_raw.name)

    try:
        print(f"[🎬] Decoding video '{video_file}' to raw RGB")
        
        # Build ffmpeg command
        ffmpeg_cmd = [
            get_tool_name('ffmpeg'),
            '-i', str(video_file),
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            str(raw_file),
            '-y'
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)

        # Read metadata
        with open(meta_file, 'r') as meta:
            lines = meta.read().strip().split('\n')
            original_size = int(lines[0])

        # Read and truncate data
        with open(raw_file, 'rb') as f:
            data = f.read()

        restored = data[:original_size]

        # Ensure output directory exists
        output_zst.parent.mkdir(parents=True, exist_ok=True)
        
        # Write restored data
        with open(output_zst, 'wb') as out:
            out.write(restored)

        print(f"[✅] Restored compressed file: {output_zst}")
        
    finally:
        # Clean up temporary raw file
        if raw_file.exists():
            raw_file.unlink()


def main():
    parser = argparse.ArgumentParser(description="Convert folders to/from lossless FFV1 video using zstd")
    subparsers = parser.add_subparsers(dest='command')

    enc = subparsers.add_parser('encode', help='Compress folder and encode as video')
    enc.add_argument('folder', help='Input folder to compress and encode')
    enc.add_argument('--out', required=True, help='Output prefix (e.g. out/backup)')

    dec = subparsers.add_parser('decode', help='Decode video and restore original folder')
    dec.add_argument('--out', required=True, help='Prefix used during encode (e.g. out/backup)')
    dec.add_argument('--output-folder', required=True, help='Folder to restore original contents into')

    args = parser.parse_args()
    
    try:
        check_tools()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.command == 'encode':
        out_path = Path(args.out)
        video_path = out_path.with_suffix('.mkv')
        meta_path = out_path.with_suffix('.meta')
        temp_zst = out_path.with_suffix('.zst')
        
        try:
            compress_folder_to_zst(args.folder, temp_zst)
            encode_zst_to_video(temp_zst, video_path, meta_path)
        finally:
            # Clean up temporary zst file
            if temp_zst.exists():
                temp_zst.unlink()

    elif args.command == 'decode':
        out_path = Path(args.out)
        video_path = out_path.with_suffix('.mkv')
        meta_path = out_path.with_suffix('.meta')
        output_folder = Path(args.output_folder)
        temp_zst = output_folder.with_suffix('.zst')

        try:
            decode_video_to_zst(video_path, meta_path, temp_zst)
            decompress_zst_to_folder(temp_zst, output_folder)
        finally:
            # Clean up temporary zst file
            if temp_zst.exists():
                temp_zst.unlink()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()