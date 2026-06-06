// dff_sequencer Sequencer

class dff_sequencer extends uvm_sequencer #(dff_txn);

  `uvm_component_utils(dff_sequencer)

   function new(string name, uvm_component parent);
     super.new(name, parent);
   endfunction

endclass
