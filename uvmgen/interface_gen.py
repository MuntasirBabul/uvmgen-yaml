import yaml
from pathlib import Path

with open("config/design.yaml") as f:
  cfg = yaml.safe_load(f)

##################################
# Generate interface 
###################################

def gen_interface(interface):
  interface_name = interface["name"]
  out_dir = Path(f"generated/test/interfaces/")
  out_dir.mkdir(parents=True, exist_ok=True)
  with open(out_dir / f"{interface_name}.sv", "w") as f:
    f.write(f"// {interface_name} Interface\n\n")
    f.write(f"interface {interface_name};\n\n")
    for signal in interface["signals"]:
      f.write(f"  {signal['type']} {signal['name']};\n")
    f.write(f"\nendinterface\n")

###########################################################
# Execute generation based on config
###########################################################
def main():
  
  for intf in cfg["interface"]:
    gen_interface(intf)

if __name__ == "__main__":
  main()