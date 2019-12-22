import subprocess

FAIL = 1
SUCCESS = 0


def ok(command: str, silent=False, log=print):
    log(f'executing: {command}', flush=True)
    p = subprocess.Popen(command.split(' '),
                         bufsize=0,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, b''):
        log('  ' + line.decode('utf-8').rstrip(), flush=True)
    p.wait(10)
    result = p.returncode
    success = result == 0
    if not success and not silent:
        log(f'command failed result code: {result}', flush=True)
    return success
