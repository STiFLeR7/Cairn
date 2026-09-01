from pathlib import Path

assert Path('.cairn-release-stage2').is_file()
Path('release.txt').write_text('holdout-release-complete\n', encoding='utf-8')
print('advanced')
