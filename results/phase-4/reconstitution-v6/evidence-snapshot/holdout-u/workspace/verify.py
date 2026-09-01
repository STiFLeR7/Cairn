from labels import normalize_label

assert normalize_label('  Blue   Sky ') == 'blue-sky'
assert normalize_label('One') == 'one'
print('verified')
