from pathlib import Path
from zero.cli.commands.test import _detect_failing_file

def test_detect_failing_file_python_traceback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    mock_file = tmp_path / "app.py"
    mock_file.write_text("print('hello')")
    
    output = """
Traceback (most recent call last):
  File "app.py", line 12, in <module>
    main()
TypeError: 'NoneType' object is not callable
"""
    detected = _detect_failing_file(output)
    assert detected == Path("app.py")

def test_detect_failing_file_linter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    mock_file = tmp_path / "utils.py"
    mock_file.write_text("x = 1")
    
    output = "utils.py:10:5: F841 local variable 'x' is assigned to but never used"
    detected = _detect_failing_file(output)
    assert detected == Path("utils.py")
