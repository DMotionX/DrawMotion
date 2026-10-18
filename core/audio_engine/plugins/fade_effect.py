import os
import subprocess
import logging

class FadeEffectPlugin:
    """
    Zero-Risk Fade In/Out Plugin using FFmpeg.
    """
    @staticmethod
    def apply(input_wav: str, fade_in_sec: float, fade_out_sec: float, total_duration: float) -> str:
        if fade_in_sec <= 0 and fade_out_sec <= 0:
            return input_wav

        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            dir_name = os.path.dirname(input_wav)
            base_name = os.path.basename(input_wav)
            out_name = f"fade_{fade_in_sec}_{fade_out_sec}_{base_name}"
            output_wav = os.path.join(dir_name, out_name)
            
            if os.path.exists(output_wav):
                return output_wav
                
            filters = []
            if fade_in_sec > 0:
                filters.append(f"afade=t=in:ss=0:d={fade_in_sec}")
            if fade_out_sec > 0 and total_duration > 0:
                st = total_duration - fade_out_sec
                if st > 0:
                    filters.append(f"afade=t=out:st={st}:d={fade_out_sec}")
                    
            if not filters:
                return input_wav
                
            filter_str = ",".join(filters)
            
            cmd = [
                ffmpeg_exe,
                "-i", input_wav,
                "-af", filter_str,
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
            logging.warning(f"FadeEffectPlugin failed: {e}")
            return input_wav
