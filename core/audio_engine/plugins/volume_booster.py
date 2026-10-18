import os
import subprocess
import logging

class VolumeBoosterPlugin:
    """
    Zero-Risk Audio Volume Booster using FFmpeg.
    """
    @staticmethod
    def apply(input_wav: str, volume_percent: int) -> str:
        """
        Adjusts the volume of the audio file.
        volume_percent: 100 is normal, 200 is double, 50 is half.
        Returns the path to the modified file or original if failed.
        """
        if volume_percent == 100:
            return input_wav # No change needed

        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            from utils.paths import get_app_data_dir
            cache_dir = os.path.join(get_app_data_dir(), "audio_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            name_no_ext = os.path.splitext(os.path.basename(input_wav))[0]
            output_wav = os.path.join(cache_dir, f"vol_{volume_percent}_{name_no_ext}.wav")
            
            if os.path.exists(output_wav) and os.path.getsize(output_wav) > 0:
                return output_wav # Return cached if already processed
            
            # FFmpeg volume filter (e.g. 1.5 = 150%)
            vol_multiplier = volume_percent / 100.0
            cmd = [
                ffmpeg_exe,
                "-i", input_wav,
                "-af", f"volume={vol_multiplier}",
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
            logging.warning(f"VolumeBoosterPlugin failed: {e}")
            return input_wav
