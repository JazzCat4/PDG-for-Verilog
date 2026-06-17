# PDG-for-Verilog

Utilizes PyVerilog to parse through a verilog module to build a Program Dependence Graph

### **Required modules:**

* pyverilog
* networkx
* matplotlib
* PyGraphviz



Note: Pyverilog can only parse through text in UTF-8



### **How to use:**



Add verilog module to same directory, run PDG.py with the name of the file as an argument



Registers/Wires are shown as nodes. Edges connecting nodes are either solid-blue (indicating data flow), or dotted-red (indicating control flow). The console will also print out all edges.

