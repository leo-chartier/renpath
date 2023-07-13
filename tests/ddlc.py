import os
import shutil

# Where and what to run
root = r"C:\Program Files (x86)\Steam\steamapps\common\Doki Doki Literature Club"
executable = "DDLC.exe"
modfile = "ddlc.rpy"

modspath = os.path.join(root, "game", "mods")

# Copy everything and run
os.makedirs(modspath, exist_ok=True)
shutil.copy("path.rpy", modspath)
shutil.copy(os.path.join("tests/" + modfile), modspath)
os.chdir(root)
os.system("start " + executable)