import os, glob, time

src = r'E:\Daodao\src\桌面分身'
print('EXE:', [f for f in os.listdir(src) if f.endswith('.exe')])

for f in sorted(glob.glob(os.path.join(src, 'selfcheck_p8*'))):
    mt = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(f)))
    print(os.path.basename(f), mt)

print('部署目录自检:')
for f in sorted(glob.glob(r'E:\Daodao\selfcheck_p8*')):
    mt = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(f)))
    print(os.path.basename(f), mt)
