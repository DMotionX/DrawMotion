import os
import subprocess
import logging

class NoiseCancelerPlugin:
    """
    Zero-Risk Noise Cancellation Plugin using FFmpeg.
    """
    @staticmethod
    def apply(input_wav: str, enable: bool) -> str:
        """
        Applies FFT DeNoise and Highpass filters to remove background static.
        If enable is False, returns original file.
        """
        if not enable:
            return input_wav

        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            dir_name = os.path.dirname(input_wav)
            base_name = os.path.basename(input_wav)
            out_name = f"denoise_{base_name}"
            output_wav = os.path.join(dir_name, out_name)
            
            if os.path.exists(output_wav):
                return output_wav # Return cached if already processed
            
            cmd = [
                ffmpeg_exe,
                "-i", input_wav,
                "-af", "highpass=f=100,afftdn",
                "-y",
                output_wav
            ]
            
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                check=True,
                timeout=15
            )
            
            if os.path.exists(output_wav) and os.path.getsize(output_wav) > 0:
                return output_wav
            return input_wav
            
        except Exception as e:
            logging.warning(f"NoiseCancelerPlugin failed: {e}")
            return input_wav
