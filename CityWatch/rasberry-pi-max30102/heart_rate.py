import max30102 
m = max30102.MAX30102()
red, ir = m.read_sequential()
print("red values:",red,"/n","ir values:",ir)