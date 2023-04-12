from distutils.core import setup, Extension

c_cc_0 = Extension("c_cc_0", sources = ["c_cc_0.cpp"])
setup (name = "c_cc_0", version = "1.0", description = "Canonicizers (C++)", ext_modules = [c_cc_0])
