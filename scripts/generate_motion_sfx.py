"""
Generates clean procedural 16-bit PCM WAV sound effects for the Motion Engine:
- assets/sfx/motion/whoosh.wav
- assets/sfx/motion/thud.wav
- assets/sfx/motion/pop.wav
"""
import os
import wave
import struct
import math
import random

def generate_motion_sfx():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "assets", "sfx", "motion")
    os.makedirs(out_dir, exist_ok=True)
    sample_rate = 44100

    # 1. Whoosh (~0.35s)
    dur_whoosh = 0.35
    total_samples = int(sample_rate * dur_whoosh)
    whoosh_path = os.path.join(out_dir, "whoosh.wav")
    with wave.open(whoosh_path, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(total_samples):
            t = i / float(sample_rate)
            t_norm = t / dur_whoosh
            # Raised cosine envelope
            env = 0.5 * (1.0 - math.cos(2.0 * math.pi * t_norm))
            # Smooth frequency glide from 520Hz down to 180Hz
            freq = 520.0 - 340.0 * (t_norm ** 0.8)
            phase = 2.0 * math.pi * (520.0 * t - (340.0 / 1.8) * (t ** 1.8) / (dur_whoosh ** 0.8))
            tone = math.sin(phase) + 0.35 * math.sin(phase * 1.5)
            # Gentle filtered noise component
            noise = (random.random() * 2.0 - 1.0) * 0.25
            sample_val = (tone * 0.75 + noise) * env
            clamped = max(-1.0, min(1.0, sample_val * 0.70))
            int_sample = int(clamped * 32767.0)
            frames.extend(struct.pack("<h", int_sample))
            
        wav_file.writeframes(frames)
    print(f"[SFX Generator] Created: {whoosh_path}")

    # 2. Thud (~0.22s)
    dur_thud = 0.22
    total_samples = int(sample_rate * dur_thud)
    thud_path = os.path.join(out_dir, "thud.wav")
    with wave.open(thud_path, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(total_samples):
            t = i / float(sample_rate)
            # Fast attack (2ms), exponential decay
            attack = min(1.0, t / 0.003)
            decay = math.exp(-18.0 * t)
            # Pitch drop from 120Hz down to 45Hz
            pitch = 45.0 + 75.0 * math.exp(-25.0 * t)
            phase = 2.0 * math.pi * (45.0 * t + 3.0 * (1.0 - math.exp(-25.0 * t)))
            # Transient snap
            snap = math.sin(2.0 * math.pi * 240.0 * t) * math.exp(-80.0 * t) * 0.35
            sample_val = (math.sin(phase) * 0.85 + snap) * attack * decay
            clamped = max(-1.0, min(1.0, sample_val * 0.85))
            int_sample = int(clamped * 32767.0)
            frames.extend(struct.pack("<h", int_sample))
            
        wav_file.writeframes(frames)
    print(f"[SFX Generator] Created: {thud_path}")

    # 3. Pop (~0.08s)
    dur_pop = 0.08
    total_samples = int(sample_rate * dur_pop)
    pop_path = os.path.join(out_dir, "pop.wav")
    with wave.open(pop_path, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(total_samples):
            t = i / float(sample_rate)
            attack = min(1.0, t / 0.002)
            decay = math.exp(-48.0 * t)
            # Quick upward chirp then drop: 300 -> 900 -> 500
            chirp_phase = 2.0 * math.pi * (350.0 * t + 12000.0 * (t ** 2) if t < 0.02 else 850.0 * t)
            sample_val = math.sin(chirp_phase) * attack * decay
            clamped = max(-1.0, min(1.0, sample_val * 0.80))
            int_sample = int(clamped * 32767.0)
            frames.extend(struct.pack("<h", int_sample))
            
        wav_file.writeframes(frames)
    print(f"[SFX Generator] Created: {pop_path}")

if __name__ == "__main__":
    generate_motion_sfx()
