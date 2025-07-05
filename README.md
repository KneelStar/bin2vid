# bin2vid

`bin2vid` is a Python tool for **losslessly** converting any folder into a **compressed video** using Zstandard (zstd) compression and FFmpeg's lossless FFV1 codec, and for decoding it back to the original folder.

---

## Features

- Archive and compress a folder with `tar` + `zstd` (lossless, multithreaded).
- Pack the compressed `.zst` into a raw RGB video stream.
- Encode the RGB stream into a lossless FFV1 video (`.mkv`).
- Decode the video back to `.zst`, decompress, and restore the exact original folder.
- Minimal Python dependencies—uses system tools (`ffmpeg`, `zstd`, `tar`).

---

## Requirements

- **Python 3.6+**
- **FFmpeg** (CLI in PATH)
- **Zstandard (zstd)** (CLI in PATH)
- **tar** (pre-installed on Linux/macOS; Windows via WSL or Git Bash)

Verify installation:

```bash
ffmpeg -version
zstd --version
tar --version
```

---

## Installation

No additional Python packages required. Simply place `bin2vid.py` in your project directory.

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

- `backup/encoded_data.mkv`  — lossless FFV1 video
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

1. **Archive:** `tar` packages the folder into a single file.
2. **Compress:** `zstd -19 --long=31 -T0` compresses the archive.
3. **Pack:** Bytes from `.zst` are mapped to RGB pixels and padded into frames.
4. **Encode:** FFmpeg encodes frames into an FFV1 `.mkv` video.
5. **Reverse:** Decoding reverses these steps to recover the folder.

---

## Customization

- **Resolution:** Default is `1920×1080`. Change `WIDTH`/`HEIGHT` in the script.
- **Threads:** `zstd -T0` auto-detects cores. Adjust if needed.

---

## Notes

- Ensure sufficient disk space for intermediate `.tar` and `.rgb` files.
- The process is fully lossless; no data corruption.
- For further compression, pre-compress text-heavy files separately.

---

## License

MIT License

---

## Contact

Open an issue or create a pull request for questions and contributions.
