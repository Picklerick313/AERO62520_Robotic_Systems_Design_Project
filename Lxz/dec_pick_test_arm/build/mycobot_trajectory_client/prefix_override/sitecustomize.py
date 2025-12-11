import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/laptop34/dec_pick_test_arm/install/mycobot_trajectory_client'
