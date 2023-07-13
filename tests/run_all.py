import os

root = os.getcwd()
for filename in os.listdir("tests"):
    if not filename.endswith(".py"):
        continue # Only keep python files
    if filename == os.path.basename(__file__):
        continue # Do no run this script

    os.chdir(root)
    name, _ = os.path.splitext(filename)
    dirpath = __import__(name).root
    dirname = os.path.basename(dirpath)

    print(f"Successfully started \"{dirname}\"")