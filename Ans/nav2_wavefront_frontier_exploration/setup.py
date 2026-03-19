import os
from glob import glob
from setuptools import setup

package_name = 'nav2_wavefront_frontier_exploration'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # 1. Install Launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        
        # 2. Install Config files (YAML and XML for Behavior Trees)
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'config'), glob('config/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Sean Regan',
    maintainer_email='dev@mail.com',
    description='Wavefront Frontier Detector for ROS2 Navigation2',
    license='MIT License',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # This name 'wavefront_frontier.py' MUST match the 'executable' in your launch file
            'wavefront_frontier = nav2_wavefront_frontier_exploration.wavefront_frontier:main',
    ],
    },
)