from setuptools import setup, find_packages

package_name = 'mycobot_280pi_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/robot_bringup.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='myCobot 280 Pi bringup (pymycobot driver + state publishers)',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'pymycobot_driver = mycobot_280pi_bringup.pymycobot_driver:main',
        ],
    },
)