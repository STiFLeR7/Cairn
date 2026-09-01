from pathlib import Path
from labels import normalize_label

assert normalize_label('  Blue   Sky ') == 'blue-sky'
assert Path('release.txt').read_text(encoding='utf-8') == 'holdout-release-complete\n'
print('final-verified')
