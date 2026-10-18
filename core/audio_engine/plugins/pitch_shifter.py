import os
import subprocess
import logging

class PitchShifterPlugin:
    """
    Zero-Risk Pitch and Speed Control Plugin using FFmpeg.
    """
    @staticmethod
    def apply(input_wav: str, speed_multiplier: float, pitch_shift: int) -> str:
        """
        speed_multiplier: 1.0 is normal, 2.0 is double speed.
        pitch_shift: 0 is normal. 1 is higher pitch, -1 is lower.
        """
        if speed_multiplier == 1.0 and pitch_shift == 0:
            return input_wav

        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            dir_name = os.path.dirname(input_wav)
            base_name = os.path.basename(input_wav)
            out_name = f"pitch_{speed_multiplier}_{pitch_shift}_{base_name}"
            output_wav = os.path.join(dir_name, out_name)
            
            if os.path.exists(output_wav):
                return output_wav
                
            # Use atempo for speed, asetrate for pitch
            # Simple rubberband or asetrate+atempo combo
            rate = 44100
            if pitch_shift > 0:
                rate = 44100 * 1.2
            elif pitch_shift < 0:
                rate = 44100 * 0.8
                
            tempo = speed_multiplier
            if pitch_shift != 0:
                tempo = tempo * (44100 / rate) # Compensate for rate change
                
            filters = []
            if rate != 44100:
                filters.append(f"asetrate={rate}")
            if tempo != 1.0:
                filters.append(f"atempo={tempo}")
                
            filter_str = ",".join(filters) if filters else "anull"
            
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
            logging.warning(f"PitchShifterPlugin failed: {e}")
            return input_wav
