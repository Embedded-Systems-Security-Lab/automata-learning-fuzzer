import sys
from ctypes import *

from FMI.mutation.base_mutation import Mutation
from FMI.utils import helper
from FMI.utils import afl_constants



class RamdamsaMutation(Mutation):

	def __init__(self,
				 seed,
				 library_path="./FMI/mutation/radamsa/libradamsa/libradamsa.so"):
		super(RamdamsaMutation, self).__init__(seed)
		self.seed = seed
		self.lib = None
		if not sys.version_info[0] == 3:
			print("Radamsa library is not supported in Python2")
		self.load_library(library_path)

	def load_library(self, library_path):
		self.lib = cdll.LoadLibrary(library_path)
		self.lib.radamsa_init()
		self.lib.radamsa.argtypes = [POINTER(c_ubyte), c_size_t, POINTER(c_ubyte), c_size_t, c_size_t]



	def get_mutated_payload(self, mut_input):
		if self.lib is None:
			print("Please call the load_library function with the path of the radamsa")
			return None
		input_len = c_size_t(len(mut_input))
		output_len = helper.AFL_choose_block_len(afl_constants.AFL_HAVOC_BLK_XL)
		mut_output = create_string_buffer(output_len)
		mut_input_casted = cast(mut_input, POINTER(c_ubyte))
		mut_output_casted = cast(mut_output, POINTER(c_ubyte))
		bytes_mutated = 0
		while bytes_mutated == 0:
			bytes_mutated = self.lib.radamsa(mut_input_casted, input_len, mut_output_casted, c_size_t(output_len), c_size_t(self.seed))
			#self.seed += 1

		#return bytearray(mut_output.raw[:bytes_mutated]) #TODO check
		return mut_output.raw[:bytes_mutated]
