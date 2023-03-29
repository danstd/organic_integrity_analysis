from sys import version

py_version = f"python-{version.split(' ')[0]}"

with open("runtime.txt", "w") as r:
    r.write(py_version)