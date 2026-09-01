from pathlib import Path

assert Path('.cairn-release-stage2').is_file()
Path('stage2.txt').write_text('phase4-stage2-complete\n', encoding='utf-8')
print('stage2-complete')
