from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    ext_modules=cythonize("bowyer_watson_cython.pyx"),
    include_dirs=[numpy.get_include()]
)
