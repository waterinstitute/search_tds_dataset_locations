import os.path
import subprocess

path = '/datasets/published/'
path = '/datasets/published/blended-global-sea-surface-wind-products/access/nrt/wind'
# path = '/home/myles.mcmanus'

def is_on_mount(path):
  while True:
    if path == os.path.dirname(path):
      # we've hit the root dir
      return False
    elif os.path.ismount(path):
      return True
    path = os.path.dirname(path)

is_mounted = is_on_mount(path)
writeable = os.access(path, os.W_OK)
# is_mounted = os.path.ismount(path)
print(is_mounted)
print(writeable)

if is_mounted:
    # run a subprocess to use findmnt -n 0o SOURCE --target path
    # to get the source of the mount.
    mnt_path = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '--target', path])
    mnt_path = mnt_path.decode('utf-8').strip()
    print(mnt_path)