from setuptools import setup

setup(
    name="Development",
    packages=["orangedemo"],
    package_data={"orangedemo": ["icons/*.svg"]},
    classifiers=["Example :: Invalid"],
    # Declare orangedemo package to contain widgets for the "Demo" category
    entry_points={"orange.widgets": "Demo = orangedemo"},
)