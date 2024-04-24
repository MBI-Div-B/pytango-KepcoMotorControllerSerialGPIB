from setuptools import setup, find_packages

setup(
    name="tangods_kepcomotorcontrollerserialgpib",
    version="0.0.1",
    description="Device server for controlling Kepco power supplies using Serial-to-GPIB-adapters",
    author="Marin Hennecke",
    author_email="hennecke@mbi-berlin.de",
    python_requires=">=3.6",
    entry_points={"console_scripts": ["KepcoMotorControllerSerialGPIB = tangods_kepcomotorcontrollerserialgpib:main"]},
    license="MIT",
    packages=["tangods_kepcomotorcontrollerserialgpib"],
    install_requires=[
        "pytango",
        "pyserial",
    ],
    url="https://github.com/MBI-Div-b/pytango-KepcoMotorControllerSerialGPIB",
    keywords=[
        "tango device",
        "tango",
        "pytango",
    ],
)
