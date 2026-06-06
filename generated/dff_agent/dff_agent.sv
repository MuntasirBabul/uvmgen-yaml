// dff_agent Agent

class dff_agent extends uvm_agent;

  `uvm_component_utils(dff_agent)

   function new(string name, uvm_component parent);
     super.new(name, parent);
   endfunction

   // Declare component Handles
   uvm_sequencer #(dff_txn) dff_sequencer_handle;
   dff_driver dff_driver_handle;
   dff_monitor dff_monitor_handle;

   // Build Phase
   function void build_phase(uvm_phase phase);
     super.build_phase(phase);
     dff_sequencer_handle = uvm_sequencer#(dff_txn)::type_id::create("dff_sequencer_handle", this);
     dff_driver_handle = dff_driver::type_id::create("dff_driver_handle", this);
     dff_monitor_handle = dff_monitor::type_id::create("dff_monitor_handle", this);
   endfunction

   // Connect Phase
   function void connect_phase(uvm_phase phase);
     super.connect_phase(phase);
     dff_driver_handle.seq_item_port.connect(dff_sequencer_handle.seq_item_export); // Connect driver to sequencer
   endfunction

endclass
