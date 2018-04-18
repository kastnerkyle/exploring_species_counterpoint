import os

with open("shared_config.py", "r") as f:
    lines = f.readlines()

for l in lines:
    p = l.split(" = ")[-1].replace('"', '').strip()
    if os.path.exists(p):
        print("Removing file {} based on shared_config.py".format(p))
        os.remove(p)

all_files = os.listdir(".")
for fi in all_files:
    if fi.endswith("log.log"):
        print("Removing logfile {}".format(fi))
        os.remove(fi)
