__global_counter: int = 0


def get_node_id():
    global __global_counter
    __global_counter = __global_counter + 1
    return __global_counter
