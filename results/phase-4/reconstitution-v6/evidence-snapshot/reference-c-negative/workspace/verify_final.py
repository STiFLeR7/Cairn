from pathlib import Path
from greeting import greet

assert greet('Ada') == 'Hello, Ada!'
assert Path('stage2.txt').read_text(encoding='utf-8') == 'phase4-stage2-complete\n'
print('final-verified')
