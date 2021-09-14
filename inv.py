import re 


def get_lines(path):
    with open(path, "r") as f:
        return f.readlines()


if __name__ == "__main__":
    path = r""
    lines = get_lines(path)
    invd_matrix = lines[8]
    invd_matrix = invd_matrix.replace(', ', ',\n ')
    split_invd = invd_matrix.split()
    itr = 0
    for i in split_invd:
        split_invd[itr] = i + "\n"
        # split_invd[itr] = i.replace("_", "") + "\n"

        itr += 1
    key = split_invd[0][-15:-2]
    # print(key)
    # idx = 0
    # for i in range(len(split_invd)):
    #     print(re.search(key, split_invd[i]))
    #     if re.search(key, split_invd[i]) is not None:
    #         idx += 1
    # print(idx)

    writeback = lines[0:8] + [split_invd[0], split_invd[256], split_invd[512], split_invd[256 * 3]] + lines[9:]
    with open("ldpc_reduce.text", "w") as f:
        for line in writeback:
            f.write(line)
