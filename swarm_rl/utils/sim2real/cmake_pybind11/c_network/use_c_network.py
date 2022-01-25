import sys
import numpy as np

from c_network.extension.c_network import Network


def main():
    arr = np.array([0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
    nn = Network()
    result = nn.forward(arr)
    print(nn.neighbor_embeds([[1, 2, 3]]))
    print('Result:', result)
    return 0


if __name__ == '__main__':
    sys.exit(main())