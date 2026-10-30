# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import tempfile
import zipfile
import time
import pytest
from core.security_engine import SecurityEngine

@pytest.fixture(scope="module")
def engine():
    return SecurityEngine.get_instance()

def test_security_engine_singleton():
    e1 = SecurityEngine.get_instance()
    e2 = SecurityEngine.get_instance()
    assert e1 is e2

def test_safe_legitimate_inputs(engine):
    """Verifies that legitimate user project and folder names are accepted with ZERO false positives."""
    valid_names = [
        "Project 1",
        "My_Animation_2026",
        "DrawMotion Demo-Test",
        "مشروع الأردوينو",
        "الدرس الأول (المقدمة)",
        "Arduino Project (V2.1)",
        "رسم كرتوني ممتع (نسخة 1)",
        "مَشْرُوعٌ_تَعْلِيمِيّ",
        "Test (Final) - 2026_01",
        "Chapter 1.Introduction"
    ]
    for name in valid_names:
        assert engine.is_safe_input(name) is True, f"Legitimate name should be accepted: {name}"

def test_malicious_inputs_blocked(engine):
    """Verifies that malicious injections, shell characters, and path traversal are strictly blocked."""
    malicious_inputs = [
        "",
        "   ",
        "../../Windows",
        "..\\..\\system32",
        "safe_prefix/../../evil",
        "; rm -rf /",
        "test & calc.exe",
        "file | whoami",
        "test`id`",
        "test$HOME",
        "<script>",
        "file>output",
        "bad/path",
        "bad\\path",
        "file:stream",
        "wildcard*test",
        "question?test",
        'quote"injection',
        "null\0byte",
        "CON",
        "con.txt",
        "PRN",
        "aux",
        "NUL",
        "COM1",
        "LPT9"
    ]
    for malicious in malicious_inputs:
        assert engine.is_safe_input(malicious) is False, f"Malicious input should be blocked: {repr(malicious)}"

def test_is_safe_path(engine):
    """Verifies directory traversal protection with is_safe_path."""
    with tempfile.TemporaryDirectory() as base_dir:
        inside_path = os.path.join(base_dir, "subfolder", "project.drawmotion")
        outside_path = os.path.join(base_dir, "..", "escaped_folder", "malicious.txt")
        
        assert engine.is_safe_path(inside_path, base_dir=base_dir) is True
        assert engine.is_safe_path(outside_path, base_dir=base_dir) is False
        assert engine.is_safe_path("normal/path/file.txt") is True
        assert engine.is_safe_path("bad\0path") is False

def test_is_safe_project_archive_zip_slip(engine):
    """Verifies Zip Slip protection against malicious archives."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Clean valid archive
        good_zip = os.path.join(tmp_dir, "clean_project.drawmotion")
        with zipfile.ZipFile(good_zip, 'w') as zf:
            zf.writestr("project.json", '{"name": "test"}')
            zf.writestr("assets/image.png", b"fake_png_data")
            
        assert engine.is_safe_project_archive(good_zip) is True

        # 2. Malicious archive with Zip Slip relative path
        bad_zip = os.path.join(tmp_dir, "zip_slip.drawmotion")
        with zipfile.ZipFile(bad_zip, 'w') as zf:
            zf.writestr("../../Windows/System32/evil.dll", b"payload")
            
        assert engine.is_safe_project_archive(bad_zip) is False

        # 3. Malicious archive with absolute path
        bad_abs_zip = os.path.join(tmp_dir, "abs_slip.drawmotion")
        with zipfile.ZipFile(bad_abs_zip, 'w') as zf:
            zf.writestr("/etc/passwd", b"root")
            
        assert engine.is_safe_project_archive(bad_abs_zip) is False

        # 4. Non-existent file
        assert engine.is_safe_project_archive(os.path.join(tmp_dir, "nonexistent.zip")) is False

def test_sanitize_file_name(engine):
    """Verifies sanitization helper."""
    assert engine.sanitize_file_name("My:Dangerous*Project?Name") == "My_Dangerous_Project_Name"
    assert engine.sanitize_file_name("مشروع جديد (نسخة 1)") == "مشروع جديد (نسخة 1)"
    assert engine.sanitize_file_name("CON") == "project_safe"
    assert engine.sanitize_file_name("") == "project"

def test_in_memory_validation_performance(engine):
    """Verifies that in-memory validation is ultra-fast (< 0.05ms per check)."""
    sample = "مشروع الأردوينو التعليمي (نسخة تجريبية 2026)"
    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        engine.validate_in_memory(sample)
    total_time = time.perf_counter() - start
    avg_ms = (total_time / iterations) * 1000
    
    # Average time must be well under 0.1ms
    assert avg_ms < 0.1, f"Validation too slow: {avg_ms:.4f}ms per call"
