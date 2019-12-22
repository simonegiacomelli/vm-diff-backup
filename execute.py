import subprocess


def ok(command: str, silent=False):
    print(f'executing: {command}')
    p = subprocess.Popen(command.split(' '),
                         bufsize=0,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, b''):
        print('  ' + line.decode('utf-8').rstrip(),flush=True)
    p.wait(10)
    result = p.returncode
    success = result == 0
    if not success and not silent:
        print(f'  command failed result code: {result}')
    return success
