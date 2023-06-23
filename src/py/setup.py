import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="pre_js_py",
    version="1.2.1",

    url="https://github.com/tkw1536/PreJsPy",
    author="Tom Wiesing",
    author_email="tkw01536@gmail.com",
    py_modules=["PreJsPy"],
    description=(
        "Highly configurable precedence-based parser written in both Python and JavaScript"
    ),
    long_description=read("../../README.rst"),
    long_description_content_type="text/x-rst",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
)
