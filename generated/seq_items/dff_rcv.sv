// dff_rcv Sequence Item

class dff_rcv extends uvm_sequence_item;

  `uvm_object_utils(dff_rcv)

   function new(string name = "dff_rcv");
     super.new(name);
   endfunction

   // Declare transaction fields
   bit d_i;
   bit reset;
   bit q_norst_o;
   bit q_async_rising_clk_rising_reset_o;
   bit q_async_rising_clk_falling_reset_o;
   bit q_async_falling_clk_falling_reset_o;
   bit q_async_falling_clk_rising_reset_o;
   bit q_sync_reset_o;

   // Use utility macros to implement standard functions
   `uvm_object_utils_begin(dff_rcv)
    `uvm_field_int(d_i, UVM_ALL_ON)
    `uvm_field_int(reset, UVM_ALL_ON)
    `uvm_field_int(q_norst_o, UVM_ALL_ON)
    `uvm_field_int(q_async_rising_clk_rising_reset_o, UVM_ALL_ON)
    `uvm_field_int(q_async_rising_clk_falling_reset_o, UVM_ALL_ON)
    `uvm_field_int(q_async_falling_clk_falling_reset_o, UVM_ALL_ON)
    `uvm_field_int(q_async_falling_clk_rising_reset_o, UVM_ALL_ON)
    `uvm_field_int(q_sync_reset_o, UVM_ALL_ON)
   `uvm_object_utils_end

endclass
