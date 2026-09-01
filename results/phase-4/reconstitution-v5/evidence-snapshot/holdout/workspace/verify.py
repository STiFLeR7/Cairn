from segments import join_segments

assert join_segments([' red ', '', 'blue ', '   ']) == 'red/blue'
print('verified')
