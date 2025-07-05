# bin2vid

`bin2vid` is a **cross-platform** Python tool for **losslessly** converting any folder into a **compressed video** using Zstandard (zstd) compression and FFmpeg's lossless FFV1 codec, and for decoding it back to the original folder.

---

## Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- Archive and compress a folder with built-in `tarfile` + `zstd` (lossless, multithreaded)
- Pack the compressed `.zst` into a raw RGB video stream
- Encode the RGB stream into a lossless FFV1 video (`.mkv`)
- Decode the video back to `.zst`, decompress, and restore the exact original folder
- Minimal Python dependencies—uses system tools (`ffmpeg`, `zstd`) and built-in Python modules
- Automatic platform-specific tool detection and helpful installation guidance

---

## Requirements

- **Python 3.6+**
- **FFmpeg** (CLI in PATH)
- **Zstandard (zstd)** (CLI in PATH)

**No external tar dependency** - uses Python's built-in `tarfile` module for cross-platform compatibility.

---

## Installation

### Install Required Tools

#### Windows
```bash
# Via chocolatey
choco install ffmpeg zstd

# Via scoop
scoop install ffmpeg zstd
```

#### macOS
```bash
# Via homebrew
brew install ffmpeg zstd

# Via MacPorts
sudo port install ffmpeg zstd
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install ffmpeg zstd

# CentOS/RHEL/Fedora
sudo yum install ffmpeg zstd
# or: sudo dnf install ffmpeg zstd

# Arch Linux
sudo pacman -S ffmpeg zstd
```

### Verify Installation
```bash
ffmpeg -version
zstd --version
```

### Get the Script
No additional Python packages required. Simply download `bin2vid.py` to your project directory.

---

## Usage

### Encode a folder to video
```bash
python bin2vid.py encode /path/to/folder --out /path/to/output_prefix
```

**Example:**
```bash
python bin2vid.py encode ./my_folder --out backup/encoded_data
```

This creates:
- `backup/encoded_data.mkv` — lossless FFV1 video
- `backup/encoded_data.meta` — metadata for decoding

### Decode video back to folder
```bash
python bin2vid.py decode --out /path/to/output_prefix --output-folder /path/to/restore_folder
```

**Example:**
```bash
python bin2vid.py decode --out backup/encoded_data --output-folder restored_folder
```

This restores the original folder contents into `restored_folder/`.

---

## How It Works

1. **Archive:** Python's `tarfile` module packages the folder into a single file (cross-platform)
2. **Compress:** `zstd -19 --long=31 -T0` compresses the archive with maximum compression
3. **Pack:** Bytes from `.zst` are mapped to RGB pixels and padded into 1920×1080 frames
4. **Encode:** FFmpeg encodes frames into a lossless FFV1 `.mkv` video
5. **Reverse:** Decoding reverses these steps to recover the original folder exactly

---

## Platform Support

- **Windows**: Fully supported with automatic `.exe` detection
- **macOS**: Native support with proper path handling
- **Linux**: Native support across all major distributions
- **Path Handling**: Uses `pathlib.Path` for robust cross-platform compatibility
- **Temporary Files**: Uses system temporary directories safely

---

## Customization

- **Resolution:** Default is `1920×1080`. Change `WIDTH`/`HEIGHT` constants in the script
- **Compression:** `zstd -19` uses maximum compression. Adjust level (1-22) for speed vs size tradeoff
- **Threads:** `zstd -T0` auto-detects CPU cores. Set specific number if needed

---

## Notes

- **Fully lossless:** No data corruption - bit-perfect restoration guaranteed
- **Automatic cleanup:** Temporary files are automatically removed after processing
- **Error handling:** Helpful error messages with platform-specific installation instructions
- **Large files:** Ensure sufficient disk space for intermediate files during processing
- **Performance:** Multi-threaded compression utilizes all available CPU cores

---

## Troubleshooting

If you encounter "tool not found" errors, the script will display platform-specific installation instructions. Common issues:

- **Windows:** Ensure tools are in PATH, or use package managers like chocolatey/scoop
- **macOS:** Install via homebrew for easiest setup
- **Linux:** Use your distribution's package manager

---

## License

MIT License

---

## Contact

Open an issue or create a pull request for questions and contributions.