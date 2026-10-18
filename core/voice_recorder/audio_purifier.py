import os
import subprocess
import logging

class AudioPurifier:
    @staticmethod
    def purify(input_wav: str) -> str:
        """
        Applies fast ffmpeg noise reduction (afftdn) and highpass filter 
        to remove background static and hum from voice recordings.
        Returns the path to the purified file. If any error occurs, it safely 
        returns the original input_wav (Zero Risk Fallback).
        """
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Generate output path
            dir_name = os.path.dirname(input_wav)
            base_name = os.path.basename(input_wav)
            out_name = f"purified_{base_name}"
            output_wav = os.path.join(dir_name, out_name)
            
            # Apply afftdn (FFT DeNoise) and highpass to remove low rumbling static
            # This is extremely fast for voice clips.
            # Using -y to overwrite if needed.
            cmd = [
                ffmpeg_exe,
                "-i", input_wav,
                "-af", "highpass=f=100,afftdn",
                "-c:a", "pcm_s16le", # Keep it standard 16-bit WAV
                "-ar", "44100",      # Standardize sample rate
                "-ac", "1",          # Force Mono
                "-y",
                output_wav
            ]
            
            # Run silently and quickly
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                check=True,
                timeout=10 # Max 10 seconds, otherwise fail safely
            )
            
            # Check if output file was actually created and has size
            if os.path.exists(output_wav) and os.path.getsize(output_wav) > 0:
                return output_wav
            else:
                return input_wav
                
        except Exception as e:
            logging.warning(f"Audio purification failed, falling back to original: {e}")
            return input_wav
