"""
HK NPU STUDIO

File Utilities

Phoenix Engine
"""

from pathlib import Path

def get_unique_filename(target_dir: Path | str, original_filename: str) -> Path:
    """
    Generiert einen eindeutigen Dateinamen im Zielordner basierend auf dem ursprünglichen Dateinamen.
    
    Falls die Datei im Zielordner noch nicht existiert, wird der ursprüngliche Name beibehalten.
    Falls sie bereits existiert, wird ein dreistelliger Suffix angehängt (_001, _002, etc.).
    
    Vorhandene Dateien werden niemals überschrieben.
    
    Args:
        target_dir (Path | str): Der Zielordner, in dem die Datei gespeichert werden soll.
        original_filename (str): Der gewünschte Dateiname (oder Pfad).
        
    Returns:
        Path: Der absolute oder relative Pfad zur eindeutigen Zieldatei.
    """
    target_path = Path(target_dir)
    original_name = Path(original_filename).name
    
    # Trennung von Stamm und Dateiendung
    orig_path = Path(original_name)
    stem = orig_path.stem
    suffix = orig_path.suffix
    
    candidate = target_path / f"{stem}{suffix}"
    if not candidate.exists():
        return candidate
        
    counter = 1
    max_counter = 999
    
    while counter <= max_counter:
        candidate = target_path / f"{stem}_{counter:03d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
        
    # Sicherheits-Fallback falls 999 überschritten wird
    return target_path / f"{stem}_{counter}{suffix}"
