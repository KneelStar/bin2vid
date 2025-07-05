import os
import shutil
import argparse
import subprocess
import math
import tempfile

WIDTH = 1920
HEIGHT = 1080
PIXELS_PER_FRAME = WIDTH * HEIGHT
BYTES_PER_FRAME = PIXELS_PER_FRAME * 3  # RGB24


def check_tools():
    for tool in ['ffmpeg', 'zstd', 'tar']:
        if shutil.which(tool) is None:
            raise RuntimeError(f"Required tool '{tool}' not found in PATH.")


def compress_folder_to_zst(folder_path, output_file):
    temp_tar = output_file + '.tar'
    print(f"[📦] Creating TAR archive from folder '{folder_path}'")
    subprocess.run(['tar', '-cf', temp_tar, '-C', folder_path, '.'], check=True)

    print(f"[🗜️] Compressing TAR with zstd to '{output_file}'")
    subprocess.run(['zstd', '-19', '--long=31', '-T0', temp_tar, '-o', output_file], check=True)
    os.remove(temp_tar)


def decompress_zst_to_folder(zst_file, output_folder):
    temp_tar = zst_file + '.tar'
    print(f"[🗜️] Decompressing '{zst_file}' to TAR")
    subprocess.run(['zstd', '--long=31', '-d', zst_file, '-o', temp_tar], check=True)

    print(f"[📂] Extracting TAR to folder '{output_folder}'")
    os.makedirs(output_folder, exist_ok=True)
    subprocess.run(['tar', '-xf', temp_tar, '-C', output_folder], check=True)
    os.remove(temp_tar)


def encode_zst_to_video(zst_file, video_file, meta_file):
    with open(zst_file, 'rb') as f:
        data = f.read()

    original_size = len(data)
    num_frames = math.ceil(original_size / BYTES_PER_FRAME)
    padded = data + b'\x00' * (BYTES_PER_FRAME * num_frames - original_size)

    raw_file = video_file + '.rgb'
    meta_file = meta_file + ".meta"

    with open(raw_file, 'wb') as out:
        out.write(padded)

    with open(meta_file, 'w') as meta:
        meta.write(f"{original_size}\n{num_frames}\n")

    print(f"[🎞️] Encoding {num_frames} frames to video '{video_file}'")
    subprocess.run([
        'ffmpeg',
        '-f', 'rawvideo',
        '-pixel_format', 'rgb24',
        '-video_size', f'{WIDTH}x{HEIGHT}',
        '-framerate', '30',
        '-i', raw_file,
        '-c:v', 'ffv1',
        '-level', '3',
        '-g', '1',
        '-coder', '1',
        '-context', '1',
        '-slices', '4',
        video_file,
        '-y'
    ], check=True)
    os.remove(raw_file)
    print(f"[✅] Video written to {video_file}")


def decode_video_to_zst(video_file, meta_file, output_zst):
    raw_file = "temp_decoded.rgb"

    print(f"[🎬] Decoding video '{video_file}' to raw RGB")
    subprocess.run([
        'ffmpeg',
        '-i', video_file,
        '-f', 'rawvideo',
        '-pix_fmt', 'rgb24',
        raw_file,
        '-y'
    ], check=True)

    with open(meta_file, 'r') as meta:
        original_size, _ = map(int, meta.read().splitlines())

    with open(raw_file, 'rb') as f:
        data = f.read()

    os.remove(raw_file)

    restored = data[:original_size]

    with open(output_zst, 'wb') as out:
        out.write(restored)

    print(f"[✅] Restored compressed file: {output_zst}")


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
    check_tools()

    if args.command == 'encode':
        video_path = args.out + '.mkv'
        meta_path = args.out + '.meta'
        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        temp_zst = args.out + '.zst'
        compress_folder_to_zst(args.folder, temp_zst)
        encode_zst_to_video(temp_zst, video_path, meta_path)
        os.remove(temp_zst)

    elif args.command == 'decode':
        video_path = args.out + '.mkv'
        meta_path = args.out + '.meta'
        temp_zst = args.output_folder + '.zst'

        decode_video_to_zst(video_path, meta_path, temp_zst)
        decompress_zst_to_folder(temp_zst, args.output_folder)
        os.remove(temp_zst)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
