"""
Purpose: High-speed multi-stream parallel update downloader.
Features:
- Splits file into 8 concurrent HTTP Range request chunks.
- Resolves CDN redirects once to maximize connection speed.
- Emits real-time progress, download speed (MB/s), and estimated time remaining (ETA).
Zero emojis, high-throughput, enterprise stability.
"""

import os
import urllib.request
import urllib.error
import concurrent.futures
import time
from PySide6.QtCore import QObject, Signal, QThread

class DownloadWorker(QThread):
    """
    High-throughput background worker executing 8-stream parallel downloads.
    """
    progress = Signal(int)                          # 0 to 100
    stats = Signal(int, int, float, int)            # downloaded_bytes, total_bytes, speed_bytes_s, eta_seconds
    finished = Signal(str)                         # downloaded file path
    error = Signal(str)
    
    def __init__(self, url, save_path, chunks=8):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.chunks = max(1, chunks)
        self._is_cancelled = False
        
    def cancel(self):
        self._is_cancelled = True
        
    def run(self):
        temp_files = []
        try:
            if not self.url.startswith("https://"):
                self.error.emit("Insecure download URL: HTTPS required.")
                return

            # Step 1: Resolve redirects and get total content length
            headers = {
                'User-Agent': 'DrawMotion-FastUpdater/1.0',
                'Accept-Encoding': 'identity'
            }
            req = urllib.request.Request(self.url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=12) as response:  # nosec B310
                final_url = response.geturl()
                if not final_url.startswith("https://"):
                    self.error.emit("Insecure redirect URL: HTTPS required.")
                    return
                file_size = int(response.headers.get('Content-Length', 0))
                accept_ranges = response.headers.get('Accept-Ranges', 'none').lower()

            if file_size <= 0 or accept_ranges == 'none':
                # Fallback to streaming single-connection download with live progress
                self._download_sequential(final_url)
                return

            # Step 2: Calculate byte segments for 8 streams
            chunk_size = file_size // self.chunks
            ranges = []
            for i in range(self.chunks):
                start = i * chunk_size
                end = file_size - 1 if i == self.chunks - 1 else (start + chunk_size - 1)
                ranges.append((start, end, i))

            temp_files = [f"{self.save_path}.part{i}" for i in range(self.chunks)]
            downloaded_bytes = [0] * self.chunks
            
            start_time = time.time()
            last_stats_time = start_time
            last_total_downloaded = 0

            # Step 3: Stream download worker
            def download_chunk(start, end, index):
                chunk_req = urllib.request.Request(final_url, headers={
                    'User-Agent': 'DrawMotion-FastUpdater/1.0',
                    'Range': f'bytes={start}-{end}',
                    'Accept-Encoding': 'identity'
                })
                try:
                    with urllib.request.urlopen(chunk_req, timeout=20) as resp, open(temp_files[index], 'wb') as out_f:  # nosec B310
                        # 1MB buffer for maximum throughput
                        while chunk_data := resp.read(1048576):
                            if self._is_cancelled:
                                return False
                            out_f.write(chunk_data)
                            downloaded_bytes[index] += len(chunk_data)
                            
                            now = time.time()
                            nonlocal last_stats_time, last_total_downloaded
                            if now - last_stats_time >= 0.25:
                                total_downloaded = sum(downloaded_bytes)
                                percent = min(99, int((total_downloaded / file_size) * 100))
                                self.progress.emit(percent)
                                
                                delta_time = now - last_stats_time
                                delta_bytes = total_downloaded - last_total_downloaded
                                speed = delta_bytes / delta_time if delta_time > 0 else 0.0
                                
                                remaining_bytes = max(0, file_size - total_downloaded)
                                eta = int(remaining_bytes / speed) if speed > 0 else 0
                                
                                self.stats.emit(total_downloaded, file_size, speed, eta)
                                last_stats_time = now
                                last_total_downloaded = total_downloaded

                    return True
                except Exception as ex:
                    return str(ex)

            # Step 4: Execute 8 threads concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.chunks) as executor:
                futures = [executor.submit(download_chunk, s, e, idx) for s, e, idx in ranges]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res is not True:
                        if self._is_cancelled:
                            break
                        raise Exception(f"Connection stream failed: {res}")

            if self._is_cancelled:
                self._cleanup(temp_files)
                self.error.emit("Download cancelled by user.")
                return

            # Step 5: High-speed assembly of parts into final installer
            with open(self.save_path, 'wb') as final_file:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        with open(temp_file, 'rb') as part_f:
                            shutil_copy(part_f, final_file)
                        os.remove(temp_file)

            self.progress.emit(100)
            self.stats.emit(file_size, file_size, 0.0, 0)
            self.finished.emit(self.save_path)

        except Exception as e:
            self._cleanup(temp_files)
            self.error.emit(str(e))
            
    def _cleanup(self, temp_files):
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
                
    def _download_sequential(self, final_url):
        try:
            if not final_url.startswith("https://"):
                self.error.emit("Insecure download URL: HTTPS required.")
                return
            req = urllib.request.Request(final_url, headers={'User-Agent': 'DrawMotion-FastUpdater/1.0'})
            with urllib.request.urlopen(req, timeout=20) as resp, open(self.save_path, 'wb') as out_f:  # nosec B310
                total_len = int(resp.headers.get('Content-Length', 0))
                downloaded = 0
                start_time = time.time()
                last_time = start_time
                last_bytes = 0
                
                while chunk := resp.read(1048576):
                    if self._is_cancelled:
                        self.error.emit("Download cancelled")
                        return
                    out_f.write(chunk)
                    downloaded += len(chunk)
                    
                    now = time.time()
                    if now - last_time >= 0.25:
                        pct = int((downloaded / total_len) * 100) if total_len > 0 else 50
                        self.progress.emit(min(99, pct))
                        speed = (downloaded - last_bytes) / (now - last_time) if (now - last_time) > 0 else 0
                        eta = int((total_len - downloaded) / speed) if speed > 0 and total_len > 0 else 0
                        self.stats.emit(downloaded, total_len, speed, eta)
                        last_time = now
                        last_bytes = downloaded
                        
            self.progress.emit(100)
            self.finished.emit(self.save_path)
        except Exception as e:
            self.error.emit(str(e))

def shutil_copy(src_f, dst_f):
    while chunk := src_f.read(4194304): # 4MB assembly buffer
        dst_f.write(chunk)
