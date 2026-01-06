import test_data_versioning

p1 = 5.5
p2 = 9.5

file_prefix = test_data_versioning.get_result_prefix()

with open(file_prefix + "testresult.txt", "w") as f:
    f.write(f"result = {p1 + p2}\n")
