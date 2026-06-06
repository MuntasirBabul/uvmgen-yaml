// dff_txn Sequence Item

class dff_txn extends uvm_sequence_item;

  `uvm_object_utils(dff_txn)

   function new(string name = "dff_txn");
     super.new(name);
   endfunction

   // Declare transaction fields
   bit d_i;
   bit reset;

   // Use utility macros to implement standard functions
   `uvm_object_utils_begin(dff_txn)
    `uvm_field_int(d_i, UVM_ALL_ON)
    `uvm_field_int(reset, UVM_ALL_ON)
   `uvm_object_utils_end

   // Constraints
   constraint dff_txn_c 
   { 
     data inside {[0:127], [128:255]};
     stop_bits inside {1,2};
   }

endclass
