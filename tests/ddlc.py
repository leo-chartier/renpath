import os
import shutil

# Where and what to run
root = r"C:\Program Files (x86)\Steam\steamapps\common\Doki Doki Literature Club"
executable = "DDLC.exe"
modfile = "ddlc.rpy"

modspath = os.path.join(root, "game", "mods")
packagepath = os.path.join(root, "game", "python-packages", "renpath")

# Clean & copy everything
if os.path.exists(packagepath):
    shutil.rmtree(packagepath)
shutil.copytree("renpath", packagepath)
if not os.path.exists(modspath):
    os.makedirs(modspath)
shutil.copy(os.path.join("tests/" + modfile), os.path.join(modspath, "renpath.rpy"))

# Run
os.chdir(root)
os.system("start \"\" \"" + executable + "\"")